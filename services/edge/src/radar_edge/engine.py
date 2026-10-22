"""Pure camera-local temporal engine. All time comes from supplied media features."""

from collections import deque
from dataclasses import dataclass

from radar_edge.policy import DEFAULT_POLICY


@dataclass(frozen=True)
class Emission:
    kind: str
    startedMs: int
    detectedMs: int
    floorDurationMs: int
    validPoseFraction: float
    analysisFps: float
    rapidDescentObserved: bool


class TemporalEngine:
    def __init__(self, policy=DEFAULT_POLICY, active=False):
        self.policy = policy
        self.state = "ACTIVE" if active else "OBSERVING"
        self.last = None
        self.context = None
        self.start = None
        self.last_candidate = None
        self.samples = deque()
        self.history = deque()
        self.rapid = False
        self.rearm_ms = 0
        self.closed = False

    def restore(self, saved):
        # Never reuse prior timing windows. ACTIVE survives; rearm starts afresh.
        self.state = "ACTIVE" if saved.get("state") in {"ACTIVE", "REARMING"} else "OBSERVING"

    def snapshot(self):
        return {"state": self.state}

    def clear_suspicion(self):
        self.start = self.last_candidate = None
        self.samples.clear()
        self.rapid = False
        self.state = "OBSERVING"

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
        if not continuous or not f.eligible:
            self.history.clear()
        if self.state in {"ACTIVE", "REARMING"}:
            if f.eligible and f.candidate:
                self.state, self.rearm_ms = "ACTIVE", 0
            elif f.eligible:
                if self.state == "REARMING" and continuous and prev.eligible and not prev.candidate:
                    self.rearm_ms += dt
                else:
                    self.rearm_ms = 0
                self.state = "REARMING"
                if self.rearm_ms >= p.rearmHoldMs:
                    self.clear_suspicion()
                    self.history.clear()
                    self.rearm_ms = 0
                    self.closed = True
            else:
                self.state, self.rearm_ms = "ACTIVE", 0
            return None
        if self.start is not None and (
            not continuous
            or (self.last_candidate is not None and t - self.last_candidate > p.maxObservationGapMs)
        ):
            self.clear_suspicion()
            self.history.clear()
        if f.eligible and not f.candidate:
            self.clear_suspicion()
        elif f.eligible and f.candidate:
            if self.start is None:
                self.start = t
                self.rapid = any(
                    0 < t - old.timestampMs <= p.rapidDescentWindowMs
                    and old.hipY is not None
                    and f.hipY - old.hipY >= p.minHipDescentNormalized
                    for old in self.history
                )
            self.state = "SUSPECTED"
            self.last_candidate = t
        if self.start is not None:
            self.samples.append((t, f.eligible and f.candidate))
            cutoff = max(self.start, t - p.floorHoldMs)
            while len(self.samples) > 1 and self.samples[1][0] <= cutoff:
                self.samples.popleft()
            covered = sum(
                b[0] - max(a[0], cutoff)
                for a, b in zip(self.samples, list(self.samples)[1:], strict=False)
                if a[1] and b[1] and b[0] - a[0] <= p.maxObservationGapMs
            )
            valid_count = sum(valid for ts, valid in self.samples if ts >= cutoff)
            duration = t - self.start
            fraction = covered / p.floorHoldMs
            if (
                f.eligible
                and f.candidate
                and duration >= p.floorHoldMs
                and valid_count >= p.minValidObservations
                and fraction >= p.minValidPoseFraction
            ):
                self.state = "ACTIVE"
                analysis_fps = (
                    (sum(ts >= cutoff for ts, _ in self.samples) - 1) * 1000 / p.floorHoldMs
                )
                self.samples.clear()
                self.history.clear()
                return Emission(
                    "POSSIBLE_FALL" if self.rapid else "PERSON_ON_FLOOR",
                    self.start,
                    t,
                    duration,
                    fraction,
                    analysis_fps,
                    self.rapid,
                )
        if f.eligible:
            self.history.append(f)
            while self.history and t - self.history[0].timestampMs > p.rapidDescentWindowMs:
                self.history.popleft()
        return None
