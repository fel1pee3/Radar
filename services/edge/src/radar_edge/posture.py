"""Small opt-in posture model. No image inference, pickle, network or training on run."""

import hashlib
import json
import math
from dataclasses import replace
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from radar_edge.config import StrictModel, private_path
from radar_edge.errors import EdgeError
from radar_edge.features import inside_polygon
from radar_edge.observations import ESSENTIAL
from radar_edge.outbox import encode

DESCRIPTOR = "symmetric-body-context-35-v1"
BODY_DESCRIPTOR = "symmetric-body-shape-29-v1"
OTHER_POSTURES = {"STANDING_OR_WALKING", "SEATED", "KNEELING_OR_CROUCHING", "OTHER_POSTURE"}


def calibration_digest(calibration):
    return hashlib.sha256(encode(calibration).encode()).hexdigest()


def body_descriptor(o, descriptor=DESCRIPTOR):
    """Pixel-correct geometry, optionally retaining the first model's image context."""
    points = {
        p.index: np.array([p.x * o.width, p.y * o.height])
        for p in o.poses[0].landmarks
        if p.index in ESSENTIAL
    }
    shoulders = (points[11] + points[12]) / 2
    hip = (points[23] + points[24]) / 2
    lengths = [
        np.linalg.norm(shoulders - hip),
        np.linalg.norm(points[11] - points[12]),
        np.linalg.norm(points[23] - points[24]),
    ]
    for a, b in [(23, 25), (24, 26), (25, 27), (26, 28), (23, 27), (24, 28)]:
        lengths.append(np.linalg.norm(points[a] - points[b]))
    scale = lengths[0] + sum(lengths[3:7]) / 2
    if scale <= 1e-6:
        return None
    values = [abs(v) for index in sorted(ESSENTIAL) for v in (points[index] - hip) / scale]
    values += [v / scale for v in lengths]
    for a, b, c in [(23, 25, 27), (24, 26, 28), (11, 23, 25), (12, 24, 26)]:
        left, right = points[a] - points[b], points[c] - points[b]
        denominator = np.linalg.norm(left) * np.linalg.norm(right)
        values.append(float(np.dot(left, right) / denominator) if denominator > 1e-6 else 0.0)
    if descriptor == DESCRIPTOR:
        values += [
            hip[0] / o.width,
            hip[1] / o.height,
            shoulders[1] / o.height,
            (points[25][1] + points[26][1]) / 2 / o.height,
            (points[27][1] + points[28][1]) / 2 / o.height,
            scale / o.height,
        ]
    elif descriptor != BODY_DESCRIPTOR:
        raise ValueError("Unknown posture descriptor")
    vector = np.asarray(values, dtype=float)
    return vector if np.isfinite(vector).all() else None


class LinearArtifact(StrictModel):
    schemaVersion: Literal[1]
    descriptor: Literal["symmetric-body-context-35-v1", "symmetric-body-shape-29-v1"]
    version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    poseModelSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    installationIds: list[str] = Field(min_length=1, max_length=100)
    mean: list[float] = Field(min_length=29, max_length=35)
    std: list[float] = Field(min_length=29, max_length=35)
    coefficients: list[float] = Field(min_length=30, max_length=36)
    lyingThreshold: float = Field(default=0.8, ge=0.5, lt=1)
    otherThreshold: float = Field(default=0.2, gt=0, lt=0.5)
    qualityThreshold: float = Field(default=0.5, gt=0, le=1)
    training: dict
    contextMode: Literal["TRAINED_INSTALLATION", "OPERATOR_CONFIRMED_FIXED_CAMERA"] = (
        "TRAINED_INSTALLATION"
    )

    @model_validator(mode="after")
    def descriptor_shape_and_scope(self):
        body = self.descriptor == BODY_DESCRIPTOR
        count = 29 if body else 35
        if (len(self.mean), len(self.std), len(self.coefficients)) != (count, count, count + 1):
            raise ValueError("Descriptor/coefficient dimension mismatch")
        if body != (self.contextMode == "OPERATOR_CONFIRMED_FIXED_CAMERA"):
            raise ValueError("Descriptor and context semantics disagree")
        return self


