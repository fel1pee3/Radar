"""Experimental RTMO-s CPU ONNX adapter; body scores are not visibility/presence.

Official ONNX deployment: OpenMMLab MMPose projects/rtmo (Apache-2.0 code).
Local implementation of documented top-left letterbox and box NMS; no RTMLib
dependency, implicit download, facial output, interpolation or identity tracking.
"""

from dataclasses import replace
from time import perf_counter

import cv2
import numpy as np

from radar_edge.errors import EdgeError
from radar_edge.model import verify_model
from radar_edge.observations import ESSENTIAL, Landmark, Pose, point_usable

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
    def __init__(self, model_path, variant="rtmo-s", recovery="NONE"):
        if variant != "rtmo-s":
            raise EdgeError("INVALID_MODEL_VARIANT", "O adaptador RTMO exige rtmo-s.")
        self.model_path = model_path
        self.session = None
        self.previous_ms = -1
        if recovery not in {"NONE", "RTMO_ADAPTIVE_V1", "RTMO_ADAPTIVE_V2"}:
            raise ValueError("Invalid recovery method")
        self.recovery = recovery
        self.person_detections = ()
        self.perception_passes = ()
        self.person_proposal_score = None
        self.proposal = None

    def infer_image(self, image):
        height, width = image.shape[:2]
        ratio = min(640 / width, 640 / height)
        resized = cv2.resize(
            image, (int(width * ratio), int(height * ratio)), interpolation=cv2.INTER_LINEAR
        )
        padded = np.full((640, 640, 3), 114, dtype=np.uint8)
        padded[: resized.shape[0], : resized.shape[1]] = resized
        tensor = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32)
        outputs = self.session.run(["dets", "keypoints"], {"input": tensor})
        poses = decode_outputs(outputs, ratio, width, height)
        selected = select_detections(outputs[0][0])
        boxes = tuple(
            tuple(
                float(x)
                for x in [
                    *(outputs[0][0, i, :4] / ratio / [width, height, width, height]),
                    outputs[0][0, i, 4],
                ]
            )
            for i in selected
        )
        score = float(outputs[0][0, :, 4].max()) if outputs[0].shape[1] else None
        self.proposal = (
            outputs[0][0, int(np.argmax(outputs[0][0, :, 4])), :4] / ratio
            if outputs[0].shape[1] and score >= 0.3
            else None
        )
        return poses, boxes, score

    @staticmethod
    def valid_essential(poses):
        if len(poses) != 1:
            return 0
        return sum(
            p.index in ESSENTIAL
            and point_usable(p, 0.5, poses[0].qualitySource)
            and 0 <= p.x <= 1
            and 0 <= p.y <= 1
            for p in poses[0].landmarks
        )

    def proposal_crop(self, image, box):
        height, width = image.shape[:2]
        x1, y1, x2, y2 = box
        dx, dy = (x2 - x1) * 0.25, (y2 - y1) * 0.25
        x1, y1, x2, y2 = (
            max(0, int(x1 - dx)),
            max(0, int(y1 - dy)),
            min(width, int(x2 + dx)),
            min(height, int(y2 + dy)),
        )
        if x2 - x1 < 16 or y2 - y1 < 16:
            return (), (), None
        poses, boxes, score = self.infer_image(image[y1:y2, x1:x2])
        poses = tuple(
            Pose(
                tuple(
                    replace(p, x=(p.x * (x2 - x1) + x1) / width, y=(p.y * (y2 - y1) + y1) / height)
                    for p in pose.landmarks
                ),
                pose.qualitySource,
            )
            for pose in poses
        )
        boxes = tuple(
            (
                (b[0] * (x2 - x1) + x1) / width,
                (b[1] * (y2 - y1) + y1) / height,
                (b[2] * (x2 - x1) + x1) / width,
                (b[3] * (y2 - y1) + y1) / height,
                b[4],
            )
            for b in boxes
        )
        return poses, boxes, score

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
            poses, boxes, score = self.infer_image(frame.bgr)
            passes = ["ORIGINAL"]
            if (
                self.recovery == "RTMO_ADAPTIVE_V2"
                and len(poses) <= 1
                and self.valid_essential(poses) < 8
                and self.proposal is not None
            ):
                cropped, crop_boxes, crop_score = self.proposal_crop(frame.bgr, self.proposal)
                passes.append("PERSON_PROPOSAL_CROP")
                score = max(x for x in (score, crop_score) if x is not None)
                if (
                    (not poses and cropped)
                    or len(cropped) > 1
                    or self.valid_essential(cropped) > self.valid_essential(poses)
                ):
                    poses, boxes = cropped, crop_boxes
            if not poses and self.recovery != "NONE":
                rotated, rotated_boxes, rotated_score = self.infer_image(
                    cv2.rotate(frame.bgr, cv2.ROTATE_180)
                )
                passes.append("ROTATE_180")
                score = (
                    max(x for x in (score, rotated_score) if x is not None)
                    if score is not None or rotated_score is not None
                    else None
                )
                poses = tuple(
                    Pose(
                        tuple(
                            replace(p, x=(width - 1) / width - p.x, y=(height - 1) / height - p.y)
                            for p in pose.landmarks
                        ),
                        pose.qualitySource,
                    )
                    for pose in rotated
                )
                boxes = tuple(
                    (
                        (width - 1) / width - b[2],
                        (height - 1) / height - b[3],
                        (width - 1) / width - b[0],
                        (height - 1) / height - b[1],
                        b[4],
                    )
                    for b in rotated_boxes
                )
                if not poses:
                    x1, y1, x2, y2 = (
                        int(0.1 * width),
                        int(0.1 * height),
                        int(0.9 * width),
                        int(0.9 * height),
                    )
                    cropped, crop_boxes, crop_score = self.infer_image(frame.bgr[y1:y2, x1:x2])
                    passes.append("CENTER_80")
                    score = (
                        max(x for x in (score, crop_score) if x is not None)
                        if score is not None or crop_score is not None
                        else None
                    )
                    poses = tuple(
                        Pose(
                            tuple(
                                replace(
                                    p,
                                    x=(p.x * (x2 - x1) + x1) / width,
                                    y=(p.y * (y2 - y1) + y1) / height,
                                )
                                for p in pose.landmarks
                            ),
                            pose.qualitySource,
                        )
                        for pose in cropped
                    )
                    boxes = tuple(
                        (
                            (b[0] * (x2 - x1) + x1) / width,
                            (b[1] * (y2 - y1) + y1) / height,
                            (b[2] * (x2 - x1) + x1) / width,
                            (b[3] * (y2 - y1) + y1) / height,
                            b[4],
                        )
                        for b in crop_boxes
                    )
            self.person_detections = boxes
            self.perception_passes = tuple(passes)
            self.person_proposal_score = score
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
