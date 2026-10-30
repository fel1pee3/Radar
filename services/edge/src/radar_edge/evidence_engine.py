"""Versioned posture evidence with bounded uncertainty and explicit transition support."""

import math
from collections import deque

from radar_edge.engine import Emission, TemporalEngine
from radar_edge.posture import OTHER_POSTURES


class EvidenceEngine(TemporalEngine):
    def __init__(self, policy, active=False):
        super().__init__(policy, active)
        self.negative_ms = 0
        self.motion_at = None
        self.motion_history = deque()
        self.motion_v3_history = deque()

    def clear_suspicion(self):
        super().clear_suspicion()
        self.negative_ms = 0
        self.motion_at = None

    def observed_transition(self, current):
        """Image motion AND posture change, never a physical fall/intent measurement."""
        p = self.policy
        recent = [
            f
            for f in self.history
            if f.eligible and 0 < current.timestampMs - f.timestampMs <= p.rapidDescentWindowMs
        ]
        supported = [f for f in recent if f.posture in {"STANDING_OR_WALKING", "SEATED"}]
        if (
            len(supported) < 2
            or supported[-1].timestampMs - supported[0].timestampMs < p.transitionUprightHoldMs
        ):
            return False
        old = supported[0]
        if any(
            getattr(f, name) is None
            for f in (old, current)
            for name in ("hipX", "hipY", "bodyScale", "torsoAngleDeg", "shoulderX", "shoulderY")
        ):
            return False
        if old.bodyScale <= 0 or current.bodyScale <= 0:
            return False
        # Frame geometry is constant within an engine context: width,height at [-3:-1].
        aspect = current.context[-3] / current.context[-2]
        displacement = math.hypot((current.hipX - old.hipX) * aspect, current.hipY - old.hipY)
        displacement = max(
            displacement,
            math.hypot(
                (current.shoulderX - old.shoulderX) * aspect, current.shoulderY - old.shoulderY
            ),
        )
        displacement /= max(old.bodyScale, current.bodyScale)
        rotation = abs(current.torsoAngleDeg - old.torsoAngleDeg)
        return (
            rotation >= p.transitionAngleChangeDeg and displacement >= p.transitionBodyDisplacement
        )

    def update_motion_v2(self, current):
        """Support dwell precedes the motion window; no pose is synthesized in gaps.

        Continue examining motion during the first second of floor suspicion.
        A missing/unknown observation contributes no displacement or support time.
        A gap >500 ms between real usable body observations destroys the history.
        """
        p, t = self.policy, current.timestampMs
        if self.motion_at is not None and t - self.motion_at > p.rapidDescentWindowMs:
            self.motion_at = None
        if self.motion_history and t - self.motion_history[-1].timestampMs > p.maxObservationGapMs:
            self.motion_history.clear()
            self.motion_at = None
        while self.motion_history and t - self.motion_history[0].timestampMs > (
            p.rapidDescentWindowMs + p.transitionUprightHoldMs
        ):
            self.motion_history.popleft()
        usable = all(
            getattr(current, name) is not None
            for name in ("hipX", "hipY", "shoulderX", "shoulderY", "torsoAngleDeg", "bodyScale")
        )
        blocked = set(current.reasons) - {
            "POSTURE_UNCERTAIN",
            "FLOOR_CONTEXT_UNKNOWN",
            "CONTEXT_EXCLUDED_REGION",
            "LYING_OUTSIDE_OBSERVED_REGION",
        }
        if not usable or blocked or current.bodyScale <= 0:
            return
        supported = [
            x
            for x in self.motion_history
            if x.posture in {"STANDING_OR_WALKING", "SEATED"}
            and x.torsoAngleDeg <= 90 - p.transitionAngleChangeDeg
        ]
        search = self.start is None or t - self.start <= p.rapidDescentWindowMs
        if search:
            for old in reversed(supported):
                if not 0 < t - old.timestampMs <= p.rapidDescentWindowMs:
                    continue
                dwell = [
                    x
                    for x in supported
                    if 0 <= old.timestampMs - x.timestampMs <= p.transitionUprightHoldMs
                ]
                if (
                    len(dwell) < 2
                    or old.timestampMs - dwell[0].timestampMs < p.transitionUprightHoldMs
                ):
                    continue
                aspect = current.context[-3] / current.context[-2]
                displacement = max(
                    math.hypot((current.hipX - old.hipX) * aspect, current.hipY - old.hipY),
                    math.hypot(
                        (current.shoulderX - old.shoulderX) * aspect,
                        current.shoulderY - old.shoulderY,
                    ),
                ) / max(old.bodyScale, current.bodyScale)
                rotation = abs(current.torsoAngleDeg - old.torsoAngleDeg)
                if (
                    rotation >= p.transitionAngleChangeDeg
                    and displacement >= p.transitionBodyDisplacement
                ):
                    self.motion_at = t
                    break
        self.motion_history.append(current)

    def update_motion_v3(self, current):
        """Use observed torso orientation independently of the posture subtype.

        Missing perception supplies neither position nor upright dwell. A marker
        breaks new support runs. Previously completed real support may remain
        only within the existing motion window and <=500 ms between real body
        observations. Current endpoints are always real; capture failures reset.
        """
        p, t = self.policy, current.timestampMs
        if self.motion_at is not None and t - self.motion_at > p.rapidDescentWindowMs:
            self.motion_at = None
        allowed = {
            "POSTURE_UNCERTAIN",
            "FLOOR_CONTEXT_UNKNOWN",
            "CONTEXT_EXCLUDED_REGION",
            "LYING_OUTSIDE_OBSERVED_REGION",
        }
        perception_gaps = {
            "NO_POSE",
            "MISSING_ESSENTIAL_LANDMARK",
            "LOW_LANDMARK_QUALITY",
            "POSTURE_DESCRIPTOR_INSUFFICIENT",
            "FLOOR_BODY_EVIDENCE_INCOMPLETE",
            "BODY_CROPPED",
            "BODY_OUT_OF_FRAME",
        }
        blocked = set(current.reasons) - allowed
        history = self.motion_v3_history
        if blocked - perception_gaps:
            history.clear()
            self.motion_at = None
            return
        while history and t - history[0][0] > (p.rapidDescentWindowMs + p.transitionUprightHoldMs):
            history.popleft()
        last_real = next((f for _, f in reversed(history) if f is not None), None)
        if last_real is not None and t - last_real.timestampMs > p.maxObservationGapMs:
            history.clear()
            self.motion_at = None
            last_real = None
        geometry = tuple(
            getattr(current, name)
            for name in ("hipX", "hipY", "shoulderX", "shoulderY", "torsoAngleDeg", "bodyScale")
        )
        usable = (
            current.observedUprightTorso is not None
            and all(value is not None and math.isfinite(value) for value in geometry)
            and current.bodyScale > 0
            and not blocked
        )
        if not usable:
            # None is a missing-measurement marker, never a substitute pose.
            if last_real is not None:
                history.append((t, None))
            return
        search = self.start is None or t - self.start <= p.rapidDescentWindowMs
        run_start = None
        if search:
            for _, old in history:
                upright = (
                    old is not None
                    and old.observedUprightTorso is True
                    and (
                        old.posture in {"STANDING_OR_WALKING", "SEATED", "UNKNOWN"}
                        or (old.posture == "OTHER_POSTURE" and old.postureSubtypeUncertain)
                    )
                    and old.torsoAngleDeg <= 90 - p.transitionAngleChangeDeg
                    and old.shoulderY < old.hipY
                )
                if not upright:
                    run_start = None
                    continue
                if run_start is None:
                    run_start = old.timestampMs
                if (
                    old.timestampMs - run_start < p.transitionUprightHoldMs
                    or not 0 < t - old.timestampMs <= p.rapidDescentWindowMs
                ):
                    continue
                aspect = current.context[-3] / current.context[-2]
                displacement = max(
                    math.hypot((current.hipX - old.hipX) * aspect, current.hipY - old.hipY),
                    math.hypot(
                        (current.shoulderX - old.shoulderX) * aspect,
                        current.shoulderY - old.shoulderY,
                    ),
                ) / max(old.bodyScale, current.bodyScale)
                rotation = abs(current.torsoAngleDeg - old.torsoAngleDeg)
                if (
                    rotation >= p.transitionAngleChangeDeg
                    and displacement >= p.transitionBodyDisplacement
                ):
                    self.motion_at = t
                    break
        history.append((t, current))

    def step(self, f):
        self.closed = False
        p, t = self.policy, f.timestampMs
        if self.context is not None and f.context != self.context:
            raise ValueError("ENGINE_CONTEXT_CHANGED")
        if self.last is not None and t <= self.last.timestampMs:
            raise ValueError("NON_MONOTONIC_OBSERVATION")
        self.context = f.context
        prev, self.last = self.last, f
        dt = t - prev.timestampMs if prev is not None else 0
        continuous = prev is not None and dt <= p.maxObservationGapMs
        positive = f.eligible and f.candidate and f.posture == "LYING"
        negative = f.eligible and not f.candidate and f.posture in OTHER_POSTURES
        prior_negative = (
            prev is not None
            and prev.eligible
            and not prev.candidate
            and prev.posture in OTHER_POSTURES
        )
        if not continuous or not f.eligible:
            self.history.clear()
        if p.transitionEvidence == "POSTURE_DYNAMICS_V2":
            if not continuous:
                self.motion_history.clear()
                self.motion_at = None
            self.update_motion_v2(f)
        if p.transitionEvidence == "POSTURE_DYNAMICS_V3":
            if not continuous:
                self.motion_v3_history.clear()
                self.motion_at = None
            self.update_motion_v3(f)
        if p.transitionEvidence == "POSTURE_DYNAMICS_V1":
            if not continuous:
                self.motion_at = None
            if self.motion_at is not None and t - self.motion_at > p.rapidDescentWindowMs:
                self.motion_at = None
            if f.eligible and self.start is None and self.observed_transition(f):
                self.motion_at = t
        if self.state in {"ACTIVE", "REARMING"}:
            if negative:
                self.rearm_ms = (
                    self.rearm_ms + dt
                    if (continuous and prior_negative and self.state == "REARMING")
                    else 0
                )
                self.state = "REARMING"
                if self.rearm_ms >= p.rearmHoldMs:
                    self.clear_suspicion()
                    self.history.clear()
                    self.motion_history.clear()
                    self.motion_v3_history.clear()
                    self.rearm_ms = 0
                    self.closed = True
            else:
                # Uncertainty never closes the persisted episode or creates a new one.
                self.state, self.rearm_ms = "ACTIVE", 0
            return None
        if self.start is not None and (
            not continuous or t - self.last_candidate > p.maxObservationGapMs
        ):
            self.clear_suspicion()
            self.history.clear()
        if negative:
            self.negative_ms = self.negative_ms + dt if continuous and prior_negative else 0
            if self.negative_ms >= p.negativeResetMs:
                if (
                    p.transitionEvidence not in {"POSTURE_DYNAMICS_V2", "POSTURE_DYNAMICS_V3"}
                    or self.start is not None
                ):
                    self.clear_suspicion()
        elif positive:
            self.negative_ms = 0
            if self.start is None:
                self.start = t
                upright = [
                    old
                    for old in self.history
                    if old.eligible
                    and old.posture == "STANDING_OR_WALKING"
                    and 0 < t - old.timestampMs <= p.rapidDescentWindowMs
                ]
                self.rapid = bool(
                    len(upright) >= 2
                    and upright[-1].timestampMs - upright[0].timestampMs
                    >= p.transitionUprightHoldMs
                    and f.hipY is not None
                    and all(old.hipY is not None for old in upright)
                    and f.hipY - min(old.hipY for old in upright) >= p.minHipDescentNormalized
                )
                if p.transitionEvidence in {
                    "POSTURE_DYNAMICS_V1",
                    "POSTURE_DYNAMICS_V2",
                    "POSTURE_DYNAMICS_V3",
                }:
                    self.rapid = self.motion_at is not None
            if (
                p.transitionEvidence in {"POSTURE_DYNAMICS_V2", "POSTURE_DYNAMICS_V3"}
                and self.motion_at is not None
            ):
                self.rapid = True
            self.state = "SUSPECTED"
            self.last_candidate = t
        else:
            self.negative_ms = 0
        if self.start is not None:
            self.samples.append((t, positive))
            cutoff = max(self.start, t - p.floorHoldMs)
            while len(self.samples) > 1 and self.samples[1][0] <= cutoff:
                self.samples.popleft()
            pairs = list(self.samples)
            covered = sum(
                b[0] - max(a[0], cutoff)
                for a, b in zip(pairs, pairs[1:], strict=False)
                if a[1] and b[1] and b[0] - a[0] <= p.maxObservationGapMs
            )
            count = sum(valid for ts, valid in pairs if ts >= cutoff)
            fraction = covered / p.floorHoldMs
            if (
                positive
                and t - self.start >= p.floorHoldMs
                and count >= p.minValidObservations
                and fraction >= p.minValidPoseFraction
            ):
                self.state = "ACTIVE"
                self.samples.clear()
                self.history.clear()
                return Emission(
                    "POSSIBLE_FALL" if self.rapid else "PERSON_ON_FLOOR",
                    self.start,
                    t,
                    t - self.start,
                    fraction,
                    (sum(ts >= cutoff for ts, _ in pairs) - 1) * 1000 / p.floorHoldMs,
                    self.rapid,
                )
        if f.eligible:
            self.history.append(f)
            while self.history and t - self.history[0].timestampMs > p.rapidDescentWindowMs:
                self.history.popleft()
        return None


def create_engine(policy, active=False):
    cls = EvidenceEngine if policy.temporalMode == "EVIDENCE_V2" else TemporalEngine
    return cls(policy, active)
