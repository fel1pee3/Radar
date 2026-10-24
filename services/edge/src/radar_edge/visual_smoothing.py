"""Optional display-only adaptive filter; never creates detector observations.

Own vector implementation inspired by Casiez/Roussel/Vogel's 1 Euro algorithm:
https://gery.casiez.net/1euro/ . Parameters validated in CALIBRATION replay only.
"""

import math

import numpy as np

from radar_edge.preview import usable_point


class VisualSmoother:
    def __init__(self):
        self.reset()

    def reset(self):
        self.states = {}
        self.timestamp = None
        self.scope = None

    @staticmethod
    def alpha(cutoff, dt):
        return 1 / (1 + 1 / (2 * math.pi * cutoff * dt))

    def update(self, observation, threshold=0.5):
        o = observation
        scope = (
            o.cameraId,
            o.runId,
            o.modelId,
            o.calibrationId,
            o.calibrationVersion,
            o.width,
            o.height,
            o.rotation,
        )
        dt = None if self.timestamp is None else (o.timestampMs - self.timestamp) / 1000
        if scope != self.scope or dt is None or not 0 < dt <= 0.250:
            self.states = {}
            dt = None
        self.scope, self.timestamp = scope, o.timestampMs
        if o.poseCount != 1 or len(o.poses) != 1 or min(o.width, o.height) < 2:
            self.states = {}
            return {}
        pose = o.poses[0]
        points = {
            p.index: p for p in pose.landmarks if usable_point(p, threshold, pose.qualitySource)
        }
        self.states = {k: s for k, s in self.states.items() if k in points}
        scale = np.array([o.width - 1, o.height - 1], dtype=float)
        length = float(max(scale))
        result = {}
        for key, point in points.items():
            raw = np.array([point.x, point.y]) * scale / length
            derivative = np.zeros(2)
            value = raw.copy()
            if key in self.states and dt is not None:
                previous, previous_derivative = self.states[key]
                ad = self.alpha(1.0, dt)
                derivative = ad * (raw - previous) / dt + (1 - ad) * previous_derivative
                cutoff = 1.5 + 30.0 * float(np.linalg.norm(derivative))
                a = self.alpha(cutoff, dt)
                value = a * raw + (1 - a) * previous
                correction = (value - raw) * length
                distance = float(np.linalg.norm(correction))
                if distance > 8.0:
                    value = raw + correction / distance * 8.0 / length
            self.states[key] = (value, derivative)
            result[key] = tuple(map(float, value * length))
        return result
