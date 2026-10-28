"""Publish uncovered media intervals using the same final host-clock eligibility gate."""

import argparse
import csv
import json
from pathlib import Path


def complement(intervals, duration):
    result, cursor = [], 0.0
    for start, end in intervals:
        if start > cursor:
            result.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < duration:
        result.append((cursor, duration))
    return result


def audit(root):
    protocol = json.loads((root / "stream-protocol.frozen.json").read_text(encoding="utf-8"))
    rows = []
    for rep in range(1, len(protocol["orders"]) + 1):
        for backend in protocol["python"]:
            for item in protocol["cases"]:
                path = root / f"stream-r{rep}-{backend}-{item['id']}" / "summary.json"
                summary = json.loads(path.read_text(encoding="utf-8"))
                report = json.loads(Path(summary["reportPath"]).read_text(encoding="utf-8"))
                records = [
                    json.loads(line)
                    for line in Path(report["decisionExport"]["path"])
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                decisions = [r for r in records if r["recordType"] == "DECISION"]
                profiles = {
                    r["timestampMs"]: r for r in records if r["recordType"] == "PROCESSING_PROFILE"
                }
                origin = summary["source"]["hostMonotonicOriginNs"]
                duration = summary["wallTimingAcceptance"]["durationMs"]
                ready = {}
                for d in decisions:
                    p = profiles[d["timestampMs"]]
                    ready[d["timestampMs"]] = (
                        (p["monotonicFinishedNs"] - origin) / 1e6
                        - p["frameAgeAfterPreviewMs"]
                        + d["timing"]["capturedFrameAgeAtDecisionMs"]
                    )
                eligible, captured = [], []
                flags = {"FRAME_TIMEOUT", "LOW_FPS", "LOW_LIGHT", "POSSIBLE_FROZEN"}
                for a, b in zip(decisions, decisions[1:], strict=False):
                    start, end = a["timestampMs"], b["timestampMs"]
                    if not (
                        0 < end - start <= 500
                        and 0 < ready[end] - ready[start] <= 500
                        and all(d["timing"]["capturedFrameAgeAtDecisionMs"] <= 2000 for d in (a, b))
                    ):
                        continue
                    if all(d["quality"]["eligible"] for d in (a, b)):
                        eligible.append((start, end))
                    if all(not flags.intersection(d["quality"]["reasons"]) for d in (a, b)):
                        captured.append((start, end))
                for kind, intervals, key in (
                    ("NO_TIMELY_ELIGIBLE_DECISION", eligible, "timelyEligibleMediaMs"),
                    ("NO_TIMELY_CAPTURE_COVERAGE", captured, "timelyCaptureEligibleMs"),
                ):
                    measured = sum(b - a for a, b in intervals)
                    if abs(measured - summary["wallTimingAcceptance"][key]) > 1e-6:
                        raise ValueError(
                            "Interval reconstruction diverged from the existing timing audit"
                        )
                    for start, end in complement(intervals, duration):
                        rows.append(
                            {
                                "case": item["id"],
                                "repetition": rep,
                                "backend": backend,
                                "kind": kind,
                                "startMs": start,
                                "endMs": end,
                                "durationMs": end - start,
                            }
                        )
    with (root / "stream-uncovered-intervals.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"intervals": len(rows), "fullHorizonTotalsMatchExistingAudit": True}))
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    audit(parser.parse_args().root)
