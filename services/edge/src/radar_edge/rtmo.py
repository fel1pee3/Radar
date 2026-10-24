"""Experimental RTMO-s CPU ONNX adapter; body scores are not visibility/presence.

Official ONNX deployment: OpenMMLab MMPose projects/rtmo (Apache-2.0 code).
Local implementation of documented top-left letterbox and box NMS; no RTMLib
dependency, implicit download, facial output, interpolation or identity tracking.
"""

from time import perf_counter

import cv2
import numpy as np

from radar_edge.errors import EdgeError
from radar_edge.model import verify_model
from radar_edge.observations import Landmark, Pose

COCO_TO_BODY = {
    5: 11,
    6: 12,
    7: 13,
    8: 14,
    9: 15,
    10: 16,
    11: 23,
    12: 24,
    13: 25,
    14: 26,
    15: 27,
    16: 28,
}
DETECTION_THRESHOLD = 0.7
NMS_THRESHOLD = 0.45


def select_detections(detections):
    """Suppress duplicate boxes, preserving multiple distinct people."""
    candidates = np.flatnonzero(detections[:, 4] > DETECTION_THRESHOLD)
    order = candidates[np.argsort(-detections[candidates, 4], kind="stable")]
    kept = []
    while order.size:
        current = int(order[0])
        kept.append(current)
        rest = order[1:]
        if not rest.size:
            break
        box, boxes = detections[current, :4], detections[rest, :4]
        lo = np.maximum(box[:2], boxes[:, :2])
        hi = np.minimum(box[2:], boxes[:, 2:])
        intersection = np.prod(np.maximum(0, hi - lo), axis=1)
        area = np.prod(np.maximum(0, box[2:] - box[:2]))
        areas = np.prod(np.maximum(0, boxes[:, 2:] - boxes[:, :2]), axis=1)
        union = area + areas - intersection
        iou = np.divide(intersection, union, out=np.zeros_like(union), where=union > 0)
        order = rest[iou <= NMS_THRESHOLD]
    return kept


def decode_outputs(outputs, ratio, width, height):
    if len(outputs) != 2:
        raise ValueError("Expected detection and pose outputs")
    detections, keypoints = outputs
    if (
        detections.ndim != 3
        or detections.shape[0] != 1
        or detections.shape[2] != 5
        or keypoints.shape != (1, detections.shape[1], 17, 3)
    ):
        raise ValueError("Unexpected RTMO output shape")
    if not np.isfinite(detections).all() or not np.isfinite(keypoints).all():
        raise ValueError("Nonfinite model output")
    if not ((0 <= keypoints[..., 2]) & (keypoints[..., 2] <= 1)).all():
        raise ValueError("Invalid native keypoint score")
    selected = select_detections(detections[0])
    if len(selected) > 100:
        raise ValueError("Unexpected detection count")
    return tuple(
        Pose(
            tuple(
                Landmark(
                    target,
                    float(keypoints[0, person, source, 0] / ratio / width),
                    float(keypoints[0, person, source, 1] / ratio / height),
                    None,
                    None,
                    None,
                    float(keypoints[0, person, source, 2]),
                )
                for source, target in COCO_TO_BODY.items()
            ),
            qualitySource="RTMO_KEYPOINT_SCORE",
        )
        for person in selected
    )


class RtmoEstimator:
    def __init__(self, model_path, variant="rtmo-s"):
        if variant != "rtmo-s":
            raise EdgeError("INVALID_MODEL_VARIANT", "O adaptador RTMO exige rtmo-s.")
        self.model_path = model_path
        self.session = None
        self.previous_ms = -1

    def __enter__(self):
        path = verify_model(self.model_path, "rtmo-s")
        try:
            import onnxruntime as ort

            options = ort.SessionOptions()
            options.intra_op_num_threads = 4
            options.inter_op_num_threads = 1
            self.session = ort.InferenceSession(
                str(path), sess_options=options, providers=["CPUExecutionProvider"]
            )
        except Exception:
            raise EdgeError(
                "MODEL_LOAD_ERROR", "ONNX Runtime não carregou o RTMO verificado em CPU."
            ) from None
        return self

    def estimate(self, frame):
        if frame.timestamp_ms <= self.previous_ms:
            raise EdgeError("MODEL_TIMESTAMP_ERROR", "Timestamps da análise devem ser crescentes.")
        try:
            start = perf_counter()
            height, width = frame.bgr.shape[:2]
            ratio = min(640 / width, 640 / height)
            resized = cv2.resize(
                frame.bgr, (int(width * ratio), int(height * ratio)), interpolation=cv2.INTER_LINEAR
            )
            image = np.full((640, 640, 3), 114, dtype=np.uint8)
            image[: resized.shape[0], : resized.shape[1]] = resized
            tensor = np.ascontiguousarray(image.transpose(2, 0, 1)[None], dtype=np.float32)
            outputs = self.session.run(["dets", "keypoints"], {"input": tensor})
            poses = decode_outputs(outputs, ratio, width, height)
            self.previous_ms = frame.timestamp_ms
            return poses, (perf_counter() - start) * 1000
        except Exception:
            raise EdgeError(
                "MODEL_INFERENCE_ERROR", "Falha real de inferência RTMO; execução interrompida."
            ) from None

    def close(self):
        self.session = None

    def __exit__(self, *_):
        self.close()
