"""Bounded aggregates and OS process counters, not a host-wide performance monitor."""

import ctypes
import math
import os
import platform
from collections import Counter
from time import perf_counter, process_time

from radar_edge.observations import ESSENTIAL

LANDMARK_FAILURE_REASONS = ("missing", "nonfinite", "outOfFrame", "lowVisibility", "lowPresence")


def process_peak_memory() -> tuple[int | None, str]:
    if platform.system() == "Windows":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                *(
                    (name, ctypes.c_size_t)
                    for name in (
                        "PeakWorkingSetSize",
                        "WorkingSetSize",
                        "QuotaPeakPagedPoolUsage",
                        "QuotaPagedPoolUsage",
                        "QuotaPeakNonPagedPoolUsage",
                        "QuotaNonPagedPoolUsage",
                        "PagefileUsage",
                        "PeakPagefileUsage",
                    )
                ),
            ]

        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(Counters),
                wintypes.DWORD,
            ]
            if psapi.GetProcessMemoryInfo(
                kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
            ):
                return (
                    counters.PeakWorkingSetSize,
                    "Windows GetProcessMemoryInfo: process lifetime peak working set",
                )
        except (OSError, AttributeError):
            pass
    return None, "Not measured on this platform"


class Metrics:
    def __init__(self, visibility=0.5, quality_source="MEDIAPIPE"):
        if not math.isfinite(visibility) or not 0 <= visibility <= 1:
            raise ValueError("Invalid landmark visibility threshold")
        self.visibility = visibility
        self.quality_source = quality_source
        self.wall_start = perf_counter()
        self.cpu_start = process_time()
        self.analyzed = 0
        self.skipped = 0
        self.states = Counter()
        self.reasons = Counter()
        self.inference_sum = 0.0
        self.inference_max = 0.0
        self.inference_min = None
        self.first_ms = None
        self.last_ms = None
        self.live_age = {
            name: {"samples": 0, "sum": 0.0, "max": 0.0}
            for name in ("frameAgeAtAnalysisStartMs", "frameAgeAfterInferenceMs")
        }
        self.pose_observations = Counter({"none": 0, "one": 0, "multiple": 0})
        self.pose_count_mismatches = 0
        self.quality_sources = Counter()
        self.keypoint_score_failures = Counter(dict.fromkeys(sorted(ESSENTIAL), 0))
        self.landmark_failures = {
            index: Counter(dict.fromkeys(LANDMARK_FAILURE_REASONS, 0))
            for index in sorted(ESSENTIAL)
        }

    def add_landmark_diagnostics(self, observation):
        count = len(observation.poses)
        self.pose_observations["none" if count == 0 else "one" if count == 1 else "multiple"] += 1
        if observation.poseCount != count:
            self.pose_count_mismatches += 1
            return
        if count != 1:
            return  # No pose is not eight missing joints; never mix people from multiple poses.
        quality_source = observation.poses[0].qualitySource
        self.quality_sources[quality_source] += 1
        points = {point.index: point for point in observation.poses[0].landmarks}
        for index, counts in self.landmark_failures.items():
            point = points.get(index)
            if point is None:
                counts["missing"] += 1
                continue
            score_mode = quality_source == "RTMO_KEYPOINT_SCORE"
            values = (
                (point.x, point.y, point.confidence)
                if score_mode
                else (point.x, point.y, point.visibility, point.presence)
            )
            counts["missing"] += any(value is None for value in values)
            counts["nonfinite"] += any(
                value is not None and not math.isfinite(value) for value in values
            )
            counts["outOfFrame"] += any(
                value is not None and math.isfinite(value) and not 0 <= value <= 1
                for value in (point.x, point.y)
            )
            if score_mode:
                self.keypoint_score_failures[index] += (
                    point.confidence is None
                    or not math.isfinite(point.confidence)
                    or not self.visibility <= point.confidence <= 1
                )
                continue
            for reason, value in (
                ("lowVisibility", point.visibility),
                ("lowPresence", point.presence),
            ):
                counts[reason] += (
                    value is not None and math.isfinite(value) and not self.visibility <= value <= 1
                )

    def add(self, observation):
        for name, values in self.live_age.items():
            age = getattr(observation, name, None)
            if age is not None and math.isfinite(age) and age >= 0:
                values["samples"] += 1
                values["sum"] += age
                values["max"] = max(values["max"], age)
        self.analyzed += 1
        self.states[observation.inferenceState] += 1
        self.reasons.update(observation.qualityReasons)
        self.add_landmark_diagnostics(observation)
        self.inference_sum += observation.inferenceMs
        self.inference_max = max(self.inference_max, observation.inferenceMs)
        self.inference_min = (
            min(self.inference_min, observation.inferenceMs)
            if self.inference_min is not None
            else observation.inferenceMs
        )
        if self.first_ms is None:
            self.first_ms = observation.timestampMs
        self.last_ms = observation.timestampMs

    def summary(self):
        wall = perf_counter() - self.wall_start
        cpu = process_time() - self.cpu_start
        memory, method = process_peak_memory()
        return {
            "analyzedFrames": self.analyzed,
            "skippedBySampling": self.skipped,
            "inferenceStates": dict(self.states),
            "noPoseObservations": self.states["NO_POSE"],
            "multiplePoseObservations": self.states["MULTIPLE_POSES"],
            "lowConfidenceObservations": self.states["LOW_CONFIDENCE"],
            "qualityReasons": dict(self.reasons),
            "landmarkDiagnostics": {
                "minLandmarkVisibility": self.visibility
                if self.quality_source == "MEDIAPIPE"
                else None,
                "minKeypointScore": self.visibility
                if self.quality_source == "RTMO_KEYPOINT_SCORE"
                else None,
                "qualitySources": dict(self.quality_sources),
                "thresholdSemantics": "Backend-specific; keypoint score is not visibility/presence",
                "keypointScoreFailures": {
                    str(k): v for k, v in self.keypoint_score_failures.items()
                },
                "scope": "SINGLE_POSE_ONLY",
                "poseObservations": dict(self.pose_observations),
                "poseCountMismatchObservations": self.pose_count_mismatches,
                "essentialLandmarkFailures": {
                    str(index): dict(counts) for index, counts in self.landmark_failures.items()
                },
            },
            "firstAnalyzedTimestampMs": self.first_ms,
            "lastAnalyzedTimestampMs": self.last_ms,
            "analysisSamplesPerMediaSecond": (
                (self.analyzed - 1) * 1000 / (self.last_ms - self.first_ms)
                if self.analyzed > 1 and self.last_ms > self.first_ms
                else None
            ),
            "inferenceMs": {
                "mean": self.inference_sum / self.analyzed if self.analyzed else None,
                "min": self.inference_min,
                "max": self.inference_max if self.analyzed else None,
            },
            "totalWallSeconds": wall,
            "liveFrameAgeMs": {
                name: {
                    "samples": value["samples"],
                    "mean": value["sum"] / value["samples"] if value["samples"] else None,
                    "max": value["max"] if value["samples"] else None,
                }
                for name, value in self.live_age.items()
            },
            "processCpuSeconds": cpu,
            "processCpuPercentOneCore": 100 * cpu / wall if wall > 0 else None,
            "logicalCpuCount": os.cpu_count(),
            "analyzedFramesPerWallSecond": self.analyzed / wall if wall > 0 else None,
            "cpuMethod": (
                "time.process_time delta / time.perf_counter delta; "
                "100% equals one logical CPU; includes native threads"
            ),
            "peakProcessMemoryBytes": memory,
            "memoryMethod": method,
            "throughputScope": (
                "includes model/hash/setup/decoding/preview/pacing/cleanup; "
                "not a real-time guarantee"
            ),
        }
