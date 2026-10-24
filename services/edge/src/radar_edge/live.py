"""One native webcam, bounded capture and independent current-health/delivery loops."""

import hashlib
import json
import sqlite3
from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime
from time import monotonic, monotonic_ns, sleep
from uuid import uuid4

import cv2

from radar_edge.calibration import check_compatibility, load_calibration
from radar_edge.config import private_path, quality_threshold
from radar_edge.errors import EdgeError
from radar_edge.estimator import create_estimator
from radar_edge.event_runtime import EventRuntime
from radar_edge.health import LiveHealth, NetworkWorker
from radar_edge.local_status import publish_status, safe_diagnostic
from radar_edge.metrics import Metrics
from radar_edge.model import get_model_spec, model_metadata
from radar_edge.observations import Observation, pose_quality
from radar_edge.preview import LocalPreview
from radar_edge.webcam import WebcamSource


def control_path(config):
    return private_path(f".local/edge-control/{config.cameraId}.json")


def send_control(config, action):
    path = control_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"id": str(uuid4()), "action": action}), encoding="utf-8")
    temporary.replace(path)
    return {
        "status": "ok",
        "command": "control",
        "action": action,
        "message": "Solicitação local enviada; confira o relatório de saúde do worker.",
    }


def _control(config):
    path = control_path(config)
    try:
        if path.stat().st_size > 4096:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("action") not in {"pause", "resume", "reconnect", "stop"}:
            return None
        return value
    except (OSError, ValueError):
        return None


def doctor_live(config):
    spec = get_model_spec(config.model.variant)
    with WebcamSource(config.source, config.processing.maxWidth) as source:
        frame = source.read()
        with create_estimator(config.model.path, config.model.variant) as estimator:
            poses, duration = estimator.estimate(frame)
        return {
            "status": "ok",
            "command": "doctor",
            "mode": "LIVE",
            "source": source.metadata(),
            "modelId": spec.model_id,
            "modelSha256": spec.sha256,
            "modelLoaded": True,
            "inferenceExecuted": True,
            "poseCount": len(poses),
            "firstInferenceMs": duration,
            "framesSaved": False,
            "cameraOpened": True,
        }


