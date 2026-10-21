"""FILE -> local observations/optional preview -> bounded private diagnostics. No HTTP."""

import hashlib
import json
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
from radar_edge.model import MODEL_ID, MODEL_SHA256, file_hash
from radar_edge.observations import Observation, pose_quality
from radar_edge.preview import LocalPreview
from radar_edge.source import FileSource, MediaSampler


class ObservationExport:
    def __init__(self, path: Path, config):
        self.stream = path.open("xb") if config.exportObservations else None
        self.config = config
        self.count = 0
        self.bytes = 0
        self.truncated = False

    def write(self, observation: Observation):
        if self.stream is None or self.truncated:
            return
        data = (
            json.dumps(observation.to_dict(), allow_nan=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
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


def run_pipeline(config: EdgeConfig) -> tuple[dict, int]:
    run_id = str(uuid4())
    directory = private_path(config.diagnostics.outputDirectory) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    metrics = Metrics()
    source = FileSource(config.source, config.processing.maxWidth)
    sequence = hashlib.sha256()
    exporter = ObservationExport(directory / "observations.jsonl", config.diagnostics)
    state = "ENDED"
    error = None
    code = 0
    video_hash = None
    calibration = None
    model_loaded = False
    try:
        with ExitStack() as resources:
            resources.callback(exporter.close)
            resources.enter_context(source)
            frame = source.read()
            calibration = load_calibration(config.calibrationPath)
            check_compatibility(calibration, frame.geometry, config.cameraId)
            video_hash = file_hash(Path(config.source.path))
            estimator = resources.enter_context(MediaPipeEstimator(config.model.path))
            model_loaded = True
            preview = resources.enter_context(LocalPreview(config.processing.preview))
            sampler = MediaSampler(config.processing.targetAnalysisFps)
            playback_start = perf_counter()
            while frame is not None:
                if sampler.accepts(frame.timestamp_ms):
                    if config.processing.replaySpeed > 0:
                        remaining = frame.timestamp_ms / 1000 / config.processing.replaySpeed - (
                            perf_counter() - playback_start
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
                        runId=run_id,
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
                        modelId=MODEL_ID,
                        calibrationId=calibration["calibrationId"],
                        calibrationVersion=calibration["version"],
                    )
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
    except KeyboardInterrupt:
        state, code = "INTERRUPTED", 130
    except EdgeError as failure:
        state, code = "ERROR", 1
        error = {"code": failure.code, "message": failure.message}
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
        "runId": run_id,
        "mode": "REPLAY",
        "captureState": state,
        "error": error,
        "workerVersion": "edge-pose-v1",
        "source": {**source.metadata(), "sha256": video_hash},
        "model": {
            "id": MODEL_ID,
            "sha256": MODEL_SHA256,
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
        "framesSaved": False,
        "incidentsEmitted": False,
        "warnings": ["INDEX_FPS assumes constant frame rate; not reliable VFR timing"]
        if source.clock and source.clock.fallback
        else [],
    }
    (directory / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8"
    )
    return {**report, "reportPath": str((directory / "report.json").relative_to(Path.cwd()))}, code


def doctor(config: EdgeConfig) -> dict:
    with FileSource(config.source, config.processing.maxWidth) as source:
        frame = source.read()
        with MediaPipeEstimator(config.model.path) as estimator:
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
            "modelId": MODEL_ID,
            "modelSha256": MODEL_SHA256,
            "modelLoaded": True,
            "inferenceExecuted": True,
            "poseCount": len(poses),
            "firstInferenceMs": duration,
            "calibration": calibration_status,
            "framesSaved": False,
            "cameraOpened": False,
        }
