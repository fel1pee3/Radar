"""Full-horizon host-clock audit of frozen sequential FILE stream comparisons."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def stats(values):
    values = [x for x in values if x is not None]
    return {
        "n": len(values),
        "mean": float(np.mean(values)) if values else None,
        "p95": float(np.percentile(values, 95)) if values else None,
        "max": max(values) if values else None,
    }


def summarize(root):
    protocol = json.loads((root / "stream-protocol.frozen.json").read_text(encoding="utf-8"))
    rows, pooled = [], defaultdict(lambda: defaultdict(list))
    path_counts = defaultdict(Counter)
    posture_counts = defaultdict(Counter)
    reasons = defaultdict(Counter)
    for repetition in range(1, len(protocol["orders"]) + 1):
        for backend in protocol["python"]:
            for item in protocol["cases"]:
                directory = root / f"stream-r{repetition}-{backend}-{item['id']}"
                summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
                report = json.loads(Path(summary["reportPath"]).read_text(encoding="utf-8"))
                records = [
                    json.loads(line)
                    for line in Path(report["decisionExport"]["path"])
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                decisions = [r for r in records if r["recordType"] == "DECISION"]
                profiles = [r for r in records if r["recordType"] == "PROCESSING_PROFILE"]
                audit, resource = summary["wallTimingAcceptance"], summary["experimentalExecutor"]
                key = (item["id"], backend)
                calls = []
                for record in decisions:
                    attempts = record["perception"]["attempts"]
                    count = sum(not a.get("skippedReason") for a in attempts)
                    calls.append(count)
                    path_counts[key].update(
                        a["pass"] for a in attempts if not a.get("skippedReason")
                    )
                    posture = record.get("posture", {})
                    posture_counts[key].update(
                        [
                            posture.get("label", posture.get("posture", "NOT_EXPORTED"))
                            if isinstance(posture, dict)
                            else str(posture)
                        ]
                    )
                    reasons[key].update(record.get("quality", {}).get("reasons", []))
                coverage = (
                    audit["captureCoverage"]
                    if item["scene"] == "negative" and item["id"] == "intake16-15"
                    else audit["decisionCoverage"]
                )
                events = audit["events"]
                positive = item["scene"] == "positive-already-lying"
                latency = (
                    [e["readyFromSourceOriginMs"] - item["positiveStartMs"] for e in events]
                    if positive
                    else []
                )
                duplicate = max(0, len(events) - 1) if positive else 0
                false_alerts = len(events) if not positive else 0
                passed = (
                    summary["complete"]
                    and audit["timingGate"]
                    and coverage >= 0.8
                    and audit["unobservedHeadMs"] <= 500
                    and audit["unobservedTailMs"] <= 500
                    and (len(events) == 1 and latency[0] <= 5000 if positive else not events)
                    and not duplicate
                    and not false_alerts
                )
                processing = [p["totalProcessingMs"] for p in profiles]
                inference = [p["inferenceMs"] for p in profiles]
                row = {
                    "case": item["id"],
                    "repetition": repetition,
                    "backend": backend,
                    "complete": summary["complete"],
                    "decisions": len(decisions),
                    "processingMeanMs": stats(processing)["mean"],
                    "processingP95Ms": stats(processing)["p95"],
                    "processingMaxMs": stats(processing)["max"],
                    "callsMean": stats(calls)["mean"],
                    "sourceCadence": summary["effectiveSamplesPerSecond"],
                    "hostGapsAbove500": audit["decisionHostGapsAbove500"],
                    "maxHostGapMs": audit["maxDecisionHostGapMs"],
                    "maxDecisionAgeMs": audit["maxDecisionAgeMs"],
                    "staleDecisions": audit["staleDecisions"],
                    "missingTimings": audit["missingTimingDecisions"],
                    "negativeStartAges": audit["negativeStartAgesRecorded"],
                    "decisionCoverage": audit["decisionCoverage"],
                    "captureCoverage": audit["captureCoverage"],
                    "acceptanceCoverage": coverage,
                    "inconclusiveDecisionMs": audit["durationMs"] - audit["timelyEligibleMediaMs"],
                    "unobservedHeadMs": audit["unobservedHeadMs"],
                    "unobservedTailMs": audit["unobservedTailMs"],
                    "events": len(events),
                    "eventKinds": ",".join(e["kind"] for e in events),
                    "wallLatencyMs": min(latency) if latency else None,
                    "missed": int(positive and not events),
                    "duplicates": duplicate,
                    "falseAlerts": false_alerts,
                    "cpuMachinePercent": resource["machineNormalizedCpuPercent"],
                    "peakWorkingSetMiB": resource["memoryAfter"]["peakWorkingSetBytes"] / 2**20,
                    "initializationMs": resource["sessions"][0]["initializationMs"],
                    "warmupMs": summary["warmupSyntheticExcludedMs"],
                    "approvedTechnicalScene": bool(passed),
                    "report": summary["reportPath"],
                }
                rows.append(row)
                pooled[key]["processing"].extend(processing)
                pooled[key]["inference"].extend(inference)
                pooled[key]["calls"].extend(calls)
                for timing in (
                    "frameAgeAtAnalysisStartMs",
                    "frameAgeAfterInferenceMs",
                    "capturedFrameAgeAtDecisionMs",
                ):
                    pooled[key][timing].extend(d.get("timing", {}).get(timing) for d in decisions)
                for p in profiles:
                    for name in ("observationPreparationMs", "runtimeAndMetricsMs", "previewMs"):
                        pooled[key][name].append(p[name])
                    for attempt in p["attempts"]:
                        if not attempt.get("skippedReason"):
                            for name in ("prepareMs", "sessionRunMs", "decodeMs", "restoreMs"):
                                pooled[key][name].append(attempt.get(name))
    aggregates = []
    for (case, backend), values in pooled.items():
        selected = [r for r in rows if r["case"] == case and r["backend"] == backend]
        aggregates.append(
            {
                "case": case,
                "backend": backend,
                "statistics": {k: stats(v) for k, v in values.items()},
                "pathCalls": dict(path_counts[(case, backend)]),
                "postureLabels": dict(posture_counts[(case, backend)]),
                "qualityReasons": dict(reasons[(case, backend)]),
                "approvedRuns": sum(r["approvedTechnicalScene"] for r in selected),
                "runs": len(selected),
                "worstAcceptanceCoverage": min(r["acceptanceCoverage"] for r in selected),
                "totalGapsAbove500": sum(r["hostGapsAbove500"] for r in selected),
                "latenciesMs": [
                    r["wallLatencyMs"] for r in selected if r["wallLatencyMs"] is not None
                ],
                "meanCpuMachinePercent": float(np.mean([r["cpuMachinePercent"] for r in selected])),
                "maxPeakWorkingSetMiB": max(r["peakWorkingSetMiB"] for r in selected),
                "missed": sum(r["missed"] for r in selected),
                "falseAlerts": sum(r["falseAlerts"] for r in selected),
                "duplicates": sum(r["duplicates"] for r in selected),
            }
        )
    result = {"scope": protocol["scope"], "rows": rows, "aggregates": aggregates}
    (root / "stream-comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (root / "stream-comparison.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            {
                "summaries": [
                    {
                        k: a[k]
                        for k in (
                            "case",
                            "backend",
                            "approvedRuns",
                            "worstAcceptanceCoverage",
                            "totalGapsAbove500",
                            "latenciesMs",
                        )
                    }
                    for a in aggregates
                ]
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    summarize(parser.parse_args().root)