def run_live(config):
    spec = get_model_spec(config.model.variant)
    report_id = str(uuid4())
    directory = private_path(config.diagnostics.outputDirectory) / report_id
    directory.mkdir(parents=True)
    metrics = Metrics(quality_threshold(config), model_metadata(spec)["qualitySource"])
    source = WebcamSource(config.source, config.processing.maxWidth)
    calibration = None
    runtime = None
    network = None
    health = None
    temporal = {"enabled": config.events.enabled}
    state, code, error = "ENDED", 0, None
    last_status = 0.0
    status_retries = 0
    previous_command = _control(config)
    started = monotonic()
    preview = None
    try:
        with ExitStack() as resources:
            resources.enter_context(source)
            first = source.read()
            try:
                calibration = load_calibration(config.calibrationPath)
                check_compatibility(calibration, first.geometry, config.cameraId)
                if (
                    calibration.get("sourceKind") != "WEBCAM"
                    or calibration.get("deviceIndex") != config.source.index
                ):
                    raise EdgeError(
                        "CALIBRATION_REQUIRED", "Selecione o piso próprio desta webcam."
                    )
            except EdgeError:
                health = LiveHealth(config, str(uuid4()), None)
                health.source = source
                health.update(capture="ERROR", flags={"CALIBRATION_REQUIRED"})
                network = resources.enter_context(NetworkWorker(config, health))
                raise
            if config.events.enabled:
                runtime = resources.enter_context(
                    EventRuntime(config, calibration, "WEBCAM", first.geometry, async_delivery=True)
                )
                resources.callback(lambda: temporal.update(runtime.summary()))
            capture_run = runtime.capture_run_id if runtime else str(uuid4())
            health = LiveHealth(config, capture_run, calibration)
            health.source = source
            network = resources.enter_context(NetworkWorker(config, health))
            # Save error/final state before the network resource is closed.
            estimator = resources.enter_context(
                create_estimator(config.model.path, config.model.variant)
            )
            preview = LocalPreview(config.processing.preview, config.processing.previewStartPaused)
            if config.processing.previewStabilization:
                preview.enable_stabilization()
            preview.name = "Radar - poses locais LIVE"
            preview.blocking_pause = False
            resources.enter_context(preview)
            if runtime:
                anchor = datetime.fromisoformat(runtime.run["anchor"].replace("Z", "+00:00"))
                offset = max(
                    runtime.run["timestamp_ms"] + 1 - first.timestamp_ms,
                    round((source.start_utc - anchor).total_seconds() * 1000),
                )
                frame_offset = runtime.run["frame_index"] + 1
            else:
                offset, frame_offset = 0, 0
            paused = False

            def pause(value):
                nonlocal paused
                paused = value
                if value:
                    source.pause()
                    health.update(capture="PAUSED", flags=set())
                else:
                    source.resume()
                    health.update(
                        capture="RUNNING", flags={"FRAME_TIMEOUT"}, inference="WARMING_UP"
                    )

            preview.on_pause = pause
            first = None  # Acquire a fresh frame after model setup, never classify an old one.
            next_analysis = 0.0
            while True:
                now = monotonic()
                command = _control(config)
                if command and command != previous_command:
                    previous_command = command
                    if command["action"] == "stop":
                        break
                    if command["action"] == "pause" and not paused:
                        preview.set_paused(True)
                    if command["action"] == "resume" and paused:
                        preview.set_paused(False)
                    if command["action"] == "reconnect":
                        source.pause()
                        source.resume()
                        paused = False
                        preview.finish_pause()
                        health.update(
                            capture="RUNNING", flags={"FRAME_TIMEOUT"}, inference="WARMING_UP"
                        )
                if not preview.poll():
                    break
                if (
                    config.processing.maxRunSeconds
                    and now - started >= config.processing.maxRunSeconds
                ):
                    break
                if now - last_status >= 1:
                    status = {
                        "heartbeat": health.snapshot(),
                        "network": health.network,
                        "capture": source.metadata(),
                        "episodeExecutionId": runtime.run["run_id"] if runtime else None,
                    }
                    target = private_path(f".local/edge-control/{config.cameraId}-status.json")
                    status_retries += publish_status(target, status)
                    last_status = now
                if paused or health.run_conflict or now < next_analysis:
                    sleep(0.02)
                    continue
                if health.network["events"] == "STORAGE_ERROR":
                    raise EdgeError(
                        "STORAGE_ERROR", "Falha no envio persistente; confira SQLite local."
                    )
                frame = source.snapshot()
                if frame is None:
                    if source.exhausted:
                        raise EdgeError(
                            source.error_code or "CAPTURE_ERROR",
                            "Tentativas de captura esgotadas; confira webcam.",
                        )
                    sleep(0.01)
                    continue
                if runtime:
                    runtime.store.check_capacity(
                        config.events.delivery.maxItems,
                        config.events.delivery.maxBytes,
                        extra_bytes=65536,
                    )
                check_compatibility(calibration, frame.geometry, config.cameraId)
                frame = replace(
                    frame,
                    index=frame.index + frame_offset,
                    timestamp_ms=frame.timestamp_ms + offset,
                )
                poses, duration = estimator.estimate(frame)
                # Inference may stall: never classify a frame that aged out meanwhile.
                age = (monotonic_ns() - source.last_acquired_ns) / 1e6
                if age > 2000:
                    health.update(flags={"FRAME_TIMEOUT", "LOW_FPS"})
                    next_analysis = monotonic()
                    continue
                inference, reasons = pose_quality(poses, quality_threshold(config))
                o = Observation(
                    schemaVersion=1,
                    runId=capture_run,
                    cameraId=config.cameraId,
                    mode="LIVE",
                    frameIndex=frame.index,
                    timestampMs=frame.timestamp_ms,
                    timestampSource="HOST_MONOTONIC",
                    width=frame.geometry.width,
                    height=frame.geometry.height,
                    rotation=frame.geometry.rotation,
                    poses=poses,
                    poseCount=len(poses),
                    inferenceState=inference,
                    qualityReasons=reasons,
                    meanLuminance=float(cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY).mean()),
                    inferenceMs=duration,
                    modelId=spec.model_id,
                    calibrationId=calibration["calibrationId"],
                    calibrationVersion=calibration["version"],
                    frameFingerprint=hashlib.sha256(frame.bgr.tobytes()).hexdigest(),
                    identicalFrameDurationMs=max(
                        0, round((source.last_acquired_ns - source.info[12]) / 1e6)
                    ),
                )
                features = runtime.process(o, frame) if runtime else None
                metrics.add(o)
                health.observation(o, features)
                health.update(capture="RUNNING")
                if not preview.show(
                    frame, o, calibration["floorPolygon"], quality_threshold(config)
                ):
                    break
                next_analysis = max(now + 1 / config.processing.targetAnalysisFps, monotonic())
                if (
                    config.processing.maxObservations
                    and metrics.analyzed >= config.processing.maxObservations
                ):
                    break
    except KeyboardInterrupt:
        state, code = "INTERRUPTED", 130
    except (EdgeError, sqlite3.Error) as failure:
        state, code = "ERROR", 1
        error = {
            "code": failure.code if isinstance(failure, EdgeError) else "STORAGE_ERROR",
            "message": failure.message
            if isinstance(failure, EdgeError)
            else "Falha SQLite; pendentes preservados.",
        }
        if isinstance(failure, EdgeError) and failure.__cause__ is not None:
            error["diagnostic"] = safe_diagnostic(failure.__cause__)
    except Exception as failure:
        state, code = "ERROR", 1
        error = {
            "code": "PROCESSING_ERROR",
            "message": "Falha local; confira recursos e configuração. Nenhum segredo exibido.",
            "diagnostic": safe_diagnostic(failure),
        }
    finally:
        source.close()
        if health and error:
            flag = (
                "STORAGE_FULL"
                if error["code"] in {"STORAGE_ERROR", "STORAGE_FULL"}
                else "CALIBRATION_REQUIRED"
                if error["code"].startswith("CALIBRATION")
                else "MODEL_ERROR"
                if error["code"].startswith("MODEL")
                else None
                if error["code"] in {"LOCAL_STATUS_WRITE_ERROR", "PROCESSING_ERROR"}
                else "CAPTURE_ERROR"
            )
            health.update(capture="ERROR", flags={flag} if flag else set())
        if network:
            network.close()
    report = {
        "schemaVersion": 1,
        "command": "run",
        "status": "ok" if code == 0 else "error",
        "mode": "LIVE",
        "diagnosticReportId": report_id,
        "captureState": state,
        "error": error,
        "localStatusRetries": status_retries,
        "runId": health.run_id if health else None,
        "source": source.metadata(),
        "model": {
            **model_metadata(spec),
        },
        "metrics": metrics.summary(),
        "temporal": temporal,
        "framesSaved": temporal.get("snapshotCaptures", 0) > 0,
        "network": health.network if health else {},
        "heartbeat": health.snapshot() if health else None,
        "reportPath": str(directory / "report.json"),
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report, code
