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
from radar_edge.config import EdgeConfig, private_path
from radar_edge.errors import EdgeError
from radar_edge.estimator import MediaPipeEstimator
from radar_edge.metrics import Metrics
from radar_edge.model import file_hash, get_model_spec
from radar_edge.observations import Observation, pose_quality
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
    metrics = Metrics(config.processing.minLandmarkVisibility)
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
    preview_paused_seconds = 0.0
    try:
        with ExitStack() as resources:
            resources.callback(exporter.close)
            resources.enter_context(source)
            frame = source.read()
            calibration = load_calibration(config.calibrationPath)
            check_compatibility(calibration, frame.geometry, config.cameraId)
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
                MediaPipeEstimator(config.model.path, config.model.variant)
            )
            model_loaded = True
            preview = resources.enter_context(
                LocalPreview(config.processing.preview, config.processing.previewStartPaused)
            )
            if health is not None:
                preview.on_pause = lambda paused: health.update(
                    capture="PAUSED" if paused else "RUNNING", flags=set()
                )
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
                    inference_state, reasons = pose_quality(
                        poses, config.processing.minLandmarkVisibility
                    )
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
                    )
                    if runtime is not None and frame.index <= runtime.run["frame_index"]:
                        # Decode and warm the VIDEO tracker, but do not replay decisions,
                        # accumulate recovery time or repeat exported observations.
                        warmup_observations += 1
                        frame = source.read()
                        continue
                    if runtime is not None:
                        runtime.process(observation, frame)
                    if health is not None:
                        health.observation(observation, runtime.previous_features)
                    metrics.add(observation)
                    sequence.update(f"{frame.index}:{frame.timestamp_ms}\n".encode())
                    exporter.write(observation)
                    if not preview.show(
                        frame,
                        observation,
                        calibration["floorPolygon"],
                        config.processing.minLandmarkVisibility,
                    ):
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
                frame = source.read()
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
        "workerVersion": "edge-temporal-v1" if config.events.enabled else "edge-pose-v1",
        "source": {**source.metadata(), "sha256": video_hash},
        "model": {
            "id": model_spec.model_id,
            "sha256": model_spec.sha256,
            "loaded": model_loaded,
            "delegate": "CPU",
            "runningMode": "VIDEO",
            "numPoses": 2,
            "segmentationMasks": False,
        },
        "calibration": {"id": calibration["calibrationId"], "version": calibration["version"]}
        if calibration
        else None,
        "processing": config.processing.model_dump(),
        "decodedFrames": source.frames_read,
        "mediaSequenceSha256": sequence.hexdigest(),
        "metrics": metrics.summary(),
        "observationExport": {
            "enabled": config.diagnostics.exportObservations,
            "count": exporter.count,
            "bytes": exporter.bytes,
            "truncated": exporter.truncated,
        },
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
        with MediaPipeEstimator(config.model.path, config.model.variant) as estimator:
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
