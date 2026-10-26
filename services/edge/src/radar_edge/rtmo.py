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
    def __init__(
        self, model_path, variant="rtmo-s", recovery="NONE", runtime_profile="REFERENCE_4_SPIN"
    ):
        if variant != "rtmo-s":
            raise EdgeError("INVALID_MODEL_VARIANT", "O adaptador RTMO exige rtmo-s.")
        self.model_path = model_path
        self.session = None
        self.previous_ms = -1
        if recovery not in {"NONE", "RTMO_ADAPTIVE_V1", "RTMO_ADAPTIVE_V2", "RTMO_ADAPTIVE_V3"}:
            raise ValueError("Invalid recovery method")
        self.recovery = recovery
        self.person_detections = ()
        self.perception_passes = ()
        self.person_proposal_score = None
        self.proposal = None
        self.proposal_essential = 0
        self.perception_attempts = []
        if runtime_profile not in {"REFERENCE_4_SPIN", "CPU_2_SPIN", "CPU_4_SLEEP", "CPU_2_SLEEP"}:
            raise ValueError("Invalid RTMO CPU runtime profile")
        self.runtime_profile = runtime_profile

    def infer_image(self, image):
        started = perf_counter()
        height, width = image.shape[:2]
        ratio = min(640 / width, 640 / height)
        resized = cv2.resize(
            image, (int(width * ratio), int(height * ratio)), interpolation=cv2.INTER_LINEAR
        )
        padded = np.full((640, 640, 3), 114, dtype=np.uint8)
        padded[: resized.shape[0], : resized.shape[1]] = resized
        tensor = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32)
        prepared = perf_counter()
        outputs = self.session.run(["dets", "keypoints"], {"input": tensor})
        inferred = perf_counter()
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
        self.proposal_essential = 0
        if self.proposal is not None:
            native = outputs[1][0, int(np.argmax(outputs[0][0, :, 4]))]
            for source, target in COCO_TO_BODY.items():
                x, y, confidence = native[source]
                self.proposal_essential += bool(
                    target in ESSENTIAL
                    and confidence >= 0.5
                    and 0 <= x / ratio <= width
                    and 0 <= y / ratio <= height
                )
        self.perception_attempts.append(
            {
                "inputWidth": width,
                "inputHeight": height,
                "topPersonProposalScore": score,
                "acceptedPersonScores": [b[4] for b in boxes],
                "poseCount": len(poses),
                "usableEssentialCount": self.valid_essential(poses),
                "proposalUsableEssentialCount": self.proposal_essential,
                "inferenceMs": (perf_counter() - started) * 1000,
                "prepareMs": (prepared - started) * 1000,
                "sessionRunMs": (inferred - prepared) * 1000,
                "decodeMs": (perf_counter() - inferred) * 1000,
            }
        )
        return poses, boxes, score

    def quarter_turn(self, image, clockwise):
        """Infer fresh pixels and restore to the original image; never swap body labels."""
        height, width = image.shape[:2]
        rotation = cv2.ROTATE_90_CLOCKWISE if clockwise else cv2.ROTATE_90_COUNTERCLOCKWISE
        poses, boxes, score = self.infer_image(cv2.rotate(image, rotation))
        restore_started = perf_counter()

        def restore(x, y):
            return (y, (height - 1) / height - x) if clockwise else ((width - 1) / width - y, x)

        poses = tuple(
            Pose(
                tuple(
                    replace(p, x=restore(p.x, p.y)[0], y=restore(p.x, p.y)[1])
                    for p in pose.landmarks
                ),
                pose.qualitySource,
            )
            for pose in poses
        )
        restored_boxes = []
        for b in boxes:
            corners = [restore(b[x], b[y]) for x, y in ((0, 1), (0, 3), (2, 1), (2, 3))]
            restored_boxes.append(
                (
                    min(p[0] for p in corners),
                    min(p[1] for p in corners),
                    max(p[0] for p in corners),
                    max(p[1] for p in corners),
                    b[4],
                )
            )
        if self.perception_attempts:
            self.perception_attempts[-1]["restoreMs"] = (perf_counter() - restore_started) * 1000
        return poses, tuple(restored_boxes), score

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
            self.perception_attempts.append(
                {
                    "inputWidth": max(0, x2 - x1),
                    "inputHeight": max(0, y2 - y1),
                    "topPersonProposalScore": None,
                    "acceptedPersonScores": [],
                    "poseCount": 0,
                    "usableEssentialCount": 0,
                    "inferenceMs": 0.0,
                    "skippedReason": "CROP_TOO_SMALL",
                }
            )
            return (), (), None
        poses, boxes, score = self.infer_image(image[y1:y2, x1:x2])
        restore_started = perf_counter()
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
        if self.perception_attempts:
            self.perception_attempts[-1]["restoreMs"] = (perf_counter() - restore_started) * 1000
        return poses, boxes, score

    def __enter__(self):
        path = verify_model(self.model_path, "rtmo-s")
        try:
            import onnxruntime as ort

            options = ort.SessionOptions()
            options.intra_op_num_threads = 2 if "_2_" in self.runtime_profile else 4
            options.inter_op_num_threads = 1
            if self.runtime_profile.endswith("SLEEP"):
                options.add_session_config_entry("session.intra_op.allow_spinning", "0")
                options.add_session_config_entry("session.inter_op.allow_spinning", "0")
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
            self.perception_attempts = []
            height, width = frame.bgr.shape[:2]
            poses, boxes, score = self.infer_image(frame.bgr)
            original_proposal = self.proposal
            original_proposal_essential = self.proposal_essential
            passes = ["ORIGINAL"]
            if (
                self.recovery in {"RTMO_ADAPTIVE_V2", "RTMO_ADAPTIVE_V3"}
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
            if (
                not poses
                and self.recovery == "RTMO_ADAPTIVE_V3"
                and original_proposal is not None
                and original_proposal_essential == len(ESSENTIAL)
                and original_proposal[2] - original_proposal[0]
                > original_proposal[3] - original_proposal[1]
            ):
                # Bounded extra work only for a current horizontal proposal with all
                # eight real essential points. This only gates work, never accepts
                # a person/pose below the detector threshold or fabricates visibility.
                # Try both directions, with identical acceptance thresholds. V1/V2 unchanged.
                for clockwise, name in ((False, "ROTATE_270"), (True, "ROTATE_90")):
                    turned, turned_boxes, turned_score = self.quarter_turn(frame.bgr, clockwise)
                    passes.append(name)
                    score = max(x for x in (score, turned_score) if x is not None)
                    if len(turned) > 1 or self.valid_essential(turned) == len(ESSENTIAL):
                        poses, boxes = turned, turned_boxes
                        break
            if not poses and self.recovery != "NONE":
                rotated, rotated_boxes, rotated_score = self.infer_image(
                    cv2.rotate(frame.bgr, cv2.ROTATE_180)
                )
                passes.append("ROTATE_180")
                restore_started = perf_counter()
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
                if self.perception_attempts:
                    self.perception_attempts[-1]["restoreMs"] = (
                        perf_counter() - restore_started
                    ) * 1000
                if not poses:
                    x1, y1, x2, y2 = (
                        int(0.1 * width),
                        int(0.1 * height),
                        int(0.9 * width),
                        int(0.9 * height),
                    )
                    cropped, crop_boxes, crop_score = self.infer_image(frame.bgr[y1:y2, x1:x2])
                    passes.append("CENTER_80")
                    restore_started = perf_counter()
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
                    if self.perception_attempts:
                        self.perception_attempts[-1]["restoreMs"] = (
                            perf_counter() - restore_started
                        ) * 1000
            self.person_detections = boxes
            self.perception_passes = tuple(passes)
            for attempt, name in zip(self.perception_attempts, passes, strict=False):
                attempt["pass"] = name
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
