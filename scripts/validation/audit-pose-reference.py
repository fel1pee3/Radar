"""Offline A/B audit: automatic boxes vs supplied visible-body boxes, never a webcam."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from radar_edge.calibration import load_calibration
from radar_edge.config import load_config, private_path
from radar_edge.features import QualityGate, extract_features
from radar_edge.model import get_model_spec
from radar_edge.observations import Landmark, Observation, Pose, pose_quality
from radar_edge.policy import configured_policy
from radar_edge.pose_audit import (
    assess_anatomy,
    box_iou,
    native_shadow_readiness,
    pose_input_from_bgr,
    restore_box,
    restore_point,
    rotate_box,
    rotated_image,
)
from radar_edge.posture import create_posture_classifier
from radar_edge.rtmo import COCO_TO_BODY

DIGESTS = {
    "detector": "ceb11c07298f95c50d7c5abeb906d03340c85f23aa79e3e66966e7fb6c307250",
    "pose": "9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d",
}


def load_pair(vendor, detector_path, pose_path):
    for kind, path in (("detector", detector_path), ("pose", pose_path)):
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != DIGESTS[kind]
        ):
            raise ValueError("Use only the pinned local model; no automatic download")
    sys.path.insert(0, str(vendor.resolve()))
    import onnxruntime as ort
    from rtmlib import YOLOX, RTMPose

    original = ort.InferenceSession

    def session(*args, **kwargs):
        options = ort.SessionOptions()
        options.intra_op_num_threads, options.inter_op_num_threads = 4, 1
        kwargs["sess_options"] = options
        return original(*args, **kwargs)

    started = perf_counter()
    try:
        ort.InferenceSession = session
        detector = YOLOX(
            str(detector_path),
            model_input_size=(416, 416),
            backend="onnxruntime",
            device="cpu",
        )
        pose = RTMPose(
            str(pose_path),
            model_input_size=(192, 256),
            backend="onnxruntime",
            device="cpu",
            to_openpose=False,
        )
    finally:
        ort.InferenceSession = original
    load_ms = (perf_counter() - started) * 1000
    if detector.session.get_inputs()[0].shape != [1, 3, 416, 416]:
        raise ValueError("Detector tensor shape differs")
    if pose.session.get_inputs()[0].shape[1:] != [3, 256, 192]:
        raise ValueError("Pose tensor shape differs")
    return detector, pose, load_ms


def classify_shadow(
    points, item, reference, config, classifier, policy, calibration, duration
):
    readiness = native_shadow_readiness(points)
    diagnostic_ready = (
        readiness["descriptorCandidateForV3"]
        if config.posture.method == "MULTICLASS_BODY_V3"
        else readiness["readyForLegacyShadow"]
    )
    if not diagnostic_ready:
        return None
    proxy = Pose(
        tuple(
            Landmark(i, v[0], v[1], None, None, None, v[2]) for i, v in points.items()
        ),
        "RTMO_KEYPOINT_SCORE",
    )
    state, reasons = pose_quality((proxy,), 0.5)
    o = Observation(
        schemaVersion=1,
        runId="QUALIFIED_SUBSET_SHADOW_ONLY",
        cameraId=config.cameraId,
        mode="REPLAY",
        frameIndex=item["frameIndex"],
        timestampMs=item["timestampMs"],
        timestampSource="SOURCE_PTS",
        width=item["width"],
        height=item["height"],
        rotation=calibration["geometry"]["rotation"],
        poses=(proxy,),
        poseCount=1,
        inferenceState=state,
        qualityReasons=reasons,
        meanLuminance=item["meanLuminance"],
        inferenceMs=duration,
        modelId="RTMPOSE_COMPATIBILITY_DIAGNOSTIC_ONLY",
        calibrationId=calibration["calibrationId"],
        calibrationVersion=calibration["version"],
    )
    f = QualityGate(policy).apply(
        o, extract_features(o, calibration["floorPolygon"], policy)
    )
    f = classifier.classify(o, f)
    return {
        "readiness": readiness,
        "nativeScoresPreserved": True,
        "wholeBodyAnatomyValidated": False,
        "legacyClassifierScored": bool(f.postureClassScores),
        "legacyClassScores": list(f.postureClassScores),
        "legacyPartialDescriptorUsed": config.posture.method == "MULTICLASS_BODY_V3"
        and not readiness["readyForLegacyShadow"],
        "legacyCandidate": f.candidate,
        "requiresCompleteHumanReference": False,
        "eventsAuthorized": False,
        "posture": f.posture,
        "eligible": f.eligible,
        "candidate": f.candidate,
        "reasons": f.reasons,
        "regionState": f.regionState,
        "nativeScoreProjection": "UNVALIDATED_RAW_SIMCC_PROJECTION_INTO_LEGACY_ARTIFACT",
        "scoreEquivalenceAssumed": False,
        "hiddenInputsVerified": False,
        "attribution": "CONDITIONAL_DIAGNOSTIC_NOT_CERTIFIED_CLASSIFIER_ERROR",
    }


def audit(reference_path, output, vendor, detector_path, pose_path):
    reference_data = json.loads(reference_path.read_text(encoding="utf-8"))
    output = private_path(output)
    output.mkdir(parents=True, exist_ok=False)
    detector, model, load_ms = load_pair(vendor, detector_path, pose_path)
    warm = perf_counter()
    detector(np.full((416, 416, 3), 114, np.uint8))
    model(np.full((256, 192, 3), 114, np.uint8), [[0, 0, 192, 256]])
    warm_ms = (perf_counter() - warm) * 1000
    rows = []
    for fid, reference in reference_data["annotations"].items():
        item = reference["frame"]
        config = load_config(item["configPath"])
        if config.source.kind != "FILE" or not config.source.authorized:
            raise ValueError("Only authorized FILE-derived frames")
        image = cv2.imread(item["imagePath"])
        if hashlib.sha256(image.tobytes()).hexdigest() != item["frameSha256"]:
            raise ValueError("Frame bytes changed")
        height, width = image.shape[:2]
        item["meanLuminance"] = float(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).mean())
        calibration = load_calibration(config.calibrationPath)
        policy = configured_policy(config.events.policy)
        classifier = create_posture_classifier(
            config.posture, calibration, get_model_spec("rtmo-s"), policy
        )
        for repeat in (1, 2):
            angles = (0, 90, 180, 270) if repeat == 1 else (270, 180, 90, 0)
            for angle in angles:
                begun = perf_counter()
                pixels = rotated_image(image, angle)
                rotate_ms = (perf_counter() - begun) * 1000
                started = perf_counter()
                boxes = np.asarray(detector(pixels))
                detector_ms = (perf_counter() - started) * 1000
                if len(boxes) > 20:
                    raise ValueError(
                        "Too many detections; bounded audit stopped without dropping boxes"
                    )
                ref_box = None
                if reference["box"]:
                    ref_box = np.array(reference["box"]) * [
                        width,
                        height,
                        width,
                        height,
                    ]
                supplied = (
                    [rotate_box(ref_box, width, height, angle)]
                    if ref_box is not None
                    else []
                )
                for path, current_boxes in (
                    ("A_AUTOMATIC", boxes),
                    ("B_REFERENCE_BOX", supplied),
                ):
                    orders = (
                        ("LEGACY_BGR", "CORRECTED_RGB")
                        if repeat == 1
                        else ("CORRECTED_RGB", "LEGACY_BGR")
                    )
                    for channel_order in orders:
                        started = perf_counter()
                        pose_pixels = (
                            pose_input_from_bgr(pixels)
                            if channel_order == "CORRECTED_RGB"
                            else pixels
                        )
                        current_poses, restored_boxes = [], []
                        # Empty reference never triggers RTMLib's full-image fallback.
                        for box in current_boxes:
                            coords, scores = model(pose_pixels, [box])
                            if coords.shape != (1, 17, 2) or scores.shape != (1, 17):
                                raise ValueError(
                                    "Unexpected native COCO17 SimCC outputs"
                                )
                            if (
                                not np.isfinite(coords).all()
                                or not np.isfinite(scores).all()
                            ):
                                raise ValueError("Nonfinite native pose output")
                            points = {}
                            for source, target in COCO_TO_BODY.items():
                                x, y = restore_point(
                                    float(coords[0, source, 0]),
                                    float(coords[0, source, 1]),
                                    width,
                                    height,
                                    angle,
                                )
                                points[target] = [
                                    x / width,
                                    y / height,
                                    float(scores[0, source]),
                                ]
                            current_poses.append(points)
                            restored_boxes.append(
                                restore_box(box, width, height, angle)
                            )
                        pipeline_ms = (perf_counter() - started) * 1000 + rotate_ms
                        if path == "A_AUTOMATIC":
                            pipeline_ms += detector_ms
                        anatomical = [
                            assess_anatomy(points, reference, width, height)
                            for points in current_poses
                        ]
                        ious = (
                            [box_iou(box, ref_box) for box in restored_boxes]
                            if ref_box is not None
                            else []
                        )
                        shadow = [
                            classify_shadow(
                                points,
                                item,
                                reference,
                                config,
                                classifier,
                                policy,
                                calibration,
                                pipeline_ms,
                            )
                            for points in current_poses
                        ]
                        row = {
                            "frameId": fid,
                            "case": item["case"],
                            "split": item["split"],
                            "timestampMs": item["timestampMs"],
                            "referenceStatus": reference["status"],
                            "repeat": repeat,
                            "orientation": angle,
                            "path": path,
                            "channelOrder": channel_order,
                            "automaticLocalization": path == "A_AUTOMATIC",
                            "referenceUsedForAssociationOnly": path == "A_AUTOMATIC",
                            "pipelineMs": pipeline_ms,
                            "detectorMs": detector_ms if path == "A_AUTOMATIC" else 0,
                            "detectorCalls": int(path == "A_AUTOMATIC"),
                            "poseCalls": len(current_boxes),
                            "detections": len(boxes) if path == "A_AUTOMATIC" else None,
                            "restoredBoxes": [
                                list(map(float, b)) for b in restored_boxes
                            ],
                            "referenceBoxIoUs": ious,
                            "poses": current_poses,
                            "anatomy": anatomical,
                            "shadowClassifier": shadow,
                            "expectedPosture": reference["posture"],
                            "effectiveVisiblePeople": reference["count"],
                            "eventsGenerated": False,
                            "orientationSelection": "COUNTERFACTUAL_ONLY_NO_ORACLE_ONLINE_POLICY",
                        }
                        rows.append(row)
                print(fid, repeat, angle, "boxes", len(boxes), flush=True)
    result = {
        "scope": "DEVELOPMENT_ANNOTATED_DRAFT_NOT_INDEPENDENT",
        "referenceSha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "models": DIGESTS,
        "loadMs": load_ms,
        "warmupMs": warm_ms,
        "nativeQualitySource": "RTMPOSE_SIMCC_SCORE_NOT_VISIBILITY",
        "rows": rows,
    }
    (output / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--vendor", type=Path, required=True)
    parser.add_argument("--detector", type=Path, required=True)
    parser.add_argument("--pose", type=Path, required=True)
    args = parser.parse_args()
    audit(args.reference, args.output, args.vendor, args.detector, args.pose)


if __name__ == "__main__":
    main()
