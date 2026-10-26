"""Signed, quality-aware posture classification; no image, identity or fitting on run."""

import hashlib
import math
from dataclasses import replace
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from radar_edge.config import StrictModel, private_path
from radar_edge.errors import EdgeError
from radar_edge.features import inside_polygon
from radar_edge.observations import ESSENTIAL, point_confidence, point_usable

DESCRIPTOR = "signed-body-quality-84-v1"
CLASSES = ("STANDING_OR_WALKING", "SEATED", "KNEELING_OR_CROUCHING", "LYING")
POINTS = tuple(sorted(ESSENTIAL))
EDGES = (
    (11, 12),
    (23, 24),
    (11, 23),
    (12, 24),
    (23, 25),
    (24, 26),
    (25, 27),
    (26, 28),
    (23, 27),
    (24, 28),
)
ANGLES = ((23, 25, 27), (24, 26, 28), (11, 23, 25), (12, 24, 26))
FEATURE_DIM = 84
RECOVERABLE = {
    "LOW_LANDMARK_QUALITY",
    "MISSING_ESSENTIAL_LANDMARK",
    "MISSING_LANDMARK",
    "BODY_CROPPED",
    "BODY_OUT_OF_FRAME",
}


def usable_body(pose, threshold=0.5):
    return {
        p.index: p
        for p in pose.landmarks
        if p.index in ESSENTIAL
        and point_usable(p, threshold, pose.qualitySource)
        and 0 <= p.x <= 1
        and 0 <= p.y <= 1
    }


def signed_descriptor(pose, width, height, threshold=0.5):
    """Preserve image orientation; missing coordinates have separate validity masks.

    Zero feature values are masked inputs, never invented landmarks or scores.
    Coordinates are converted to pixels before normalizing translation and size.
    """
    if pose.qualitySource != "RTMO_KEYPOINT_SCORE" or width <= 0 or height <= 0:
        return None
    original = {p.index: p for p in pose.landmarks}
    if len(original) != len(pose.landmarks):
        return None
    valid = usable_body(pose, threshold)
    if len(valid) < 4 or len({11, 12, 23, 24} & valid.keys()) < 3:
        return None
    pixels = {i: np.array([p.x * width, p.y * height]) for i, p in valid.items()}
    span = np.ptp(np.array(list(pixels.values())), axis=0)
    scale = float(np.linalg.norm(span))
    if scale < 1e-6:
        return None
    hip_center = {23, 24} <= pixels.keys()
    center = (pixels[23] + pixels[24]) / 2 if hip_center else np.mean(list(pixels.values()), axis=0)
    values = []
    for index in POINTS:
        point = original.get(index)
        score = point_confidence(point, pose.qualitySource) if point is not None else None
        relative = (pixels[index] - center) / scale if index in valid else (0.0, 0.0)
        values.extend(
            [
                *relative,
                score if score is not None else 0.0,
                float(point is not None),
                float(index in valid),
                float(score is not None),
            ]
        )
    for a, b in EDGES:
        available = a in valid and b in valid
        values.extend(
            [
                float(np.linalg.norm(pixels[a] - pixels[b]) / scale) if available else 0.0,
                float(available),
            ]
        )
    for a, b, c in ANGLES:
        available = all(i in valid for i in (a, b, c))
        cosine = 0.0
        if available:
            left, right = pixels[a] - pixels[b], pixels[c] - pixels[b]
            norm = np.linalg.norm(left) * np.linalg.norm(right)
            available = norm > 1e-6
            if available:
                cosine = float(np.dot(left, right) / norm)
        values.extend([cosine, float(available)])
    for group in [(11, 12, 23, 24), (23, 24, 27, 28)]:
        available = all(i in valid for i in group)
        direction = (0.0, 0.0)
        if available:
            a, b, c, d = group
            vector = (pixels[c] + pixels[d] - pixels[a] - pixels[b]) / 2
            norm = np.linalg.norm(vector)
            available = norm > 1e-6
            if available:
                direction = vector / norm
        values.extend([*direction, float(available)])
    values.extend([len(valid) / len(POINTS), float(hip_center)])
    vector = np.asarray(values, dtype=np.float64)
    return vector if vector.shape == (FEATURE_DIM,) and np.isfinite(vector).all() else None


