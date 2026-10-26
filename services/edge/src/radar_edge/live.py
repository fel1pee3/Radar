"""One native webcam, bounded capture and independent current-health/delivery loops."""

import hashlib
import json
import os
import sqlite3
from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from time import monotonic, monotonic_ns, perf_counter, sleep
from uuid import uuid4

import cv2

from radar_edge.calibration import check_compatibility, load_calibration
from radar_edge.config import private_path, quality_threshold
from radar_edge.decision_trace import DecisionTrace
from radar_edge.errors import EdgeError
from radar_edge.estimator import create_estimator, perception_summary, reset_processing_preference
from radar_edge.event_runtime import EventRuntime
from radar_edge.features import QualityGate, extract_features
from radar_edge.health import LiveHealth, NetworkWorker
from radar_edge.local_status import publish_status, safe_diagnostic
from radar_edge.metrics import Metrics
from radar_edge.model import file_hash, get_model_spec, model_metadata
from radar_edge.observations import Observation, pose_quality
from radar_edge.policy import configured_policy
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
        with create_estimator(
            config.model.path,
            config.model.variant,
            **({"recovery": config.model.recovery} if config.model.recovery != "NONE" else {}),
            **(
                {"runtime_profile": config.model.runtimeProfile}
                if config.model.runtimeProfile != "REFERENCE_4_SPIN"
                else {}
            ),
        ) as estimator:
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


