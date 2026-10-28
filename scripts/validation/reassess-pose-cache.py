"""Reassess saved RGB outputs with a partial reference; never invoke an estimator."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from time import perf_counter

import cv2
from radar_edge.calibration import load_calibration
from radar_edge.config import load_config, private_path
from radar_edge.model import get_model_spec
from radar_edge.policy import configured_policy
from radar_edge.pose_audit import (
    assess_anatomy,
    localization_assessment,
    native_shadow_readiness,
)
from radar_edge.posture import create_posture_classifier


def audit_module():
    path = Path(__file__).with_name("audit-pose-reference.py")
    spec = importlib.util.spec_from_file_location("radar_offline_pose_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classifier_context(reference):
    config = load_config(reference["frame"]["configPath"])
    if config.source.kind != "FILE" or not config.source.authorized:
        raise ValueError("Only existing authorized FILE references")
    calibration = load_calibration(config.calibrationPath)
    policy = configured_policy(config.events.policy)
    classifier = create_posture_classifier(
        config.posture, calibration, get_model_spec("rtmo-s"), policy
    )
    return config, calibration, policy, classifier


def shadow_from_saved(points, reference, milliseconds, context, module):
    config, calibration, policy, classifier = context
    started = perf_counter()
    result = module.classify_shadow(
        points,
        reference["frame"],
        reference,
        config,
        classifier,
        policy,
        calibration,
        milliseconds,
    )
    return result, (perf_counter() - started) * 1000


def reassess(reference_path, cache_path, cache_reference_path, output):
    reference_data = json.loads(reference_path.read_text(encoding="utf-8"))
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    source_reference = json.loads(cache_reference_path.read_text(encoding="utf-8"))
    if (
        hashlib.sha256(cache_reference_path.read_bytes()).hexdigest()
        != cache["referenceSha256"]
    ):
        raise ValueError("Cached reference identity differs")
    if (
        cache["models"]["detector"]
        != "ceb11c07298f95c50d7c5abeb906d03340c85f23aa79e3e66966e7fb6c307250"
    ):
        raise ValueError("Cached baseline detector differs")
    expected = "9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d"
    if cache["models"]["pose"] != expected:
        raise ValueError("Cached pose model differs; refuse to reuse")
    output = private_path(output)
    output.mkdir(parents=True, exist_ok=False)
    module = audit_module()
    contexts = {}
    for fid, ref in reference_data["annotations"].items():
        original_frame = source_reference["annotations"][fid]["frame"]
        for key in ("frameSha256", "timestampMs", "width", "height", "videoSha256"):
            if original_frame[key] != ref["frame"][key]:
                raise ValueError("Cached frame identity or geometry differs")
        image = cv2.imread(ref["frame"]["imagePath"])
        if (
            image is None
            or hashlib.sha256(image.tobytes()).hexdigest()
            != ref["frame"]["frameSha256"]
        ):
            raise ValueError("Pixels differ; cached outputs cannot be reused")
        ref["frame"]["meanLuminance"] = float(
            cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).mean()
        )
        contexts[fid] = classifier_context(ref)
    rows = []
    for original in cache["rows"]:
        if original["channelOrder"] != "CORRECTED_RGB":
            continue
        fid = original["frameId"]
        reference = reference_data["annotations"][fid]
        if original["orientation"] not in (0, 90, 180, 270):
            raise ValueError("Cached transform is unsupported")

        width, height = reference["frame"]["width"], reference["frame"]["height"]
        if original["timestampMs"] != reference["frame"]["timestampMs"]:
            raise ValueError("Cached frame timestamp differs")
        poses = []
        for index, values in enumerate(original["poses"]):
            points = {int(key): value for key, value in values.items()}
            native = native_shadow_readiness(points)
            anatomy = assess_anatomy(points, reference, width, height)
            shadow, shadow_ms = shadow_from_saved(
                points, reference, original["pipelineMs"], contexts[fid], module
            )
            old = original["anatomy"][index]
            old_groups = sorted({d["group"] for d in old["details"]})
            old_missing = len(old_groups) != 4
            cause = (
                (
                    "B_MISSING_HUMAN_GROUPS"
                    if old_missing
                    else "B_INVALIDATED_ALIGNMENT_REQUIREMENT"
                )
                if native["readyForLegacyShadow"]
                else (
                    "C_NUMERIC_AND_MISSING_HUMAN_GROUPS"
                    if old_missing
                    else "A_NUMERIC_QUALITY"
                )
            )

            poses.append(
                {
                    "nativeReadiness": native,
                    "partialAnatomy": anatomy,
                    "oldAnatomyGate": old["qualifiedVisibleSubset"],
                    "oldHumanGroups": old_groups,
                    "oldMissingHumanGroups": old_missing,
                    "oldProbeBlockAudit": cause,
                    "oldAlignmentMetricInvalid": True,
                    "oldNoProbeCause": "REFERENCE_GATE_ONLY"
                    if native["readyForLegacyShadow"]
                    else "NUMERIC_QUALITY_AND_REFERENCE_GATE",
                    "shadow": shadow,
                    "shadowMs": shadow_ms,
                    "expectedPosture": reference["posture"],
                    "anatomicalCausationNotEstablished": True,
                }
            )
        rows.append(
            {
                "frameId": fid,
                "case": original["case"],
                "path": original["path"],
                "repeat": original["repeat"],
                "orientation": original["orientation"],
                "localization": localization_assessment(
                    original["restoredBoxes"], reference, width, height
                )
                if original["path"] == "A_AUTOMATIC"
                else None,
                "manualBoxProvided": original["path"] == "B_REFERENCE_BOX",
                "savedInputBoxes": original["restoredBoxes"],
                "providedBoxesReference": "ORIGINAL_CACHE_REFERENCE_NOT_REPLACED_OR_RERUN",
                "poses": poses,
                "originalPipelineMs": original["pipelineMs"],
                "originalPreviousPCKInvalid": True,
                "humanReferenceStatus": reference_data["humanReviewStatus"],
                "allHumanJointsAvailable": False,
                "postureComparisonAvailable": reference["posture"] != "EMPTY",
                "estimatorCallsThisReassessment": 0,
            }
        )
    result = {
        "scope": "DEVELOPMENT_CACHED_RGB_PARTIAL_REFERENCE_SHADOW_ONLY",
        "cacheSha256": hashlib.sha256(cache_path.read_bytes()).hexdigest(),
        "referenceSha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "referenceStatus": reference_data["humanReviewStatus"],
        "estimatorCalls": 0,
        "eventsCreated": 0,
        "fullBodyAccuracyMeasured": False,
        "previousPCKStillInvalid": True,
        "rows": rows,
    }
    (output / "reassessment.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--cache-reference", type=Path, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = reassess(args.reference, args.cache, args.cache_reference, args.output)
    probes = sum(
        p["shadow"] is not None for row in result["rows"] for p in row["poses"]
    )
    print(
        json.dumps(
            {"rows": len(result["rows"]), "shadowProbes": probes, "estimatorCalls": 0}
        )
    )


if __name__ == "__main__":
    main()
