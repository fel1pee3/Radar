"""Compare event behavior and same-media decision traces; retain historical failures."""

import argparse
import csv
import json
from math import hypot
from pathlib import Path


def decisions(result):
    report = json.loads(Path(result["reportPath"]).read_text(encoding="utf-8"))
    return {
        r["timestampMs"]: r
        for line in Path(report["decisionExport"]["path"]).read_text(encoding="utf-8").splitlines()
        if (r := json.loads(line))["recordType"] == "DECISION"
    }


def compare(root):
    protocol = json.loads((root / "functional-protocol.frozen.json").read_text(encoding="utf-8"))
    rows = []
    for item in protocol["cases"]:
        results = {
            backend: json.loads(
                (root / "functional" / backend / item["id"] / "evaluation.json").read_text(
                    encoding="utf-8"
                )
            )
            for backend in ("cpu-reference", "directml")
        }
        reference, gpu = results["cpu-reference"], results["directml"]
        traces = {backend: decisions(result) for backend, result in results.items()}
        shared = set(traces["cpu-reference"]) & set(traces["directml"])
        fields = (
            "inferenceState",
            "posture",
            "quality",
            "decisionReasons",
            "criteria",
            "temporalAfter",
        )
        numeric_max_px = numeric_max_score = 0.0
        numeric_outliers = []
        width = reference["source"]["geometry"]["width"]
        height = reference["source"]["geometry"]["height"]
        for timestamp in shared:
            qa = traces["cpu-reference"][timestamp]["quality"]
            qb = traces["directml"][timestamp]["quality"]
            points_a = {p["index"]: p for p in qa.get("essential", [])}
            points_b = {p["index"]: p for p in qb.get("essential", [])}
            pixel_delta = score_delta = 0.0
            for index in points_a.keys() & points_b.keys():
                a, b = points_a[index], points_b[index]
                if all(isinstance(p.get(k), (int, float)) for p in (a, b) for k in ("x", "y")):
                    pixel_delta = max(
                        pixel_delta, hypot((a["x"] - b["x"]) * width, (a["y"] - b["y"]) * height)
                    )
                if all(isinstance(p.get("score"), (int, float)) for p in (a, b)):
                    score_delta = max(score_delta, abs(a["score"] - b["score"]))
            numeric_max_px = max(numeric_max_px, pixel_delta)
            numeric_max_score = max(numeric_max_score, score_delta)
            if pixel_delta > 1 or score_delta > 0.005:
                numeric_outliers.append(
                    {"timestampMs": timestamp, "maxPointPx": pixel_delta, "maxScore": score_delta}
                )
        for trace in traces.values():
            for record in trace.values():
                record["perceptionPasses"] = record["perception"]["passes"]
                record["quality"] = {
                    **{k: v for k, v in record["quality"].items() if k != "essential"},
                    "essential": [
                        {k: v for k, v in p.items() if k not in ("x", "y", "score")}
                        for p in record["quality"].get("essential", [])
                    ],
                }
        fields += ("perceptionPasses",)
        changed = [
            {
                "timestampMs": t,
                "fields": [
                    f for f in fields if traces["cpu-reference"][t][f] != traces["directml"][t][f]
                ],
            }
            for t in sorted(shared)
            if any(traces["cpu-reference"][t][f] != traces["directml"][t][f] for f in fields)
        ]

        def event_signature(result):
            return [(e["kind"], e["sourceOffsetMs"]) for e in result["temporal"]["events"]]

        row = {
            "case": item["id"],
            "cpuApproved": reference["score"]["approved"],
            "gpuApproved": gpu["score"]["approved"],
            "cpuMissed": reference["score"]["missed"],
            "gpuMissed": gpu["score"]["missed"],
            "cpuNegative": reference["score"]["negativeResult"],
            "gpuNegative": gpu["score"]["negativeResult"],
            "cpuCoverage": reference["score"]["eligibleFraction"],
            "gpuCoverage": gpu["score"]["eligibleFraction"],
            "cpuEvents": event_signature(reference),
            "gpuEvents": event_signature(gpu),
            "eventSignaturePreserved": event_signature(reference) == event_signature(gpu),
            "sameAnalyzedTimestamps": set(traces["cpu-reference"]) == set(traces["directml"]),
            "changedDecisionCount": len(changed),
            "changedDecisions": changed,
            "maxEssentialPointDeltaPx": numeric_max_px,
            "maxEssentialScoreDelta": numeric_max_score,
            "numericOutliers": numeric_outliers,
            "cpuDuplicates": reference["score"]["duplicates"],
            "gpuDuplicates": gpu["score"]["duplicates"],
            "cpuUnexpected": reference["score"]["unmatchedAlerts"],
            "gpuUnexpected": gpu["score"]["unmatchedAlerts"],
            "cpuUnjustifiedTransitions": reference["score"]["unjustifiedTransitionAlerts"],
            "gpuUnjustifiedTransitions": gpu["score"]["unjustifiedTransitionAlerts"],
        }
        rows.append(row)
    result = {
        "scope": protocol["scope"],
        "rows": rows,
        "cpuApproved": sum(r["cpuApproved"] for r in rows),
        "gpuApproved": sum(r["gpuApproved"] for r in rows),
        "newApprovalRegressions": [
            r["case"] for r in rows if r["cpuApproved"] and not r["gpuApproved"]
        ],
        "changedEventCases": [r["case"] for r in rows if not r["eventSignaturePreserved"]],
        "changedDecisionCases": [r["case"] for r in rows if r["changedDecisionCount"]],
        "numericOutlierCases": [r["case"] for r in rows if r["numericOutliers"]],
        "historicalLossesRetained": [
            r for r in rows if r["case"] in ("floor03", "floor05", "floor07", "controlled-lying")
        ],
        "historicalInconclusiveRetained": [
            r for r in rows if r["case"] in ("cauca-10", "chair08-01")
        ],
        "notIndependentOrRealtimeEvaluation": True,
    }
    (root / "functional-comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (root / "functional-comparison.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[k for k in rows[0] if k not in ("changedDecisions", "numericOutliers")],
        )
        writer.writeheader()
        writer.writerows(
            {k: v for k, v in r.items() if k not in ("changedDecisions", "numericOutliers")}
            for r in rows
        )
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "cpuApproved",
                    "gpuApproved",
                    "newApprovalRegressions",
                    "changedEventCases",
                    "changedDecisionCases",
                )
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    compare(parser.parse_args().root)