def run_live(config, *, technical_stream=False):
    if technical_stream and (
        config.source.kind != "FILE"
        or config.events.delivery.enabled
        or config.events.snapshotAuthorized
    ):
        raise EdgeError(
            "TECHNICAL_STREAM_CONFIG", "Reprodução técnica exige FILE isolado, sem HTTP/snapshot."
        )
    if not technical_stream and config.source.kind != "WEBCAM":
        raise EdgeError(
            "SOURCE_KIND_INVALID", "Use FILE técnico explicitamente ou webcam configurada."
        )
    if (
        technical_stream
        and config.events.enabled
        and private_path(config.events.outboxPath).exists()
    ):
        raise EdgeError(
            "TECHNICAL_OUTBOX_EXISTS",
            "Use uma fila técnica nova; resultados anteriores são preservados.",
        )
    spec = get_model_spec(config.model.variant)
    report_id = str(uuid4())
    directory = private_path(config.diagnostics.outputDirectory) / report_id
    directory.mkdir(parents=True)
    metrics = Metrics(quality_threshold(config), model_metadata(spec)["qualitySource"])
    estimator = None
    if technical_stream:
        from radar_edge.paced_file import PacedFileSource

        source = PacedFileSource(config.source, config.processing.maxWidth)
    else:
        source = WebcamSource(config.source, config.processing.maxWidth)
    profile_enabled = config.diagnostics.profileProcessing
    warmup_ms = 0.0
    profile_write_ms = 0.0
    idle_sleep_ms = 0.0
    previous_profile_end = None
    processing_profile_count = 0
    stale_analysis_discarded = 0
    attempt_timing = {
        "attempts": 0,
        "totalInferenceMs": 0.0,
        "maxInferenceMs": 0.0,
        "maxFrameAgeAtStartMs": 0.0,
        "maxFrameAgeAfterInferenceMs": 0.0,
    }
    offset = 0
    calibration = None
    runtime = None
    network = None
    health = None
    temporal = {"enabled": config.events.enabled}
    state, code, error = "ENDED", 0, None
    last_status = 0.0
    status_retries = 0
    previous_command = None if technical_stream else _control(config)
    started = monotonic()
    preview = None
    trace = None
    try:
        trace = DecisionTrace(
            directory,
            config.diagnostics,
            os.environ.get("EVIDENCE_MODE", config.events.evidenceMode),
        )
        trace.status("OPENING", "SOURCE_OPEN_REQUEST")
        with ExitStack() as resources:
            resources.enter_context(source)
            first = source.read()
            trace.status("RUNNING", "SOURCE_FRAME_AVAILABLE")
            try:
                calibration = load_calibration(config.calibrationPath)
                check_compatibility(calibration, first.geometry, config.cameraId)
                if not technical_stream and (
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
                    EventRuntime(
                        config,
                        calibration,
                        file_hash(Path(config.source.path)) if technical_stream else "WEBCAM",
                        first.geometry,
                        async_delivery=True,
                        decision_trace=trace,
                    )
                )
                resources.callback(lambda: temporal.update(runtime.summary()))
            diagnostic_gate = (
                QualityGate(configured_policy(config.events.policy))
                if trace.enabled and runtime is None
                else None
            )
            capture_run = runtime.capture_run_id if runtime else str(uuid4())
            health = LiveHealth(config, capture_run, calibration)
            health.source = source
            network = resources.enter_context(NetworkWorker(config, health))
            # Save error/final state before the network resource is closed.
            estimator = resources.enter_context(
                create_estimator(
                    config.model.path,
                    config.model.variant,
                    **(
                        {"recovery": config.model.recovery}
                        if config.model.recovery != "NONE"
                        else {}
                    ),
                    **(
                        {"runtime_profile": config.model.runtimeProfile}
                        if config.model.runtimeProfile != "REFERENCE_4_SPIN"
                        else {}
                    ),
                )
            )
            preview = LocalPreview(config.processing.preview, config.processing.previewStartPaused)
            if config.processing.previewStabilization:
                preview.enable_stabilization()
            preview.name = (
                "Radar - arquivo em transmissao TECNICA REPLAY"
                if technical_stream
                else "Radar - poses locais LIVE"
            )
            preview.blocking_pause = False
            resources.enter_context(preview)
            if runtime and not technical_stream:
                anchor = datetime.fromisoformat(runtime.run["anchor"].replace("Z", "+00:00"))
                offset = max(
                    runtime.run["timestamp_ms"] + 1 - first.timestamp_ms,
                    round((source.start_utc - anchor).total_seconds() * 1000),
                )
                frame_offset = runtime.run["frame_index"] + 1
            else:
                offset, frame_offset = 0, 0
            if technical_stream:
                import numpy as np

                if hasattr(estimator, "infer_image"):
                    warm_started = perf_counter()
                    estimator.infer_image(np.full((640, 640, 3), 114, dtype=np.uint8))
                    warmup_ms = (perf_counter() - warm_started) * 1000
                source.start_stream()
            paused = False
            capture_unavailable = False
            reconnect_count = getattr(source, "reconnects", 0)

            def pause(value):
                nonlocal paused
                paused = value
                reset_processing_preference(estimator, "PAUSE_OR_RESUME")
                if runtime:
                    runtime.break_observation()
                trace.status("PAUSED" if value else "RUNNING", "OPERATOR_PREVIEW_CONTROL")
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
                command = None if technical_stream else _control(config)
                if command and command != previous_command:
                    previous_command = command
                    if command["action"] == "stop":
                        break
                    if command["action"] == "pause" and not paused:
                        preview.set_paused(True)
                    if command["action"] == "resume" and paused:
                        preview.set_paused(False)
                    if command["action"] == "reconnect":
                        reset_processing_preference(estimator, "OPERATOR_RECONNECT")
                        if runtime:
                            runtime.break_observation()
                        trace.status("RECONNECTING", "OPERATOR_RECONNECT")
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
                if not technical_stream and now - last_status >= 1:
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
                    slept = perf_counter()
                    sleep(0.02)
                    idle_sleep_ms += (perf_counter() - slept) * 1000
                    continue
                if health.network["events"] == "STORAGE_ERROR":
                    raise EdgeError(
                        "STORAGE_ERROR", "Falha no envio persistente; confira SQLite local."
                    )
                frame = source.snapshot()
                if technical_stream and frame is None and source.ended and not source.exhausted:
                    if runtime:
                        runtime.finish()
                    break
                current_reconnects = getattr(source, "reconnects", 0)
                if current_reconnects != reconnect_count:
                    reset_processing_preference(estimator, "SOURCE_RECONNECT")
                    reconnect_count = current_reconnects
                    if runtime:
                        runtime.break_observation()
                    trace.status("RECONNECTING", "SOURCE_RECONNECT")
                if frame is None:
                    if not capture_unavailable and (
                        getattr(source, "error_code", None) or source.exhausted
                    ):
                        capture_unavailable = True
                        reset_processing_preference(estimator, "SOURCE_UNAVAILABLE")
                        if runtime:
                            runtime.break_observation()
                        trace.status("UNAVAILABLE", "WAITING_FOR_FRESH_FRAME")
                    if source.exhausted:
                        raise EdgeError(
                            source.error_code or "CAPTURE_ERROR",
                            "Tentativas de captura esgotadas; confira webcam.",
                        )
                    slept = perf_counter()
                    sleep(0.01)
                    idle_sleep_ms += (perf_counter() - slept) * 1000
                    continue
                if capture_unavailable:
                    capture_unavailable = False
                    trace.status("RUNNING", "FRESH_FRAME_AFTER_UNAVAILABLE")
                processing_started = perf_counter()
                profile = {
                    "monotonicStartNs": monotonic_ns(),
                    "waitSleepMs": idle_sleep_ms,
                    "betweenProcessingMs": (processing_started - previous_profile_end) * 1000
                    if previous_profile_end is not None
                    else None,
                }
                idle_sleep_ms = 0.0
                if runtime:
                    runtime.store.check_capacity(
                        config.events.delivery.maxItems,
                        config.events.delivery.maxBytes,
                        extra_bytes=65536,
                    )
                check_compatibility(calibration, frame.geometry, config.cameraId)
                profile["outerCapacityAndCompatibilityMs"] = (
                    perf_counter() - processing_started
                ) * 1000
                frame = replace(
                    frame,
                    index=frame.index + frame_offset,
                    timestamp_ms=frame.timestamp_ms + offset,
                )
                age_at_start = (monotonic_ns() - source.last_acquired_ns) / 1e6
                poses, duration = estimator.estimate(frame)
                pose_finished = perf_counter()
                # Inference may stall: never classify a frame that aged out meanwhile.
                age = (monotonic_ns() - source.last_acquired_ns) / 1e6
                attempt_timing["attempts"] += 1
                attempt_timing["totalInferenceMs"] += duration
                attempt_timing["maxInferenceMs"] = max(attempt_timing["maxInferenceMs"], duration)
                attempt_timing["maxFrameAgeAtStartMs"] = max(
                    attempt_timing["maxFrameAgeAtStartMs"], age_at_start
                )
                attempt_timing["maxFrameAgeAfterInferenceMs"] = max(
                    attempt_timing["maxFrameAgeAfterInferenceMs"], age
                )
                if age > 2000:
                    stale_analysis_discarded += 1
                    trace.status("RUNNING", "STALE_ANALYSIS_DISCARDED_NO_DECISION")
                    health.update(flags={"FRAME_TIMEOUT", "LOW_FPS"})
                    next_analysis = monotonic()
                    continue
                inference, reasons = pose_quality(poses, quality_threshold(config))
                o = Observation(
                    schemaVersion=1,
                    runId=capture_run,
                    cameraId=config.cameraId,
                    mode="REPLAY" if technical_stream else "LIVE",
                    frameIndex=frame.index,
                    timestampMs=frame.timestamp_ms,
                    timestampSource=frame.timestamp_source
                    if technical_stream
                    else "HOST_MONOTONIC",
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
                    personDetections=getattr(estimator, "person_detections", ()),
                    perceptionPasses=getattr(estimator, "perception_passes", ()),
                    perceptionAttempts=tuple(getattr(estimator, "perception_attempts", ())),
                    frameAgeAtAnalysisStartMs=age_at_start,
                    frameAgeAfterInferenceMs=age,
                    personProposalScore=getattr(estimator, "person_proposal_score", None),
                )
                observation_ready = perf_counter()
                features = (
                    runtime.process(o, frame, acquired_ns=source.last_acquired_ns)
                    if runtime
                    else None
                )
                if diagnostic_gate is not None:
                    features = diagnostic_gate.apply(
                        o, extract_features(o, calibration["floorPolygon"], diagnostic_gate.policy)
                    )
                    trace.observation(o, features, diagnostic_gate.policy, None, None)
                metrics.add(o)
                health.observation(o, features)
                health.update(capture="RUNNING")
                before_preview = perf_counter()
                if not preview.show(
                    frame, o, calibration["floorPolygon"], quality_threshold(config)
                ):
                    break
                preview_finished = perf_counter()
                if profile_enabled:
                    profile.update(
                        {
                            "inferenceMs": duration,
                            "observationPreparationMs": (observation_ready - pose_finished) * 1000,
                            "runtimeAndMetricsMs": (before_preview - observation_ready) * 1000,
                            "previewMs": (preview_finished - before_preview) * 1000,
                            "totalProcessingMs": (preview_finished - processing_started) * 1000,
                            "eventRuntimeStages": getattr(runtime, "last_processing", {}),
                            "monotonicFinishedNs": monotonic_ns(),
                            "frameAgeAfterPreviewMs": (monotonic_ns() - source.last_acquired_ns)
                            / 1e6,
                            "attempts": getattr(estimator, "perception_attempts", []),
                        }
                    )
                    write_started = perf_counter()
                    trace.processing(frame.timestamp_ms, profile)
                    profile_write_ms += (perf_counter() - write_started) * 1000
                    processing_profile_count += 1
                previous_profile_end = perf_counter()
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
        if trace is not None:
            try:
                trace.status(state, error["code"] if error else state)
            except EdgeError as failure:
                if error is None:
                    state, code = "ERROR", 1
                    error = {"code": failure.code, "message": failure.message}
            finally:
                trace.close()
            if trace.write_failed and error is None:
                state, code = "ERROR", 1
                error = {
                    "code": "DECISION_TRACE_WRITE_ERROR",
                    "message": "Falha ao concluir diagnóstico privado; confira acesso e espaço.",
                }
    report = {
        "schemaVersion": 1,
        "command": "run",
        "status": "ok" if code == 0 else "error",
        "mode": "REPLAY" if technical_stream else "LIVE",
        "executionKind": "TECHNICAL_PACED_FILE_NOT_WEBCAM"
        if technical_stream
        else "PHYSICAL_WEBCAM",
        "runtimeProfile": config.model.runtimeProfile,
        **perception_summary(estimator),
        "warmupSyntheticExcludedMs": warmup_ms,
        "processingProfile": {
            "enabled": profile_enabled,
            "records": processing_profile_count,
            "writeTotalMs": profile_write_ms,
        },
        "diagnosticReportId": report_id,
        "captureState": state,
        "error": error,
        "localStatusRetries": status_retries,
        "runId": health.run_id if health else None,
        "source": source.metadata(),
        "sourceTimestampOffsetMs": offset,
        "staleAnalysesDiscarded": stale_analysis_discarded,
        "liveInferenceAttemptTiming": attempt_timing,
        "model": {
            **model_metadata(spec),
        },
        "metrics": metrics.summary(),
        "decisionExport": trace.summary() if trace else {"enabled": False},
        "preview": preview.summary() if preview and hasattr(preview, "summary") else None,
        "temporal": temporal,
        "framesSaved": temporal.get("snapshotCaptures", 0) > 0,
        "network": health.network if health else {},
        "heartbeat": health.snapshot() if health else None,
        "reportPath": str(directory / "report.json"),
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report, code
