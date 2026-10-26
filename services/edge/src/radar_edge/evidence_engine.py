"""Versioned posture evidence with bounded uncertainty and explicit transition support."""

import math

from radar_edge.engine import Emission, TemporalEngine
from radar_edge.posture import OTHER_POSTURES


class EvidenceEngine(TemporalEngine):
    def __init__(self, policy, active=False):
        super().__init__(policy, active)
        self.negative_ms = 0
        self.motion_at = None

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
                if p.transitionEvidence == "POSTURE_DYNAMICS_V1":
                    self.rapid = self.motion_at is not None
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
