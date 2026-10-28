"""Compare frozen CPU/GPU batches. Reference preservation is not accuracy ground truth."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from runtime import profile_summary


def statistics(values):
    return {
        "count": len(values),
        "mean": float(np.mean(values)),
        "p95": float(np.percentile(values, 95)),
        "max": max(values),
        "min": min(values),
    }


def box_iou(a, b):
    lo = np.maximum(a[:2], b[:2])
    hi = np.minimum(a[2:4], b[2:4])
    overlap = float(np.prod(np.maximum(0, hi - lo)))
    union = (
        float(np.prod(np.maximum(0, np.array(a[2:4]) - a[:2])))
        + float(np.prod(np.maximum(0, np.array(b[2:4]) - b[:2])))
        - overlap
    )
    return overlap / union if union > 0 else 0.0


def compare_rows(reference, candidate, width, height, thresholds):
    semantic = (
        "poseCount",
        "paths",
        "poseState",
        "poseReasons",
        "posture",
        "eligible",
        "candidate",
        "reasons",
        "regionState",
    )
    changed = [key for key in semantic if reference[key] != candidate[key]]
    remaining = set(range(len(candidate["boxes"])))
    box_delta = point_delta = score_delta = 0.0
    structure_changed = False
    matches = []
    if len(reference["boxes"]) != len(candidate["boxes"]):
        structure_changed = True
    for i, box in enumerate(reference["boxes"]):
        if not remaining:
            structure_changed = True
            break
        j = max(remaining, key=lambda k: box_iou(box, candidate["boxes"][k]))
        remaining.remove(j)
        overlap = box_iou(box, candidate["boxes"][j])
        matches.append({"reference": i, "candidate": j, "iou": overlap})
        box_delta = max(
            box_delta,
            float(
                np.max(
                    np.abs(np.array(box[:4]) - candidate["boxes"][j][:4])
                    * [width, height, width, height]
                )
            ),
        )
        score_delta = max(score_delta, abs(box[4] - candidate["boxes"][j][4]))
        if i >= len(reference["poses"]) or j >= len(candidate["poses"]):
            structure_changed = True
            continue
        old = {p["index"]: p for p in reference["poses"][i]["landmarks"]}
        new = {p["index"]: p for p in candidate["poses"][j]["landmarks"]}
        if set(old) != set(new):
            structure_changed = True
            continue
        for index in old:
            p, q = old[index], new[index]
            point_delta = max(
                point_delta,
                float(np.hypot((p["x"] - q["x"]) * width, (p["y"] - q["y"]) * height)),
            )
            score_delta = max(score_delta, abs(p["confidence"] - q["confidence"]))
    input_changes, raw_differences = [], []
    for i, (a, b) in enumerate(zip(reference["calls"], candidate["calls"], strict=False)):
        if a["pass"] != b["pass"] or a["inputTensorSha256"] != b["inputTensorSha256"]:
            input_changes.append(i)
            continue
        with np.load(a["rawOutputsPath"]) as old, np.load(b["rawOutputsPath"]) as new:
            row = {"pass": a["pass"]}
            for key in ("dets", "keypoints"):
                row[key] = {
                    "sameShape": old[key].shape == new[key].shape,
                    "maxAbs": float(np.max(np.abs(old[key] - new[key])))
                    if old[key].shape == new[key].shape and old[key].size
                    else None,
                }
            raw_differences.append(row)
    old_scores = reference.get("postureClassScores", [])
    new_scores = candidate.get("postureClassScores", [])
    class_structure_changed = len(old_scores) != len(new_scores)
    class_score_delta = (
        float(np.max(np.abs(np.array(old_scores) - new_scores)))
        if old_scores and not class_structure_changed
        else 0.0
    )
    structure_changed = structure_changed or class_structure_changed
    tolerance = (
        box_delta <= thresholds["boxPixelsMaxAbs"]
        and point_delta <= thresholds["pointPixelsMaxAbs"]
        and score_delta <= thresholds["scoresMaxAbs"]
        and class_score_delta <= thresholds["scoresMaxAbs"]
    )
    return {
        "changedBehaviorFields": changed,
        "bodyStructureChanged": structure_changed,
        "acceptedBoxMaxDeltaPx": box_delta,
        "bodyPointMaxDeltaPx": point_delta,
        "bodyScoreMaxDelta": score_delta,
        "postureClassScoreMaxDelta": class_score_delta,
        "withinInvestigationTolerance": tolerance,
        "sameFeedTensorInputs": not input_changes
        and len(reference["calls"]) == len(candidate["calls"]),
        "changedFeedCallIndices": input_changes,
        "nativeOutputDifferences": raw_differences,
        "boxMatchesForAssessmentOnly": matches,
        "behaviorPreserved": not changed and not structure_changed,
    }


def analyze(root):
    protocol = json.loads((root / "micro-protocol.frozen.json").read_text(encoding="utf-8"))
    batches, values = {}, defaultdict(list)
    for rep in range(1, protocol["repetitions"] + 1):
        for backend in protocol["backends"]:
            batch = json.loads(
                (root / f"micro-r{rep}-{backend}" / "result.json").read_text(encoding="utf-8")
            )
            if batch["profiling"]:
                raise ValueError("Profiling batches cannot enter timing results")
            batches[(rep, backend)] = {row["frameId"]: row for row in batch["rows"]}
            for row in batch["rows"]:
                values[(row["frameId"], backend)].append(row["fullProcessingMs"])
    differences = []
    for rep in range(1, protocol["repetitions"] + 1):
        for backend in ("cpu-matched", "directml"):
            for item in protocol["cases"]:
                ref_backend = "cpu-reference" if backend == "cpu-matched" else "cpu-matched"
                ref = batches[(rep, ref_backend)][item["id"]]
                candidate = batches[(rep, backend)][item["id"]]
                differences.append(
                    {
                        "frameId": item["id"],
                        "repetition": rep,
                        "referenceBackend": ref_backend,
                        "candidateBackend": backend,
                        **compare_rows(
                            ref,
                            candidate,
                            item["width"],
                            item["height"],
                            protocol["numericInvestigationThresholds"],
                        ),
                    }
                )
    rows = []
    for item in protocol["cases"]:
        stats = {
            backend: statistics(values[(item["id"], backend)]) for backend in protocol["backends"]
        }
        rows.append(
            {
                "frameId": item["id"],
                "case": item["case"],
                "role": item["role"],
                "statistics": stats,
                "gpuMeanLower": stats["directml"]["mean"] < stats["cpu-matched"]["mean"],
                "gpuP95NotWorse": stats["directml"]["p95"] <= stats["cpu-matched"]["p95"],
                "reductionPercent": 100
                * (1 - stats["directml"]["mean"] / stats["cpu-matched"]["mean"]),
            }
        )
    cpu_mean = sum(r["statistics"]["cpu-matched"]["mean"] for r in rows)
    gpu_mean = sum(r["statistics"]["directml"]["mean"] for r in rows)
    reduction = 100 * (1 - gpu_mean / cpu_mean)
    behavior_preserved = all(
        r["behaviorPreserved"] and r["withinInvestigationTolerance"] and r["sameFeedTensorInputs"]
        for r in differences
    )
    proof = json.loads((root / "placement-proof.json").read_text(encoding="utf-8"))
    real_gpu = profile_summary(proof["profilePath"])["gpuComputeProven"]
    gate = (
        real_gpu
        and behavior_preserved
        and reduction >= 15
        and all(r["gpuMeanLower"] and r["gpuP95NotWorse"] for r in rows)
    )
    result = {
        "scope": protocol["scope"],
        "rows": rows,
        "differences": differences,
        "aggregateReductionPercentVsMatchedCpu": reduction,
        "behaviorAndNumericPreserved": behavior_preserved,
        "gpuExecutionProfiled": real_gpu,
        "eligibleForStreamComparison": gate,
        "cameraOpened": False,
        "eventsCreated": 0,
    }
    (root / "micro-comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "cases": rows,
                "reductionPercent": reduction,
                "behaviorPreserved": behavior_preserved,
                "advance": gate,
                "maxBodyPointDeltaPx": max(r["bodyPointMaxDeltaPx"] for r in differences),
                "maxScoreDelta": max(r["bodyScoreMaxDelta"] for r in differences),
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.root)
