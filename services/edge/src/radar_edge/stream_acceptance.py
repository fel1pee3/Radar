"""Deadline audit for paced FILE traces; EOF is not real-time success."""

from math import isfinite


def assess_stream_timing(records, duration_ms, origin_ns, *, max_age_ms=2000, max_gap_ms=500):
    """Audit full source horizon and final decision wall age without rewriting traces.

    Nanoseconds are host-monotonic; milliseconds are media/elapsed durations.
    Missing timing cannot produce successful real-time acceptance.
    """
    if not isinstance(duration_ms, (int, float)) or not isfinite(duration_ms) or duration_ms <= 0:
        raise ValueError("Expected a positive finite full source duration")
    decisions = [r for r in records if r.get("recordType") == "DECISION"]
    profiles = {r["timestampMs"]: r for r in records if r.get("recordType") == "PROCESSING_PROFILE"}
    timed = []
    missing = stale = negative_start = 0
    for d in decisions:
        p = profiles.get(d["timestampMs"], {})
        t = d.get("timing", {})
        start = t.get("frameAgeAtAnalysisStartMs")
        age = t.get("capturedFrameAgeAtDecisionMs")
        ns = p.get("monotonicStartNs")
        if any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v)
            for v in (start, age, ns, origin_ns)
        ):
            missing += 1
            continue
        negative_start += start < 0
        if age < 0:
            missing += 1
            continue
        finished = p.get("monotonicFinishedNs")
        preview_age = p.get("frameAgeAfterPreviewMs")
        if all(isinstance(v, (int, float)) and isfinite(v) for v in (finished, preview_age)):
            # Paired end/age samples reconstruct acquisition more closely than start.
            captured_ms = (finished - origin_ns) / 1e6 - preview_age
        else:
            captured_ms = (ns - origin_ns) / 1e6 - start
        ready_ms = captured_ms + age
        stale += age > max_age_ms
        timed.append((d, ready_ms, age))
    eligible = capture = 0
    gaps = []
    capture_flags = {"FRAME_TIMEOUT", "LOW_FPS", "LOW_LIGHT", "POSSIBLE_FROZEN"}
    for a, b in zip(timed, timed[1:], strict=False):
        da, ra, aa = a
        db, rb, ab = b
        media_gap = db["timestampMs"] - da["timestampMs"]
        host_gap = rb - ra
        gaps.append(host_gap)
        if not (
            0 < media_gap <= max_gap_ms
            and 0 < host_gap <= max_gap_ms
            and aa <= max_age_ms
            and ab <= max_age_ms
        ):
            continue
        if all(d.get("quality", {}).get("eligible", False) for d in (da, db)):
            eligible += media_gap
        if all(
            not capture_flags.intersection(d.get("quality", {}).get("reasons", []))
            for d in (da, db)
        ):
            capture += media_gap
    return {
        "criterion": "FULL_SOURCE_HORIZON_AND_CURRENT_DECISION_WALL_TIME_V1",
        "durationMs": duration_ms,
        "decisionCoverage": eligible / duration_ms,
        "captureCoverage": capture / duration_ms,
        "approvalRequiresSceneAnnotations": True,
        "timingComplete": bool(decisions) and not missing,
        "missingTimingDecisions": missing,
        "staleDecisions": stale,
        "negativeStartAgesRecorded": negative_start,
        "maxDecisionAgeMs": max((a for _, _, a in timed), default=None),
        "maxDecisionHostGapMs": max(gaps, default=None),
        "decisionHostGapsAbove500": sum(g > max_gap_ms for g in gaps),
        "unobservedHeadMs": decisions[0]["timestampMs"] if decisions else duration_ms,
        "unobservedTailMs": max(0, duration_ms - decisions[-1]["timestampMs"])
        if decisions
        else duration_ms,
        "lastDecisionFromOriginMs": timed[-1][1] if timed else None,
        "timelyEligibleMediaMs": eligible,
        "timelyCaptureEligibleMs": capture,
        "events": [
            {
                "sourceOffsetMs": d["timestampMs"],
                "readyFromSourceOriginMs": ready,
                "kind": d["emission"].get("kind"),
            }
            for d, ready, _ in timed
            if d.get("emission")
        ],
        "maxAgeMs": max_age_ms,
        "maxGapMs": max_gap_ms,
        "timingGate": bool(decisions) and not missing and not stale,
    }
