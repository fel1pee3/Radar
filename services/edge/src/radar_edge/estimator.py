"""Synchronous CPU Tasks VIDEO adapter. Never substitutes a failed inference with NO_POSE."""

from time import perf_counter
from typing import Protocol

import cv2
import numpy as np

from radar_edge.errors import EdgeError
from radar_edge.model import ModelVariant, get_model_spec, verify_model
from radar_edge.observations import Pose, body_poses
from radar_edge.source import Frame


class PoseEstimator(Protocol):
    def estimate(self, frame: Frame) -> tuple[tuple[Pose, ...], float]: ...
    def close(self) -> None: ...


class MediaPipeEstimator:
    def __init__(self, model_path: str, variant: ModelVariant = "lite"):
        self.model_path = model_path
        self.variant = variant
        spec = get_model_spec(variant)
        self.model_id = spec.model_id
        self.model_sha256 = spec.sha256
        self.landmarker = None
        self.previous_ms = -1

    def __enter__(self):
        path = verify_model(self.model_path, self.variant)
        from mediapipe.tasks.python import BaseOptions, vision

        try:
            self.landmarker = vision.PoseLandmarker.create_from_options(
                vision.PoseLandmarkerOptions(
                    base_options=BaseOptions(
                        model_asset_path=str(path), delegate=BaseOptions.Delegate.CPU
                    ),
                    running_mode=vision.RunningMode.VIDEO,
                    num_poses=2,
                    output_segmentation_masks=False,
                    min_pose_detection_confidence=0.5,
                    min_pose_presence_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
            )
        except Exception:
            raise EdgeError(
                "MODEL_LOAD_ERROR", "MediaPipe não conseguiu carregar o bundle verificado em CPU."
            ) from None
        return self

    def estimate(self, frame: Frame) -> tuple[tuple[Pose, ...], float]:
        from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

        if frame.timestamp_ms <= self.previous_ms:
            raise EdgeError("MODEL_TIMESTAMP_ERROR", "MediaPipe VIDEO exige timestamps crescentes.")
        try:
            rgb = np.ascontiguousarray(cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2RGB))
            image = Image(image_format=ImageFormat.SRGB, data=rgb)
            start = perf_counter()
            result = self.landmarker.detect_for_video(image, frame.timestamp_ms)
            elapsed = (perf_counter() - start) * 1000
            self.previous_ms = frame.timestamp_ms
            return body_poses(result), elapsed
        except EdgeError:
            raise
        except Exception:
            raise EdgeError(
                "MODEL_INFERENCE_ERROR",
                "Falha na inferência real do MediaPipe; a execução foi interrompida.",
            ) from None

    def close(self):
        if self.landmarker is not None:
            try:
                self.landmarker.close()
            finally:
                self.landmarker = None

    def __exit__(self, *_):
        self.close()