def other_posture(o, vector):
    """Conservative descriptive subtypes; not independently validated action labels.

    These rules never turn a low lying score into positive floor evidence.
    A projection compatible with both sitting and crouching stays OTHER_POSTURE.
    """
    knee_angles = [math.degrees(math.acos(float(np.clip(v, -1, 1)))) for v in vector[25:27]]
    points = {p.index: p for p in o.poses[0].landmarks}
    hip_y, shoulder_y, knee_y, ankle_y = (
        vector[30:34]
        if len(vector) == 35
        else [(points[a].y + points[b].y) / 2 for a, b in [(23, 24), (11, 12), (25, 26), (27, 28)]]
    )
    if (
        min(knee_angles) >= 155
        and shoulder_y < hip_y < knee_y < ankle_y
        and hip_y - shoulder_y > 0.08
        and max(abs(points[h].x - points[a].x) for h, a in [(23, 27), (24, 28)]) < 0.12
    ):
        return "STANDING_OR_WALKING"
    if max(knee_angles) <= 60 and shoulder_y < hip_y and ankle_y >= knee_y:
        return "KNEELING_OR_CROUCHING"
    # Sitting is not separable from a deep squat by pose alone without support context.
    return "OTHER_POSTURE"


class PostureClassifier:
    def __init__(self, settings, calibration, model_spec, policy):
        self.settings = settings
        try:
            path = private_path(settings.artifactPath)
            if path.stat().st_size > 256 * 1024:
                raise ValueError()
            data = path.read_bytes()
            if (
                len(data) > 256 * 1024
                or hashlib.sha256(data).hexdigest() != settings.artifactSha256
            ):
                raise ValueError()
            self.artifact = LinearArtifact.model_validate(json.loads(data))
            if min(self.artifact.std) < 0.05:
                raise ValueError()
        except (OSError, ValueError, TypeError):
            raise EdgeError(
                "POSTURE_ARTIFACT_INVALID", "Confira o classificador privado e seu SHA-256."
            ) from None
        if (
            self.artifact.poseModelSha256 != model_spec.sha256
            or not settings.operatorConfirmed
            or (
                self.artifact.contextMode == "TRAINED_INSTALLATION"
                and settings.installationId not in self.artifact.installationIds
            )
            or (self.artifact.descriptor == BODY_DESCRIPTOR)
            != (settings.method == "LINEAR_BODY_V2")
            or (self.artifact.descriptor == BODY_DESCRIPTOR)
            != policy.version.startswith("floor-rtmo-score-posture-body-v2")
            or settings.calibrationSha256 != calibration_digest(calibration)
            or policy.qualitySource != "RTMO_KEYPOINT_SCORE"
            or policy.minKeypointScore != self.artifact.qualityThreshold
            or policy.temporalMode != "EVIDENCE_V2"
        ):
            raise EdgeError(
                "POSTURE_CONTEXT_UNSUPPORTED",
                "Instalação, calibração, qualidade ou modelo não corresponde ao candidato.",
            )
        self.geometry = calibration["geometry"]
        self.mean = np.array(self.artifact.mean)
        self.std = np.array(self.artifact.std)
        self.coefficients = np.array(self.artifact.coefficients)

    def classify(self, o, f):
        if not f.eligible:
            return replace(
                f,
                posture="NO_PERSON_DETECTED" if not o.poses else "PERSON_POSE_INSUFFICIENT",
                postureModel=self.artifact.version,
                postureMethod=self.settings.method,
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
                postureModel=self.artifact.version,
                postureMethod=self.settings.method,
            )
        vector = body_descriptor(o, self.artifact.descriptor)
        if vector is None:
            return replace(
                f,
                eligible=False,
                candidate=False,
                posture="UNKNOWN",
                reasons=("POSTURE_DESCRIPTOR_INVALID",),
                postureModel=self.artifact.version,
                postureMethod=self.settings.method,
            )
        z = np.append((vector - self.mean) / self.std, 1) @ self.coefficients
        score = float(1 / (1 + np.exp(-np.clip(z, -40, 40))))
        points = {p.index: p for p in o.poses[0].landmarks}
        hip = [(getattr(points[23], k) + getattr(points[24], k)) / 2 for k in ("x", "y")]
        excluded = any(inside_polygon(*hip, region) for region in self.settings.excludedRegions)
        supports = [
            region.kind
            for region in self.settings.supportRegions
            if inside_polygon(*hip, region.polygon)
        ]
        excluded = excluded or bool(supports)
        region = "EXCLUDED" if excluded else "INSIDE" if f.hipInFloorZone else "OUTSIDE"
        known = score >= self.artifact.lyingThreshold or score <= self.artifact.otherThreshold
        lying = score >= self.artifact.lyingThreshold
        posture = "LYING" if lying else other_posture(o, vector) if known else "UNKNOWN"
        if posture == "OTHER_POSTURE" and "CHAIR" in supports:
            knees = [math.degrees(math.acos(float(np.clip(v, -1, 1)))) for v in vector[25:27]]
            if all(65 <= angle <= 125 for angle in knees) and (
                points[11].y + points[12].y < points[23].y + points[24].y
            ):
                posture = "SEATED"
        reasons = []
        if not known:
            reasons.append("POSTURE_UNCERTAIN")
        # V2 can use a recognized other posture as negative evidence on a support.
        # Keep the frozen V1 context semantics for its existing policy/configs.
        if excluded and (self.settings.method != "LINEAR_BODY_V2" or lying or not known):
            reasons.append("CONTEXT_EXCLUDED_REGION")
        elif lying and not f.hipInFloorZone:
            reasons.append("LYING_OUTSIDE_OBSERVED_REGION")
        return replace(
            f,
            eligible=not reasons,
            candidate=lying and not reasons,
            reasons=tuple(reasons),
            posture=posture,
            postureScore=score,
            postureModel=self.artifact.version,
            postureMethod=self.settings.method,
            postureAttributes=tuple(vector),
            regionState=region,
        )


