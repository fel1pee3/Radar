"""Opt-in bounded search on current pixels; memory contains processing choices only."""

from collections import Counter
from dataclasses import replace
from time import perf_counter

import cv2

from radar_edge.errors import EdgeError
from radar_edge.observations import Pose
from radar_edge.rtmo import RtmoEstimator

MAX_CALLS = 2
EXTRA_CALL_START_MS = 220
FULL_SCAN_MS = 800
LEASE_MS = 1600
MAX_INPUT_GAP_MS = 500
SEARCH_MS = 1600
SEARCH_ANALYSES = 8
SEARCH_PATHS = ("ROTATE_270", "ROTATE_90", "ROTATE_180", "CENTER_80")
CROPS = {"PERSON_PROPOSAL_CROP", "CENTER_80"}


class PreferredRtmoEstimator(RtmoEstimator):
    def __init__(self, model_path, runtime_profile="REFERENCE_4_SPIN"):
        super().__init__(model_path, recovery="RTMO_ADAPTIVE_V3", runtime_profile=runtime_profile)
        self.preferred = None
        self.lease_until = -1
        self.last_full = None
        self.last_input = None
        self.last_geometry = None
        self.search_started = None
        self.search_analyses = self.cursor = 0
        self.counts = Counter()
        self.pending = []

    def reset_preference(self, reason):
        self.preferred = None
        self.lease_until = -1
        self.last_full = None
        self.search_started = None
        self.search_analyses = self.cursor = 0
        self.counts["reset." + reason] += 1
        self.pending = [*self.pending[-15:], reason]

    def _search(self, timestamp, tried):
        while self.cursor < len(SEARCH_PATHS):
            path = SEARCH_PATHS[self.cursor]
            if path not in tried:
                return path
            self.cursor += 1
        self.reset_preference("SEARCH_CYCLE_EXHAUSTED")
        self.search_started = timestamp
        return None

    def _run_path(self, path, frame, proposal):
        image = frame.bgr
        if path == "ORIGINAL":
            result = self.infer_image(image)
        elif path == "PERSON_PROPOSAL_CROP":
            result = self.proposal_crop(image, proposal)
        elif path in {"ROTATE_270", "ROTATE_90"}:
            result = self.quarter_turn(image, path == "ROTATE_90")
        else:
            height, width = image.shape[:2]
            if path == "ROTATE_180":
                pixels = cv2.rotate(image, cv2.ROTATE_180)

                def restore(x, y):
                    return (width - 1) / width - x, (height - 1) / height - y
            else:
                x1, y1, x2, y2 = (
                    int(0.1 * width),
                    int(0.1 * height),
                    int(0.9 * width),
                    int(0.9 * height),
                )
                pixels = image[y1:y2, x1:x2]

                def restore(x, y):
                    return (x * (x2 - x1) + x1) / width, (y * (y2 - y1) + y1) / height

            poses, boxes, score = self.infer_image(pixels)
            started = perf_counter()
            poses = tuple(
                Pose(
                    tuple(
                        replace(p, x=restore(p.x, p.y)[0], y=restore(p.x, p.y)[1])
                        for p in pose.landmarks
                    ),
                    pose.qualitySource,
                )
                for pose in poses
            )
            restored = []
            for box in boxes:
                corners = [restore(box[x], box[y]) for x, y in ((0, 1), (0, 3), (2, 1), (2, 3))]
                restored.append(
                    (
                        min(p[0] for p in corners),
                        min(p[1] for p in corners),
                        max(p[0] for p in corners),
                        max(p[1] for p in corners),
                        box[4],
                    )
                )
            self.perception_attempts[-1]["restoreMs"] = (perf_counter() - started) * 1000
            result = poses, tuple(restored), score
        self.perception_attempts[-1]["pass"] = path
        if not self.perception_attempts[-1].get("skippedReason"):
            self.counts["call." + path] += 1
        return result

    def estimate(self, frame):
        if frame.timestamp_ms <= self.previous_ms:
            raise EdgeError("MODEL_TIMESTAMP_ERROR", "Timestamps da análise devem ser crescentes.")
        started = perf_counter()
        timestamp = frame.timestamp_ms
        geometry = (frame.bgr.shape, getattr(frame, "geometry", None))
        if self.last_geometry is not None and geometry != self.last_geometry:
            self.reset_preference("GEOMETRY_CHANGED")
        if self.last_input is not None and timestamp - self.last_input > MAX_INPUT_GAP_MS:
            self.reset_preference("INPUT_GAP")
        self.last_input, self.last_geometry = timestamp, geometry
        if self.preferred and timestamp >= self.lease_until:
            self.reset_preference("LEASE_EXPIRED")
        if self.search_started is not None and (
            timestamp - self.search_started >= SEARCH_MS or self.search_analyses >= SEARCH_ANALYSES
        ):
            self.reset_preference("SEARCH_LIMIT")
        if self.preferred is None:
            if self.search_started is None:
                self.search_started = timestamp
            self.search_analyses += 1
        before = self.preferred
        self.perception_attempts = []
        tried, scores = [], []
        best = ((), (), None)
        best_quality, selected = -1, None
        useful = False
        original_proposal = None  # Exists only within this frame, never across estimates.
        due = self.last_full is None or timestamp - self.last_full >= FULL_SCAN_MS
        path = (
            "ORIGINAL"
            if due or self.preferred in CROPS or self.preferred == "ORIGINAL"
            else self.preferred or self._search(timestamp, tried) or "ORIGINAL"
        )
        try:
            while path and len(tried) < MAX_CALLS:
                if tried and (perf_counter() - started) * 1000 >= EXTRA_CALL_START_MS:
                    self.counts["extraCallDeferred"] += 1
                    self.pending.append("EXTRA_CALL_BUDGET")
                    break
                poses, boxes, score = self._run_path(path, frame, original_proposal)
                tried.append(path)
                if path in SEARCH_PATHS:
                    self.cursor = SEARCH_PATHS.index(path) + 1
                if score is not None:
                    scores.append(score)
                if path == "ORIGINAL":
                    self.last_full = timestamp
                    original_proposal = self.proposal
                quality = self.valid_essential(poses)
                if len(poses) > 1:
                    best, selected = (poses, boxes, score), path
                    self.reset_preference("MULTIPLE_PEOPLE")
                    break
                if quality > best_quality:
                    best, selected, best_quality = (
                        (poses, boxes, score),
                        path if poses else None,
                        quality,
                    )
                if quality == 8:
                    useful = True
                    self.preferred = "ORIGINAL" if path == "PERSON_PROPOSAL_CROP" else path
                    self.lease_until = self.last_full + LEASE_MS
                    self.search_started = None
                    self.search_analyses = self.cursor = 0
                    break
                if path == before:
                    self.reset_preference("CURRENT_PATH_FAILED")
                    self.search_started = timestamp
                    if path in SEARCH_PATHS:
                        self.cursor = SEARCH_PATHS.index(path) + 1
                    # Canonical inspection on this same frame remains usable.
                    if "ORIGINAL" in tried:
                        self.last_full = timestamp
                if len(tried) >= MAX_CALLS:
                    break
                if path != "ORIGINAL" and "ORIGINAL" not in tried:
                    if before is None:
                        break  # Search is spread across fresh frames; audit has its own deadline.
                    path = "ORIGINAL"
                elif (
                    before in CROPS
                    and before not in tried
                    and (before != "PERSON_PROPOSAL_CROP" or original_proposal is not None)
                ):
                    path = before
                elif before and before not in tried and before not in CROPS:
                    path = before
                elif original_proposal is not None and "PERSON_PROPOSAL_CROP" not in tried:
                    path = "PERSON_PROPOSAL_CROP"
                else:
                    path = self._search(timestamp, tried)
            self.counts["analyses"] += 1
            self.counts["useful"] += useful
            self.counts["inconclusive"] += not useful
            self.counts["preferredSuccess"] += bool(useful and before and selected == before)
            diagnostic = {
                "strategy": "RTMO_PREFERRED_V1",
                "preferredBefore": before,
                "preferredAfter": self.preferred,
                "selectedPath": selected,
                "useful": useful,
                "calls": sum(not a.get("skippedReason") for a in self.perception_attempts),
                "canonicalInspected": "ORIGINAL" in tried,
                "searchAgeMs": timestamp - self.search_started
                if self.search_started is not None
                else None,
                "transitions": self.pending[-16:],
                "leaseUntilMs": self.lease_until,
                "noSavedCallCounterfactualReported": True,
            }
            self.pending = []
            self.perception_attempts[0]["strategy"] = diagnostic
            self.person_detections = best[1]
            self.perception_passes = tuple(tried)
            self.person_proposal_score = max(scores) if scores else None
            self.proposal = None  # Current-frame ROI is never retained as a search preference.
            self.proposal_essential = 0
            self.previous_ms = timestamp
            return best[0], (perf_counter() - started) * 1000
        except Exception as failure:
            self.reset_preference("INFERENCE_ERROR")
            if isinstance(failure, EdgeError):
                raise
            raise EdgeError(
                "MODEL_INFERENCE_ERROR", "Falha real da busca adaptativa RTMO."
            ) from failure

    def strategy_summary(self):
        return {
            "strategy": "RTMO_PREFERRED_V1",
            "counts": dict(self.counts),
            "limits": {
                "maxCalls": MAX_CALLS,
                "extraCallStartMs": EXTRA_CALL_START_MS,
                "fullScanMs": FULL_SCAN_MS,
                "leaseMs": LEASE_MS,
                "searchMs": SEARCH_MS,
                "searchAnalyses": SEARCH_ANALYSES,
            },
        }
