"""Limited attribution of saved LIVE coverage. No video, model, camera or HTTP."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/edge/src"))
from radar_edge.stream_acceptance import assess_stream_timing


def complement(intervals, end):
    result, cursor = [], 0.0
    for a, b in sorted(intervals):
        a, b = max(0, a), min(end, b)
        if b <= a:
            continue
        if a > cursor:
            result.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < end:
        result.append((cursor, end))
    return result


def audit(path, output, planned_ms):
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    r = json.loads(path.read_text(encoding="utf-8"))
    if r["mode"] != "LIVE":
        raise ValueError("Expected saved LIVE report; no replay relabeling")
    trace = Path(r["decisionExport"]["path"])
    trace_hash = hashlib.sha256(trace.read_bytes()).hexdigest()
    records = [json.loads(x) for x in trace.read_text(encoding="utf-8").splitlines()]
    origin = r["source"]["hostMonotonicOriginNs"]
    ds = [x for x in records if x["recordType"] == "DECISION"]
    ps = {x["timestampMs"]: x for x in records if x["recordType"] == "PROCESSING_PROFILE"}
    offset = r["sourceTimestampOffsetMs"]
    actual = r["metrics"]["totalWallSeconds"] * 1000
    measured = []
    for d in ds:
        p = ps.get(d["timestampMs"])
        if p:
            captured = (p["monotonicFinishedNs"] - origin) / 1e6 - p["frameAgeAfterPreviewMs"]
            measured.append((d, captured + d["timing"]["capturedFrameAgeAtDecisionMs"]))
    intervals, delays = [], []
    for (a, ra), (b, rb) in zip(measured, measured[1:], strict=False):
        gap = b["timestampMs"] - a["timestampMs"]
        elapsed = rb - ra
        ages = [d["timing"]["capturedFrameAgeAtDecisionMs"] for d in (a, b)]
        timely = 0 < gap <= 500 and 0 < elapsed <= 500 and all(0 <= age <= 2000 for age in ages)
        if timely and a["quality"]["eligible"] and b["quality"]["eligible"]:
            intervals.append((a["timestampMs"] - offset, b["timestampMs"] - offset))
        if gap > 500 or elapsed > 500:
            p = ps[b["timestampMs"]]
            delays.append(
                {
                    "fromCaptureMs": a["timestampMs"] - offset,
                    "toCaptureMs": b["timestampMs"] - offset,
                    "mediaGapMs": gap,
                    "decisionHostGapMs": elapsed,
                    "fromHostReadyMs": ra,
                    "toHostReadyMs": rb,
                    "bothEndpointsIneligible": not a["quality"]["eligible"]
                    and not b["quality"]["eligible"],
                    "nextInferenceMs": p["inferenceMs"],
                    "nextCheckpointMs": p["eventRuntimeStages"].get("checkpointMs"),
                    "nextTotalProcessingMs": p["totalProcessingMs"],
                    "scope": "OVERLAPS_QUALITY_GAPS_DO_NOT_ADD_TO_UNCOVERED_SUM",
                }
            )
    planned = assess_stream_timing(records, planned_ms, origin)
    executed = assess_stream_timing(records, actual, origin)
    assert sum(b - a for a, b in intervals) == planned["timelyEligibleMediaMs"]
    first = ds[0]["timestampMs"] - offset
    last = ds[-1]["timestampMs"] - offset
    last_profile = max(ps) - offset
    parts = []
    for a, b in complement(intervals, planned_ms):
        boundaries = sorted({a, b, *[v for v in (first, last_profile, last, actual) if a < v < b]})
        for lo, hi in zip(boundaries, boundaries[1:], strict=False):
            if hi <= first:
                category = "INITIALIZATION_NO_ANALYZED_CAPTURE"
            elif lo >= actual:
                category = "NOT_EXECUTED_AFTER_MANUAL_END"
            elif lo >= last:
                category = "FINAL_TAIL_PROCESSING_AND_CLOSURE_NOT_SEPARABLE"
            elif lo >= last_profile and ds[-1]["timestampMs"] not in ps:
                category = "MISSING_FINAL_PROFILE_ALSO_INELIGIBLE_OBSERVATIONS"
            else:
                category = "OBSERVATIONS_WITHOUT_TIMELY_ELIGIBLE_DECISION"
            cause = "INDETERMINATE_WITHOUT_VIDEO_OR_PRECISE_ANNOTATION"
            if category == "INITIALIZATION_NO_ANALYZED_CAPTURE":
                cause = "SETUP_PHASE_BEFORE_FIRST_ANALYZED_CAPTURE"
            elif category == "NOT_EXECUTED_AFTER_MANUAL_END":
                cause = "MANUAL_END_CONFIRMED_BY_FOUNDER"
            parts.append(
                dict(
                    startMs=lo, endMs=hi, durationMs=hi - lo, category=category, physicalCause=cause
                )
            )
    assert (
        abs(sum(x["durationMs"] for x in parts) + planned["timelyEligibleMediaMs"] - planned_ms)
        < 0.001
    )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert hashlib.sha256(trace.read_bytes()).hexdigest() == trace_hash
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "scope": "LIMITED_SAVED_DATA_ATTRIBUTION_NOT_HUMAN_ANNOTATION",
        "reportSha256": before,
        "traceSha256": trace_hash,
        "planned": planned,
        "executed": executed,
        "captureClockOffsetMs": offset,
        "uncoveredPartition": parts,
        "processingDelayIntervals": delays,
        "originalsUnchanged": True,
        "noNewSamples": True,
    }
    (output / "coverage.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (output / "coverage-intervals.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(parts[0]))
        writer.writeheader()
        writer.writerows(parts)
    print(
        json.dumps(
            {
                "output": str(output),
                "plannedCoverage": planned["decisionCoverage"],
                "executedCoverage": executed["decisionCoverage"],
                "unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--planned-seconds", required=True, type=float)
    a = p.parse_args()
    audit(a.report, a.output, a.planned_seconds * 1000)
