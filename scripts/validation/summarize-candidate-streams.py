"""Summarize saved paired streams without inference, capture or changed thresholds."""

import argparse
import csv
import json
from pathlib import Path


def summarize(root, output):
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    rows = []
    for item in plan:
        data = json.loads(
            (Path(item["output"]) / "summary.json").read_text(encoding="utf-8")
        )
        timing, metric = data["wallTimingAcceptance"], data["metrics"]
        empty = item["case"] == "intake16-15"  # Existing human-annotated empty control.
        coverage = timing["captureCoverage" if empty else "decisionCoverage"]
        times = data["stages"]["totalProcessingMs"]
        row = {
            "case": item["case"],
            "repeat": item["repeat"],
            "variant": item["variant"],
            "complete": data["complete"],
            "processingMeanMs": times["mean"],
            "processingP95Ms": times["p95"],
            "processingMaxMs": times["max"],
            "modelCallsMean": data["modelCallsPerAnalysis"]["mean"],
            "analysesPerSecond": data["effectiveSamplesPerSecond"],
            "frameAgeMaxMs": timing["maxDecisionAgeMs"],
            "decisionGapMaxMs": timing["maxDecisionHostGapMs"],
            "gapsAbove500": timing["decisionHostGapsAbove500"],
            "decisionCoverage": timing["decisionCoverage"],
            "captureCoverage": timing["captureCoverage"],
            "inconclusiveMs": timing["durationMs"] * (1 - timing["decisionCoverage"]),
            "events": data["temporal"]["generatedEvents"],
            "kinds": "|".join(e["kind"] for e in timing["events"]),
            "readyFromOriginMs": "|".join(
                str(e["readyFromSourceOriginMs"]) for e in timing["events"]
            ),
            "processCpuPercentOneCore": metric.get("processCpuPercentOneCore"),
            "peakProcessMemoryBytes": metric.get("peakProcessMemoryBytes"),
            "timingAndCoveragePassed": bool(
                data["complete"]
                and timing["timingGate"]
                and coverage >= 0.8
                and timing["maxDecisionHostGapMs"] is not None
                and timing["maxDecisionHostGapMs"] <= 500
                and timing["maxDecisionAgeMs"] <= 2000
            ),
        }
        rows.append(row)
    if output.exists():
        raise ValueError("Preserve o resumo anterior; use outro destino.")
    with output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = summarize(args.root, args.output)
    print(json.dumps({"rows": len(rows), "scope": "DEVELOPMENT_PACED_FILE_NOT_WEBCAM"}))