class MulticlassArtifact(StrictModel):
    schemaVersion: Literal[2]
    descriptor: Literal["signed-body-quality-84-v1"]
    version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    poseModelSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    classes: tuple[str, ...]
    mean: list[float]
    std: list[float]
    weights1: list[list[float]]
    bias1: list[float]
    weights2: list[list[float]]
    bias2: list[float]
    qualityThreshold: float = Field(default=0.5, gt=0, le=1)
    decisionThreshold: float = Field(default=0.65, ge=0.5, lt=1)
    marginThreshold: float = Field(default=0.15, ge=0, lt=1)
    contextMode: Literal["OPERATOR_CONFIRMED_FIXED_CAMERA"]
    training: dict

    @model_validator(mode="after")
    def finite_dimensions(self):
        if tuple(self.classes) != CLASSES:
            raise ValueError("Posture class order mismatch")
        shapes = [
            (self.mean, (FEATURE_DIM,)),
            (self.std, (FEATURE_DIM,)),
            (self.weights1, (FEATURE_DIM, 32)),
            (self.bias1, (32,)),
            (self.weights2, (32, len(CLASSES))),
            (self.bias2, (len(CLASSES),)),
        ]
        for values, shape in shapes:
            array = np.asarray(values, dtype=float)
            if array.shape != shape or not np.isfinite(array).all() or np.max(np.abs(array)) > 1e6:
                raise ValueError("Posture artifact numeric shape/value mismatch")
        if min(self.std) < 0.05:
            raise ValueError("Invalid standardization")
        return self


