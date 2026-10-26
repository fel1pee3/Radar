"""FILE observations, optional temporal events, durable storage and local delivery."""

import hashlib
import json
import os
import sqlite3
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter, sleep
from uuid import uuid4

import cv2

from radar_edge.calibration import check_compatibility, load_calibration
from radar_edge.config import EdgeConfig, private_path, quality_threshold
from radar_edge.decision_trace import DecisionTrace
from radar_edge.errors import EdgeError
from radar_edge.estimator import create_estimator
from radar_edge.features import QualityGate, extract_features
from radar_edge.metrics import Metrics
from radar_edge.model import file_hash, get_model_spec, model_metadata
from radar_edge.observations import Observation, pose_quality
from radar_edge.policy import configured_policy
from radar_edge.preview import LocalPreview
from radar_edge.source import FileSource, MediaSampler


class ObservationExport:
    def __init__(self, path: Path, config, evidence_mode="skeleton"):
        self.stream = path.open("xb") if config.exportObservations else None
        self.config = config
        self.evidence_mode = evidence_mode
        self.count = 0
        self.bytes = 0
        self.truncated = False

    def write(self, observation: Observation):
        if self.stream is None or self.truncated:
            return
        value = observation.to_dict()
        if self.evidence_mode == "none":
            value["poses"] = []
            value["personDetections"] = []
        data = (json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        if (
            self.count >= self.config.maxExportObservations
            or self.bytes + len(data) > self.config.maxExportBytes
        ):
            self.truncated = True
            return
        self.stream.write(data)
        self.count += 1
        self.bytes += len(data)

    def close(self):
        if self.stream is not None:
            self.stream.close()


def run_pipeline(config: EdgeConfig, evaluation_excluded=None) -> tuple[dict, int]:
    if config.source.kind == "WEBCAM":
        from radar_edge.live import run_live

        return run_live(config)
    model_spec = get_model_spec(config.model.variant)
    run_id = str(uuid4())
    directory = private_path(config.diagnostics.outputDirectory) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    metrics = Metrics(quality_threshold(config), model_metadata(model_spec)["qualitySource"])
    source = FileSource(config.source, config.processing.maxWidth)
    sequence = hashlib.sha256()
    exporter = ObservationExport(
        directory / "observations.jsonl",
        config.diagnostics,
        os.environ.get("EVIDENCE_MODE", config.events.evidenceMode),
    )
    state = "ENDED"
    error = None
    code = 0
    video_hash = None
    calibration = None
    model_loaded = False
    runtime = None
    health = network = None
    temporal_summary = {"enabled": False}
    warmup_observations = 0
    preview = None
    preview_paused_seconds = 0.0
    trace = None
    capture_read_seconds = 0.0
    capture_read_count = 0
    preview_call_seconds = 0.0

    def read_frame():
        nonlocal capture_read_seconds, capture_read_count
        started = perf_counter()
        try:
            return source.read()
        finally:
            capture_read_seconds += perf_counter() - started
            capture_read_count += 1

    try:
        trace = DecisionTrace(
            directory,
            config.diagnostics,
            os.environ.get("EVIDENCE_MODE", config.events.evidenceMode),
        )
        trace.status("OPENING", "SOURCE_OPEN_REQUEST")
        with ExitStack() as resources:
            resources.callback(exporter.close)
            resources.enter_context(source)
            frame = read_frame()
            calibration = load_calibration(config.calibrationPath)
            check_compatibility(calibration, frame.geometry, config.cameraId)
            trace.status("RUNNING", "SOURCE_FRAME_AVAILABLE")
            diagnostic_gate = (
                QualityGate(configured_policy(config.events.policy))
                if trace.enabled and not config.events.enabled
                else None
            )
            video_hash = file_hash(Path(config.source.path))
            if config.events.enabled:
                from radar_edge.event_runtime import EventRuntime

                runtime = resources.enter_context(
                    EventRuntime(
                        config,
                        calibration,
                        video_hash,
                        frame.geometry,
                        evaluation_excluded,
                        async_delivery=True,
                        decision_trace=trace,
                    )
                )
                resources.callback(lambda: temporal_summary.update(runtime.summary()))
                if runtime.run["completed"]:
                    frame = None
                from radar_edge.health import LiveHealth, NetworkWorker

                health = LiveHealth(config, runtime.capture_run_id, calibration)
                if frame is None:
                    health.update(capture="ENDED", flags=set())
                network = resources.enter_context(NetworkWorker(config, health))
            estimator = resources.enter_context(
                create_estimator(
                    config.model.path,
                    config.model.variant,
                    **(
                        {"recovery": config.model.recovery}
                        if config.model.recovery != "NONE"
                        else {}
                    ),
                )
            )
            model_loaded = True
            preview = resources.enter_context(
                LocalPreview(config.processing.preview, config.processing.previewStartPaused)
            )
            if config.processing.previewStabilization:
                preview.enable_stabilization()
            if health is not None:

                def on_pause(paused):
                    runtime.break_observation()
                    health.update(capture="PAUSED" if paused else "RUNNING", flags=set())
                    trace.status("PAUSED" if paused else "RUNNING", "OPERATOR_PREVIEW_CONTROL")

                preview.on_pause = on_pause
            sampler = MediaSampler(config.processing.targetAnalysisFps)
            playback_start = perf_counter()
            last_frame_digest = None
            identical_since = None
            while frame is not None:
                if health is not None and health.run_conflict:
                    raise EdgeError("RUN_CONFLICT", "Outra execução controla a saúde desta câmera.")
                if health is not None and health.network["events"] == "STORAGE_ERROR":
                    raise EdgeError("STORAGE_ERROR", "Falha na persistência local de eventos.")
                frame_digest = hashlib.sha256(frame.bgr.tobytes()).hexdigest()
                if frame_digest != last_frame_digest:
                    identical_since = frame.timestamp_ms
                last_frame_digest = frame_digest
                if sampler.accepts(frame.timestamp_ms):
                    if config.processing.replaySpeed > 0:
                        offset = max(0, runtime.run["timestamp_ms"]) if runtime else 0
                        remaining = (
                            frame.timestamp_ms - offset
                        ) / 1000 / config.processing.replaySpeed - (
                            perf_counter() - playback_start - preview.paused_seconds
                        )
                        if remaining > 0:
                            sleep(remaining)
                    poses, inference_ms = estimator.estimate(frame)
                    inference_state, reasons = pose_quality(poses, quality_threshold(config))
                    luminance = float(cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY).mean())
                    # Instantaneous luminance diagnostic; temporal LOW_LIGHT policy belongs to 05.
                    if luminance < 25:
                        reasons = (*reasons, "DARK_FRAME")
                    observation = Observation(
                        schemaVersion=1,
                        runId=runtime.capture_run_id if runtime else run_id,
                        cameraId=config.cameraId,
                        mode="REPLAY",
                        frameIndex=frame.index,
                        timestampMs=frame.timestamp_ms,
                        timestampSource=frame.timestamp_source,
                        width=frame.geometry.width,
                        height=frame.geometry.height,
                        rotation=frame.geometry.rotation,
                        poses=poses,
                        poseCount=len(poses),
                        inferenceState=inference_state,
                        qualityReasons=reasons,
                        meanLuminance=luminance,
                        inferenceMs=inference_ms,
                        modelId=model_spec.model_id,
                        calibrationId=calibration["calibrationId"],
                        calibrationVersion=calibration["version"],
                        frameFingerprint=frame_digest,
                        identicalFrameDurationMs=frame.timestamp_ms - identical_since,
                        personDetections=getattr(estimator, "person_detections", ()),
                        perceptionPasses=getattr(estimator, "perception_passes", ()),
                        personProposalScore=getattr(estimator, "person_proposal_score", None),
                    )
                    if runtime is not None and frame.index <= runtime.run["frame_index"]:
                        # Decode and warm the VIDEO tracker, but do not replay decisions,
                        # accumulate recovery time or repeat exported observations.
                        warmup_observations += 1
                        frame = read_frame()
                        continue
                    if runtime is not None:
                        runtime.process(observation, frame)
                    elif diagnostic_gate is not None:
                        features = diagnostic_gate.apply(
                            observation,
                            extract_features(
                                observation, calibration["floorPolygon"], diagnostic_gate.policy
                            ),
                        )
                        trace.observation(observation, features, diagnostic_gate.policy, None, None)
                    if health is not None:
                        health.observation(observation, runtime.previous_features)
                    metrics.add(observation)
                    sequence.update(f"{frame.index}:{frame.timestamp_ms}\n".encode())
                    exporter.write(observation)
                    preview_started = perf_counter()
                    keep_running = preview.show(
                        frame,
                        observation,
                        calibration["floorPolygon"],
                        quality_threshold(config),
                    )
                    preview_call_seconds += perf_counter() - preview_started
                    if not keep_running:
                        state = "STOPPED_REQUEST"
                        break
                    if (
                        config.processing.maxObservations is not None
                        and metrics.analyzed >= config.processing.maxObservations
                    ):
                        state = "STOPPED_LIMIT"
                        break
                else:
                    metrics.skipped += 1
                frame = read_frame()
            if runtime is not None and state == "ENDED":
                runtime.finish()
            preview_paused_seconds = preview.paused_seconds
    except KeyboardInterrupt:
        state, code = "INTERRUPTED", 130
    except EdgeError as failure:
        state, code = "ERROR", 1
        error = {"code": failure.code, "message": failure.message}
    except sqlite3.Error:
        state, code = "ERROR", 1
        error = {
            "code": "STORAGE_ERROR",
            "message": "Falha no SQLite; verifique espaço e acesso. "
            "Evento não confirmado permanece local.",
        }
    except Exception:
        state, code = "ERROR", 1
        error = {
            "code": "PROCESSING_ERROR",
            "message": "Falha no processamento local; verifique configuração e recursos.",
        }
    finally:
        exporter.close()
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
        "runId": temporal_summary.get("runId", run_id),
        "diagnosticReportId": run_id,
        "captureRunId": runtime.capture_run_id if runtime else run_id,
        "health": health.snapshot() if health else None,
        "network": network.health.network if network else None,
        "mode": "REPLAY",
        "captureState": state,
        "error": error,
        "workerVersion": (
            "edge-posture-v3"
            if config.posture.method == "MULTICLASS_BODY_V3"
            else "edge-posture-v2"
            if config.posture.method == "LINEAR_BODY_V2"
            else "edge-posture-v1"
            if config.posture.method == "LINEAR_CONTEXT_V1"
            else "edge-temporal-v1"
            if config.events.enabled
            else "edge-pose-v1"
        ),
        "source": {**source.metadata(), "sha256": video_hash},
        "model": {
            **model_metadata(model_spec),
            "loaded": model_loaded,
        },
        "calibration": {"id": calibration["calibrationId"], "version": calibration["version"]}
        if calibration
        else None,
        "processing": config.processing.model_dump(),
        "decodedFrames": source.frames_read,
        "mediaSequenceSha256": sequence.hexdigest(),
        "metrics": {
            **metrics.summary(),
            "captureRead": {
                "calls": capture_read_count,
                "totalMs": capture_read_seconds * 1000,
                "scope": "FILE decode, timestamp and resize; includes end-of-file read",
            },
            "previewCalls": {
                "enabled": config.processing.preview,
                "totalMs": preview_call_seconds * 1000,
                "scope": (
                    "show calls including pacing/interaction; disabled is not display throughput"
                ),
            },
        },
        "observationExport": {
            "enabled": config.diagnostics.exportObservations,
            "count": exporter.count,
            "bytes": exporter.bytes,
            "truncated": exporter.truncated,
        },
        "decisionExport": trace.summary() if trace else {"enabled": False},
        "preview": preview.summary() if preview and hasattr(preview, "summary") else None,
        "framesSaved": temporal_summary.get("snapshotCaptures", 0) > 0,
        "incidentsEmitted": temporal_summary.get("generatedEvents", 0) > 0,
        "temporal": temporal_summary,
        "trackerWarmupObservations": warmup_observations,
        "previewPausedSeconds": preview_paused_seconds,
        "warnings": ["INDEX_FPS assumes constant frame rate; not reliable VFR timing"]
        if source.clock and source.clock.fallback
        else [],
    }
    (directory / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8"
    )
    return {**report, "reportPath": str((directory / "report.json").relative_to(Path.cwd()))}, code


def doctor(config: EdgeConfig) -> dict:
    if config.source.kind == "WEBCAM":
        from radar_edge.live import doctor_live

        return doctor_live(config)
    model_spec = get_model_spec(config.model.variant)
    with FileSource(config.source, config.processing.maxWidth) as source:
        frame = source.read()
        with create_estimator(
            config.model.path,
            config.model.variant,
            **({"recovery": config.model.recovery} if config.model.recovery != "NONE" else {}),
        ) as estimator:
            poses, duration = estimator.estimate(frame)
        calibration_status = "MISSING"
        if private_path(config.calibrationPath).exists():
            check_compatibility(
                load_calibration(config.calibrationPath), frame.geometry, config.cameraId
            )
            calibration_status = "COMPATIBLE"
        return {
            "status": "ok",
            "command": "doctor",
            "mode": "REPLAY",
            "source": {**source.metadata(), "sha256": file_hash(Path(config.source.path))},
            "modelId": model_spec.model_id,
            "modelSha256": model_spec.sha256,
            "modelLoaded": True,
            "inferenceExecuted": True,
            "poseCount": len(poses),
            "firstInferenceMs": duration,
            "calibration": calibration_status,
            "framesSaved": False,
            "cameraOpened": False,
        }
