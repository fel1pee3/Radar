"""Experimental baseline constants; no inference, I/O or clock dependencies."""

import math
import re
from dataclasses import asdict, dataclass, fields


@dataclass(frozen=True)
class Policy:
    version: str = "floor-v0.1"
    qualitySource: str = "MEDIAPIPE"
    minKeypointScore: float = 0.5
    minLandmarkVisibility: float = 0.5
    minTorsoAngleDeg: float = 60.0
    maxBboxAspectRatio: float = 1.0
    floorHoldMs: int = 2000
    minValidPoseFraction: float = 0.8
    minValidObservations: int = 5
    maxObservationGapMs: int = 500
    rapidDescentWindowMs: int = 1000
    minHipDescentNormalized: float = 0.18
    rearmHoldMs: int = 3000
    frameTimeoutMs: int = 2000
    lowFpsThreshold: float = 2.0
    lowFpsHoldMs: int = 5000
    lowLightThreshold: float = 25.0
    lowLightHoldMs: int = 2000
    frozenHoldMs: int = 10000

    def __post_init__(self):
        if self.qualitySource not in {"MEDIAPIPE", "RTMO_KEYPOINT_SCORE"}:
            raise ValueError("Invalid pose quality source")
        if not isinstance(self.version, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._+-]{0,119}", self.version
        ):
            raise ValueError("Invalid policy version")
        for field in fields(self):
            if field.name in {"version", "qualitySource"}:
                continue
            value = getattr(self, field.name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError("Invalid policy parameter")
            if field.name.endswith("Ms") or field.name == "minValidObservations":
                if type(value) is not int or value > 120000:
                    raise ValueError("Invalid duration/count")
        if not 0 < self.minValidPoseFraction <= 1 or not 0 < self.minLandmarkVisibility <= 1:
            raise ValueError("Invalid fraction")
        if not 0 < self.minKeypointScore <= 1:
            raise ValueError("Invalid keypoint score")
        if not 0 < self.minHipDescentNormalized <= 1 or self.minTorsoAngleDeg > 90:
            raise ValueError("Invalid geometry threshold")
        if self.minValidObservations < 5 or self.maxObservationGapMs > self.floorHoldMs:
            raise ValueError("Invalid persistence window")

    def to_dict(self):
        value = asdict(self)
        if self.qualitySource == "MEDIAPIPE":
            # Preserve existing Full/Lite execution fingerprints and checkpoints.
            value.pop("qualitySource")
            value.pop("minKeypointScore")
        return value


DEFAULT_POLICY = Policy()


def configured_policy(overrides):
    policy = Policy(**overrides)
    score_version = policy.version.startswith("floor-rtmo-score-")
    if score_version != (policy.qualitySource == "RTMO_KEYPOINT_SCORE"):
        raise ValueError("RTMO score quality requires its explicit policy family")
    if policy.version == DEFAULT_POLICY.version and policy != DEFAULT_POLICY:
        raise ValueError("Parameter changes require another policy version")
    return policy
