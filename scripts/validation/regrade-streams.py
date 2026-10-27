"""Regrade preserved stabilization artifacts, without inference or source mutation."""

import argparse
import json
from collections import Counter
from pathlib import Path

from radar_edge.stream_acceptance import assess_stream_timing


def regrade(root, output):
    output.mkdir(parents=True, exist_ok=False)
    previous = json.loads((root / "analysis.json").read_text())
    rows = []
    for row in previous["rows"]:
        detail = next(
            d
            for d in previous["details"]
            if d["case"] == row["case"]
            and d["rep"] == row["repeat"]
            and d["variant"] == row["variant"]
        )
        s = json.loads(Path(detail["summary"]).read_text())
        report = json.loads(Path(s["reportPath"]).read_text())
        records = [
            json.loads(line)
            for line in Path(report["decisionExport"]["path"]).read_text().splitlines()
        ]
        duration = s["source"]["durationMsEstimate"]
        audit = assess_stream_timing(
            records, duration, s["source"]["hostMonotonicOriginNs"]
        )
        numerator = (
            audit["timelyCaptureEligibleMs"]
            if row["case"] == "intake16-15"
            else audit["timelyEligibleMediaMs"]
        )
        coverage = numerator / duration
        latencies = (
            [e["readyFromSourceOriginMs"] for e in audit["events"]]
            if row["case"] in {"yoga2-01", "yoga2-02", "intake16-03"}
            else []
        )
        rows.append(
            {
                "case": row["case"],
                "repeat": row["repeat"],
                "method": row["variant"],
                "oldApproved": row["approved"],
                "oldCoverage": row["captureEligiblePercent"] / 100
                if row["case"] == "intake16-15"
                else row["eligiblePercent"] / 100,
                "coverage": coverage,
                "wallLatenciesMs": latencies,
                "approved": bool(
                    row["approved"]
                    and audit["timingGate"]
                    and coverage >= 0.8
                    and all(t <= 5000 for t in latencies)
                ),
                "audit": audit,
            }
        )
    functional = []
    for f in sorted((root / "full-matrix").glob("*/*/evaluation.json")):
        s = json.loads(f.read_text())
        old = s["score"]
        duration = s["source"]["durationMsEstimate"]
        numerator = (
            old["eligibleMs"]
            if old["negativeExpectedPerson"] or old["targets"]
            else s["temporal"]["captureEligibleMs"]
        )
        functional.append(
            {
                "case": s["id"],
                "method": s["method"],
                "oldApproved": old["approved"],
                "oldCoverage": old["eligibleFraction"]
                if old["negativeExpectedPerson"] or old["targets"]
                else old["negativeObservationCoverage"],
                "coverage": numerator / duration,
                "approved": bool(old["approved"] and numerator / duration >= 0.8),
                "scope": "FILE_MEDIA_ONLY_NOT_REALTIME",
            }
        )
    result = {"streams": rows, "functional": functional}
    (output / "regraded.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    for label, data in (("streams", rows), ("functional", functional)):
        counts = Counter()
        for row in data:
            counts[(row["method"], "old")] += row["oldApproved"]
            counts[(row["method"], "new")] += row["approved"]
        print(label, {str(k): v for k, v in counts.items()})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    regrade(args.experiment_root, args.output)