class MulticlassClassifier:
    def __init__(self, settings, calibration, model_spec, policy):
        from radar_edge.posture import calibration_digest

        try:
            path = private_path(settings.artifactPath)
            if path.stat().st_size > 256 * 1024:
                raise ValueError()
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != settings.artifactSha256:
                raise ValueError()
            self.artifact = MulticlassArtifact.model_validate_json(data)
        except (OSError, ValueError, TypeError):
            raise EdgeError(
                "POSTURE_ARTIFACT_INVALID", "Confira o artefato multiclasse e seu SHA-256."
            ) from None
        if (
            settings.method != "MULTICLASS_BODY_V3"
            or not settings.operatorConfirmed
            or settings.calibrationSha256 != calibration_digest(calibration)
            or self.artifact.poseModelSha256 != model_spec.sha256
            or not policy.version.startswith("floor-rtmo-score-posture-multiclass-v3")
            or policy.qualitySource != "RTMO_KEYPOINT_SCORE"
            or policy.temporalMode != "EVIDENCE_V2"
            or policy.minKeypointScore != self.artifact.qualityThreshold
        ):
            raise EdgeError(
                "POSTURE_CONTEXT_UNSUPPORTED",
                "Modelo, política ou contexto não corresponde ao candidato multiclasse.",
            )
        self.settings = settings
        self.geometry = calibration["geometry"]
        self._floor = calibration["floorPolygon"]
        self.arrays = {
            key: np.asarray(getattr(self.artifact, key))
            for key in ["mean", "std", "weights1", "bias1", "weights2", "bias2"]
        }

    def scores(self, vector):
        a = self.arrays
        x = (vector - a["mean"]) / a["std"]
        logits = np.tanh(x @ a["weights1"] + a["bias1"]) @ a["weights2"] + a["bias2"]
        exp = np.exp(logits - logits.max())
        return exp / exp.sum()

    def classify(self, observation, features):
        f, o = features, observation
        common = {"postureModel": self.artifact.version, "postureMethod": self.settings.method}
        if len(o.poses) != 1 or set(f.reasons) - RECOVERABLE:
            return replace(
                f,
                eligible=False,
                candidate=False,
                posture="NO_PERSON_DETECTED"
                if not o.poses and not o.personDetections
                else "PERSON_POSE_INSUFFICIENT",
                **common,
            )
        if (o.width, o.height, o.rotation) != (
            self.geometry["width"],
            self.geometry["height"],
            self.geometry["rotation"],
        ):
            return replace(
                f,
                eligible=False,
                candidate=False,
                posture="UNKNOWN",
                reasons=("POSTURE_GEOMETRY_UNSUPPORTED",),
                **common,
            )
        vector = signed_descriptor(o.poses[0], o.width, o.height, self.artifact.qualityThreshold)
        if vector is None:
            return replace(
                f,
                eligible=False,
                candidate=False,
                posture="PERSON_POSE_INSUFFICIENT",
                reasons=("POSTURE_DESCRIPTOR_INSUFFICIENT",),
                **common,
            )
        probabilities = self.scores(vector)
        order = np.argsort(probabilities)
        winner, runner = int(order[-1]), int(order[-2])
        known = (
            probabilities[winner] >= self.artifact.decisionThreshold
            and probabilities[winner] - probabilities[runner] >= self.artifact.marginThreshold
        )
        posture = CLASSES[winner] if known else "UNKNOWN"
        valid = usable_body(o.poses[0], self.artifact.qualityThreshold)
        original_reasons = tuple(sorted(set(f.reasons) & RECOVERABLE))
        hip_x = (valid[23].x + valid[24].x) / 2 if {23, 24} <= valid.keys() else None
        hip_y = (valid[23].y + valid[24].y) / 2 if {23, 24} <= valid.keys() else None
        torso_angle, aspect = f.torsoAngleDeg, f.bboxAspectRatio
        body_scale = None
        shoulder_x = shoulder_y = None
        if ESSENTIAL <= valid.keys():
            xs = [p.x * o.width for p in valid.values()]
            ys = [p.y * o.height for p in valid.values()]
            shoulder_x = (valid[11].x + valid[12].x) / 2
            shoulder_y = (valid[11].y + valid[12].y) / 2
            dx, dy = (hip_x - shoulder_x) * o.width, (hip_y - shoulder_y) * o.height
            if max(xs) > min(xs) and max(ys) > min(ys) and math.hypot(dx, dy) > 1e-6:
                torso_angle = math.degrees(math.atan2(abs(dx), abs(dy)))
                aspect = (max(ys) - min(ys)) / (max(xs) - min(xs))
                body_scale = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / o.height
        floor = inside_polygon(hip_x, hip_y, self.calibration_floor) if hip_x is not None else None
        excluded = hip_x is not None and any(
            inside_polygon(hip_x, hip_y, p)
            for p in [
                *self.settings.excludedRegions,
                *(r.polygon for r in self.settings.supportRegions),
            ]
        )
        reasons = []
        if not known:
            reasons.append("POSTURE_UNCERTAIN")
        if posture == "LYING":
            if not ESSENTIAL <= valid.keys() or torso_angle is None or aspect is None:
                reasons.append("FLOOR_BODY_EVIDENCE_INCOMPLETE")
            if excluded:
                reasons.append("CONTEXT_EXCLUDED_REGION")
            elif floor is not True:
                reasons.append("LYING_OUTSIDE_OBSERVED_REGION")
        return replace(
            f,
            eligible=not reasons,
            candidate=posture == "LYING" and not reasons,
            reasons=tuple(reasons),
            posture=posture,
            postureScore=float(probabilities[3]),
            postureAttributes=tuple(vector),
            postureClassScores=tuple(float(x) for x in probabilities),
            postureQualityReasons=original_reasons,
            postureEvidenceOrigin="RTMO_FULL_BODY"
            if ESSENTIAL <= valid.keys()
            else "RTMO_PARTIAL_BODY",
            regionState="EXCLUDED" if excluded else "INSIDE" if floor else "OUTSIDE",
            hipInFloorZone=floor,
            hipY=hip_y,
            hipX=hip_x,
            bodyScale=body_scale,
            shoulderX=shoulder_x,
            shoulderY=shoulder_y,
            torsoAngleDeg=torso_angle,
            bboxAspectRatio=aspect,
            **common,
        )

    @property
    def calibration_floor(self):
        return self._floor