def create_posture_classifier(settings, calibration, model_spec, policy):
    if settings.method in {"MULTICLASS_BODY_V3", "MULTICLASS_CONTEXT_V4"}:
        from radar_edge.posture_multiclass import MulticlassClassifier

        return MulticlassClassifier(settings, calibration, model_spec, policy)
    return PostureClassifier(settings, calibration, model_spec, policy)


def check_posture(config):
    """Verify local model/context before a founder elects to open any source."""
    from radar_edge.calibration import load_calibration
    from radar_edge.model import get_model_spec, verify_model
    from radar_edge.policy import configured_policy

    result = {
        "status": "ok",
        "command": "posture-check",
        "method": config.posture.method,
        "sourceKind": config.source.kind,
        "sourceOpened": False,
        "databaseOpened": False,
        "functionalMvpApproved": False,
    }
    if config.posture.method != "BASELINE":
        verify_model(config.model.path, config.model.variant)
        classifier = create_posture_classifier(
            config.posture,
            load_calibration(config.calibrationPath),
            get_model_spec(config.model.variant),
            configured_policy(config.events.policy),
        )
        result.update(
            artifactVersion=classifier.artifact.version,
            descriptor=classifier.artifact.descriptor,
            contextMode=classifier.artifact.contextMode,
            artifactSha256=config.posture.artifactSha256,
            installationId=config.posture.installationId,
            calibrationSha256=config.posture.calibrationSha256,
            poseModelFileVerified=True,
            eventsEnabled=config.events.enabled,
            scoreMeaning="UNCALIBRATED_CLASSIFIER_SCORE_NOT_VISIBILITY_OR_MEDICAL_PROBABILITY",
        )
    return result
