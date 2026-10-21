"""Local body observations. No face landmarks, identities, classification or transport."""

import math
from dataclasses import asdict, dataclass
from typing import Literal

ESSENTIAL = {11, 12, 23, 24, 25, 26, 27, 28}


@dataclass(frozen=True)
class Landmark:
    index: int
    x: float | None
    y: float | None
    z: float | None
    visibility: float | None
    presence: float | None


@dataclass(frozen=True)
class Pose:
    landmarks: tuple[Landmark, ...]


@dataclass(frozen=True)
class Observation:
    schemaVersion: int
    runId: str
    cameraId: str
    mode: Literal["REPLAY"]
    frameIndex: int
    timestampMs: int
    timestampSource: str
    width: int
    height: int
    rotation: int
    poses: tuple[Pose, ...]
    poseCount: int
    inferenceState: str
    qualityReasons: tuple[str, ...]
    meanLuminance: float
    inferenceMs: float
    modelId: str
    calibrationId: str
    calibrationVersion: int

    def to_dict(self) -> dict:
        return asdict(self)


def finite_or_none(value) -> float | None:
    return float(value) if value is not None and math.isfinite(value) else None


def body_poses(result) -> tuple[Pose, ...]:
    return tuple(
        Pose(
            tuple(
                Landmark(
                    index,
                    *(
                        finite_or_none(getattr(point, name, None))
                        for name in ("x", "y", "z", "visibility", "presence")
                    ),
                )
                for index, point in enumerate(landmarks)
                if 11 <= index <= 32
            )
        )
        for landmarks in result.pose_landmarks
    )


def pose_quality(poses: tuple[Pose, ...], visibility: float) -> tuple[str, tuple[str, ...]]:
    if not poses:
        return "NO_POSE", ("NO_POSE",)
    if len(poses) > 1:
        return "MULTIPLE_POSES", ("MULTIPLE_POSES",)
    points = {point.index: point for point in poses[0].landmarks}
    reasons = set()
    for index in ESSENTIAL:
        point = points.get(index)
        if point is None or point.x is None or point.y is None:
            reasons.add("MISSING_LANDMARK")
            continue
        if not 0 <= point.x <= 1 or not 0 <= point.y <= 1:
            reasons.add("BODY_OUT_OF_FRAME")
        if (
            point.visibility is None
            or not visibility <= point.visibility <= 1
            or point.presence is None
            or not visibility <= point.presence <= 1
        ):
            reasons.add("LOW_LANDMARK_QUALITY")
    return ("LOW_CONFIDENCE", tuple(sorted(reasons))) if reasons else ("ONE_VALID_POSE", ())
