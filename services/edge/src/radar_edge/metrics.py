"""Bounded aggregates and OS process counters, not a host-wide performance monitor."""

import ctypes
import os
import platform
from collections import Counter
from time import perf_counter, process_time


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
    def __init__(self):
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

    def add(self, observation):
        self.analyzed += 1
        self.states[observation.inferenceState] += 1
        self.reasons.update(observation.qualityReasons)
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
