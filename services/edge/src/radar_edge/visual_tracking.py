"""Experimental visual-only flow. Never produces observations or detector evidence."""

from collections import Counter, deque
from dataclasses import dataclass
from time import perf_counter

import cv2
import numpy as np

from radar_edge.preview import usable_point


@dataclass(frozen=True)
class VisualPoints:
    points: dict
    kinds: dict
    age_ms: int | None


class VisualTracker:
    """Track only accepted body points, briefly, with forward/backward validation.

    Coordinates are pixels in the displayed source geometry. FLOW points have
    no model score/visibility and cannot be used as Landmark/Observation data.
    New model anchors always remove missing/low-quality points immediately.
    """

    def __init__(self, threshold=0.5, max_age_ms=250, anchor_blend=0.65, blur_sigma=0.8):
        self.threshold = threshold
        self.max_age_ms = max_age_ms
        self.anchor_blend = anchor_blend
        self.blur_sigma = blur_sigma
        self.gray = None
        self.points = {}
        self.timestamp = None
        self.anchor_timestamp = None
        self.scope = None
        self.geometry = None
        self.stats = Counter()
        self.flow_ms = deque(maxlen=1024)

    def clear(self, reason):
        self.gray = None
        self.points = {}
        self.timestamp = self.anchor_timestamp = None
        self.stats[f"reset:{reason}"] += 1

    def _flow(self, gray):
        if self.gray is None or not self.points:
            return {}
        keys = tuple(self.points)
        previous = np.array([self.points[k] for k in keys], dtype=np.float32).reshape(-1, 1, 2)
        options = {
            "winSize": (21, 21),
            "maxLevel": 3,
            "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
            "minEigThreshold": 0.0001,
        }
        started = perf_counter()
        forward, status, error = cv2.calcOpticalFlowPyrLK(
            self.gray, gray, previous, None, **options
        )
        if forward is None or status is None or error is None:
            self.stats["flowRejected"] += len(keys)
            return {}
        if not np.isfinite(forward).all():
            self.stats["flowRejected"] += len(keys)
            return {}
        backward, reverse, _ = cv2.calcOpticalFlowPyrLK(gray, self.gray, forward, None, **options)
        self.flow_ms.append((perf_counter() - started) * 1000)
        if backward is None or reverse is None:
            self.stats["flowRejected"] += len(keys)
            return {}
        height, width = gray.shape
        result = {}
        for n, key in enumerate(keys):
            point = forward[n, 0]
            valid = (
                status[n, 0]
                and reverse[n, 0]
                and np.isfinite(point).all()
                and np.isfinite(backward[n, 0]).all()
                and np.linalg.norm(backward[n, 0] - previous[n, 0]) <= 1.5
                and error[n, 0] <= 20
                and 0 <= point[0] < width
                and 0 <= point[1] < height
            )
            if valid:
                result[key] = tuple(map(float, point))
                self.stats["flowAccepted"] += 1
            else:
                self.stats["flowRejected"] += 1
        return result

    def update(self, frame, anchor=None):
        geometry = (frame.geometry, frame.bgr.shape)
        if self.geometry is not None and geometry != self.geometry:
            self.clear("geometry")
        self.geometry = geometry
        if self.timestamp is not None and (
            frame.timestamp_ms <= self.timestamp or frame.timestamp_ms - self.timestamp > 250
        ):
            self.clear("time")
        if anchor is not None:
            if anchor.frameIndex != frame.index or anchor.timestampMs != frame.timestamp_ms:
                raise ValueError("Visual anchor must match its original frame")
            scope = (anchor.cameraId, anchor.runId, anchor.modelId)
            if self.scope is not None and scope != self.scope:
                self.clear("source")
            self.scope = scope
        gray = cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY)
        if self.blur_sigma > 0:
            gray = cv2.GaussianBlur(gray, (5, 5), self.blur_sigma)
        predicted = self._flow(gray)
        kinds = {key: "FLOW" for key in predicted}
        if anchor is not None:
            self.stats["modelFrames"] += 1
            self.anchor_timestamp = frame.timestamp_ms
            current = {}
            if anchor.poseCount == 1 and len(anchor.poses) == 1:
                pose = anchor.poses[0]
                height, width = gray.shape
                for point in pose.landmarks:
                    if not usable_point(point, self.threshold, pose.qualitySource):
                        continue
                    raw = np.array((point.x * (width - 1), point.y * (height - 1)))
                    value = raw
                    kinds[point.index] = "MODEL"
                    if point.index in predicted:
                        delta = np.array(predicted[point.index]) - raw
                        # Large disagreement resets to the current observation.
                        if np.linalg.norm(delta) <= 8:
                            correction = delta * self.anchor_blend
                            length = np.linalg.norm(correction)
                            if length > 4:
                                correction *= 4 / length
                            value = raw + correction
                            kinds[point.index] = "FLOW"
                            self.stats["anchorAdjustments"] += 1
                    current[point.index] = tuple(map(float, value))
            else:
                self.stats["reset:noSinglePose"] += 1
            # No old point survives a rejected/missing current model point.
            predicted = current
        age = None if self.anchor_timestamp is None else frame.timestamp_ms - self.anchor_timestamp
        if age is None or age > self.max_age_ms:
            predicted = {}
            self.stats["expiredFrames"] += 1
        self.points = predicted
        self.gray = gray
        self.timestamp = frame.timestamp_ms
        return VisualPoints(dict(predicted), {k: kinds[k] for k in predicted}, age)

    def summary(self):
        return {
            "kind": "VISUAL_ONLY",
            "parameters": {
                "maxAgeMs": self.max_age_ms,
                "anchorBlend": self.anchor_blend,
                "blurSigma": self.blur_sigma,
                "maxForwardBackwardErrorPx": 1.5,
                "maxPhotometricError": 20,
                "maxAnchorAdjustmentPx": 4,
            },
            "counts": dict(self.stats),
            "flowMsMean": float(np.mean(self.flow_ms)) if self.flow_ms else None,
            "flowMsP95": float(np.percentile(self.flow_ms, 95)) if self.flow_ms else None,
            "timingScope": "Last 1024 flow calls; comparison only, not full LIVE latency",
            "modelScoreFabricated": False,
            "detectorInputChanged": False,
        }
