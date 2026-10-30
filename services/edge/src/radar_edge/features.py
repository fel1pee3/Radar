"""Pixel-correct geometry and media-time quality gates. No OpenCV or network."""

import math
from collections import deque
from dataclasses import dataclass, replace

from radar_edge.observations import ESSENTIAL, Observation, point_usable
from radar_edge.policy import DEFAULT_POLICY, Policy


def inside_polygon(x, y, polygon):
    inside = False
    for a, b in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        cross = (x - a[0]) * (b[1] - a[1]) - (y - a[1]) * (b[0] - a[0])
        if abs(cross) < 1e-12 and min(a[0], b[0]) <= x <= max(a[0], b[0]):
            if min(a[1], b[1]) <= y <= max(a[1], b[1]):
                return True
        if (a[1] > y) != (b[1] > y):
            if x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
                inside = not inside
    return inside


@dataclass(frozen=True)
class Features:
    timestampMs: int
    context: tuple
    eligible: bool
    reasons: tuple[str, ...]
    candidate: bool = False
    torsoAngleDeg: float | None = None
    bboxAspectRatio: float | None = None
    hipInFloorZone: bool | None = None
    hipY: float | None = None
    posture: str | None = None
    postureScore: float | None = None
    postureModel: str | None = None
    postureMethod: str | None = None
    postureAttributes: tuple[float, ...] = ()
    regionState: str | None = None
    postureClassScores: tuple[float, ...] = ()
    postureQualityReasons: tuple[str, ...] = ()
    postureEvidenceOrigin: str | None = None
    bodyEvidenceSufficient: bool | None = None
    floorContextCompatible: bool | None = None
    contextEvidenceIndices: tuple[int, ...] = ()
    contextSupportMechanism: str | None = None
    postureSubtypeUncertain: bool = False
    hipX: float | None = None
    bodyScale: float | None = None
    shoulderX: float | None = None
    shoulderY: float | None = None
    observedUprightTorso: bool | None = None


def extract_features(o: Observation, polygon, policy: Policy = DEFAULT_POLICY) -> Features:
    context = (
        o.cameraId,
        o.calibrationId,
        o.calibrationVersion,
        o.modelId,
        o.width,
        o.height,
        o.rotation,
    )
    reasons = set(o.qualityReasons) - {"DARK_FRAME"}
    if o.poseCount != len(o.poses):
        reasons.add("POSE_COUNT_MISMATCH")
    if len(o.poses) != 1:
        reasons.add("MULTIPLE_POSES" if len(o.poses) > 1 else "NO_POSE")
    points = {}
    if len(o.poses) == 1:
        if o.poses[0].qualitySource != policy.qualitySource:
            reasons.add("QUALITY_POLICY_MISMATCH")
        if len({p.index for p in o.poses[0].landmarks}) != len(o.poses[0].landmarks):
            reasons.add("DUPLICATE_LANDMARK")
        for p in o.poses[0].landmarks:
            threshold = (
                policy.minKeypointScore
                if policy.qualitySource == "RTMO_KEYPOINT_SCORE"
                else policy.minLandmarkVisibility
            )
            valid = point_usable(p, threshold, o.poses[0].qualitySource)
            if not valid:
                if p.index in ESSENTIAL:
                    reasons.add("LOW_LANDMARK_QUALITY")
                continue
            if not 0 <= p.x <= 1 or not 0 <= p.y <= 1:
                reasons.add("BODY_CROPPED")
            if 11 <= p.index <= 32:
                points[p.index] = p
    if not ESSENTIAL <= points.keys():
        reasons.add("MISSING_ESSENTIAL_LANDMARK")
    if o.width <= 0 or o.height <= 0:
        reasons.add("INVALID_DIMENSIONS")
    if reasons:
        return Features(o.timestampMs, context, False, tuple(sorted(reasons)))
    xs = [p.x * o.width for p in points.values()]
    ys = [p.y * o.height for p in points.values()]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    sx, sy = ((getattr(points[11], k) + getattr(points[12], k)) / 2 for k in ("x", "y"))
    hx, hy = ((getattr(points[23], k) + getattr(points[24], k)) / 2 for k in ("x", "y"))
    dx, dy = (hx - sx) * o.width, (hy - sy) * o.height
    if w <= 1e-6 or h <= 1e-6 or math.hypot(dx, dy) <= 1e-6:
        return Features(o.timestampMs, context, False, ("DEGENERATE_BODY_GEOMETRY",))
    angle = math.degrees(math.atan2(abs(dx), abs(dy)))
    aspect = h / w
    floor = inside_polygon(hx, hy, polygon)
    candidate = floor and angle >= policy.minTorsoAngleDeg and aspect <= policy.maxBboxAspectRatio
    return Features(o.timestampMs, context, True, (), candidate, angle, aspect, floor, hy)


class QualityGate:
    """Conservative intervals; flags use media duration, never CPU throughput."""

    def __init__(self, policy=DEFAULT_POLICY):
        self.policy = policy
        self.previous = None
        self.dark_start = None
        self.same_start = None
        self.last_digest = None
        self.times = deque()

    def apply(self, observation, features):
        t, p = observation.timestampMs, self.policy
        reasons = set(features.reasons)
        if self.previous is not None and t - self.previous > p.frameTimeoutMs:
            reasons.add("FRAME_TIMEOUT")
        self.dark_start = (
            (t if self.dark_start is None else self.dark_start)
            if (observation.meanLuminance < p.lowLightThreshold)
            else None
        )
        if self.dark_start is not None and t - self.dark_start >= p.lowLightHoldMs:
            reasons.add("LOW_LIGHT")
        digest = observation.frameFingerprint
        if not digest or digest != self.last_digest:
            self.same_start = t
        frozen_duration = observation.identicalFrameDurationMs
        if frozen_duration is None:
            frozen_duration = t - self.same_start
        if digest and frozen_duration >= p.frozenHoldMs:
            reasons.add("POSSIBLE_FROZEN")
        self.last_digest = digest
        self.times.append(t)
        while len(self.times) > 1 and self.times[1] <= t - p.lowFpsHoldMs:
            self.times.popleft()
        span = t - self.times[0]
        if span >= p.lowFpsHoldMs and (len(self.times) - 1) * 1000 / span < p.lowFpsThreshold:
            reasons.add("LOW_FPS")
        self.previous = t
        return replace(
            features,
            eligible=features.eligible and not reasons,
            candidate=features.candidate and not reasons,
            reasons=tuple(sorted(reasons)),
        )
