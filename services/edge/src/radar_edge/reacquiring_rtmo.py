"""V2: canonical-first reacquisition, with unchanged V1 work/quality limits."""

from time import perf_counter

from radar_edge.errors import EdgeError
from radar_edge.preferred_rtmo import (
    CROPS,
    EXTRA_CALL_START_MS,
    FULL_SCAN_MS,
    LEASE_MS,
    MAX_CALLS,
    MAX_INPUT_GAP_MS,
    SEARCH_ANALYSES,
    SEARCH_MS,
    SEARCH_PATHS,
    PreferredRtmoEstimator,
)


class ReacquiringRtmoEstimator(PreferredRtmoEstimator):
    def __init__(self, model_path, runtime_profile="REFERENCE_4_SPIN"):
        super().__init__(model_path, runtime_profile=runtime_profile)
        self.proposal_checked = False

    def reset_preference(self, reason):
        super().reset_preference(reason)
        self.proposal_checked = False

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
            if self.preferred is None
            or due
            or self.preferred in CROPS
            or self.preferred == "ORIGINAL"
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
                if path == "PERSON_PROPOSAL_CROP":
                    self.proposal_checked = True
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
                    self.preferred = path
                    self.lease_until = self.last_full + LEASE_MS
                    self.search_started = None
                    self.search_analyses = self.cursor = 0
                    self.proposal_checked = False
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
                    path = "ORIGINAL"
                elif (
                    before in CROPS
                    and before not in tried
                    and (before != "PERSON_PROPOSAL_CROP" or original_proposal is not None)
                ):
                    path = before
                elif before and before not in tried and before not in CROPS:
                    path = before
                elif (
                    original_proposal is not None
                    and "PERSON_PROPOSAL_CROP" not in tried
                    and (not self.proposal_checked or bool(best[0]))
                ):
                    path = "PERSON_PROPOSAL_CROP"
                else:
                    path = self._search(timestamp, tried)
            self.counts["analyses"] += 1
            self.counts["useful"] += useful
            self.counts["inconclusive"] += not useful
            self.counts["preferredSuccess"] += bool(useful and before and selected == before)
            diagnostic = {
                "strategy": "RTMO_PREFERRED_V2",
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
                "reacquiringBefore": before is None,
                "reacquiringAfter": self.preferred is None,
                "nextAnalysisPriority": "ORIGINAL" if self.preferred is None else self.preferred,
                "originalDeferredAfterFailure": not useful and "ORIGINAL" not in tried,
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
        result = super().strategy_summary()
        result["strategy"] = "RTMO_PREFERRED_V2"
        return result
