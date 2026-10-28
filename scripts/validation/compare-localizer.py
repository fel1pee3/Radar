"""Single frozen detector alternative, fixed RGB pose; no events, webcam or online selector."""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from radar_edge.config import private_path
from radar_edge.pose_audit import (
    assess_anatomy,
    localization_assessment,
    native_shadow_readiness,
    pose_input_from_bgr,
    restore_box,
    restore_point,
    rotated_image,
)
from radar_edge.rtmo import COCO_TO_BODY

DETECTOR_SHA = "3dea6513388889f0fff4b77bf7a26013600321b9eb9ceb0e9a400a82572f5f23"
POSE_SHA = "9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d"


def load_models(vendor, detector_path, pose_path):
    for path, expected in ((detector_path, DETECTOR_SHA), (pose_path, POSE_SHA)):
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Only the frozen detector and unchanged pose are allowed")
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
            model_input_size=(640, 640),
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
    if detector.session.get_inputs()[0].shape != [1, 3, 640, 640]:
        raise ValueError("Candidate detector tensor shape differs")
    if pose.session.get_inputs()[0].shape[1:] != [3, 256, 192]:
        raise ValueError("Fixed pose tensor shape differs")
    return detector, pose, load_ms


def cache_module():
    path = Path(__file__).with_name("reassess-pose-cache.py")
    spec = importlib.util.spec_from_file_location("radar_reassess_cache", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compare(
    reference_path, cache_path, protocol_path, vendor, detector_path, pose_path, output
):
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if (
        hashlib.sha256(reference_path.read_bytes()).hexdigest()
        != protocol["referenceSha256"]
    ):
        raise ValueError("Reference changed after protocol freeze")
    if protocol["candidateSha256"] != DETECTOR_SHA or protocol["frames"] != list(
        reference["annotations"]
    ):
        raise ValueError("Candidate or sample differs from frozen protocol")
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    if cache["models"]["pose"] != POSE_SHA:
        raise ValueError("Cached baseline pose differs")
    output = private_path(output)
    output.mkdir(parents=True, exist_ok=False)
    helper = cache_module()
    shadow_module = helper.audit_module()
    detector, pose_model, load_ms = load_models(vendor, detector_path, pose_path)
    started = perf_counter()
    detector(np.full((640, 640, 3), 114, np.uint8))
    pose_model(np.full((256, 192, 3), 114, np.uint8), [[0, 0, 192, 256]])
    warmup_ms = (perf_counter() - started) * 1000
    rows = []
    for fid, ref in reference["annotations"].items():
        frame = ref["frame"]
        source = cv2.imread(frame["imagePath"])
        if (
            source is None
            or hashlib.sha256(source.tobytes()).hexdigest() != frame["frameSha256"]
        ):
            raise ValueError("Source pixels differ")
        height, width = source.shape[:2]
        frame["meanLuminance"] = float(cv2.cvtColor(source, cv2.COLOR_BGR2GRAY).mean())
        context = helper.classifier_context(ref)
        for repeat in (1, 2):
            angles = (0, 90, 180, 270) if repeat == 1 else (270, 180, 90, 0)
            for angle in angles:
                begun = perf_counter()
                image = rotated_image(source, angle)
                rotation_ms = (perf_counter() - begun) * 1000
                started = perf_counter()
                boxes = np.asarray(detector(image))
                detection_ms = (perf_counter() - started) * 1000
                if len(boxes) > 20 or (
                    boxes.size and (boxes.shape[1] != 4 or not np.isfinite(boxes).all())
                ):
                    raise ValueError(
                        "Unbounded or invalid native output; no boxes discarded"
                    )
                started = perf_counter()
                pose_pixels = pose_input_from_bgr(image) if len(boxes) else None
                poses, restored = [], []
                for box in boxes:
                    coordinates, scores = pose_model(pose_pixels, [box])
                    if coordinates.shape != (1, 17, 2) or scores.shape != (1, 17):
                        raise ValueError("Fixed pose output shape differs")
                    if (
                        not np.isfinite(coordinates).all()
                        or not np.isfinite(scores).all()
                    ):
                        raise ValueError("Nonfinite pose output")
                    points = {}
                    for index, target in COCO_TO_BODY.items():
                        x, y = restore_point(
                            float(coordinates[0, index, 0]),
                            float(coordinates[0, index, 1]),
                            width,
                            height,
                            angle,
                        )
                        points[target] = [
                            x / width,
                            y / height,
                            float(scores[0, index]),
                        ]
                    poses.append(points)
                    restored.append(restore_box(box, width, height, angle))
                pose_restore_ms = (perf_counter() - started) * 1000
                outputs, shadow_total = [], 0.0
                for points in poses:
                    shadow, shadow_ms = helper.shadow_from_saved(
                        points,
                        ref,
                        rotation_ms + detection_ms + pose_restore_ms,
                        context,
                        shadow_module,
                    )
                    shadow_total += shadow_ms
                    outputs.append(
                        {
                            "points": points,
                            "nativeReadiness": native_shadow_readiness(points),
                            "partialAnatomy": assess_anatomy(
                                points, ref, width, height
                            ),
                            "shadow": shadow,
                            "shadowMs": shadow_ms,
                        }
                    )
                rows.append(
                    {
                        "frameId": fid,
                        "case": frame["case"],
                        "split": frame["split"],
                        "repeat": repeat,
                        "orientation": angle,
                        "method": "YOLOX_M_HUMANART_640_FIXED",
                        "path": "A_AUTOMATIC",
                        "referenceUsedForProcessing": False,
                        "restoredBoxes": [list(map(float, b)) for b in restored],
                        "localization": localization_assessment(
                            restored, ref, width, height
                        ),
                        "poses": outputs,
                        "rotationMs": rotation_ms,
                        "detectorMs": detection_ms,
                        "poseAndRestorationMs": pose_restore_ms,
                        "shadowMs": shadow_total,
                        "perceptionMs": rotation_ms + detection_ms + pose_restore_ms,
                        "fullWithShadowMs": rotation_ms
                        + detection_ms
                        + pose_restore_ms
                        + shadow_total,
                        "detectorCalls": 1,
                        "poseCalls": len(boxes),
                        "eventsCreated": 0,
                    }
                )
                print(fid, repeat, angle, "boxes", len(boxes), flush=True)
    result = {
        "scope": "DEVELOPMENT_SINGLE_AUTOMATIC_LOCALIZER_DIAGNOSTIC",
        "baselineCacheSha256": hashlib.sha256(cache_path.read_bytes()).hexdigest(),
        "protocolSha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "models": {"detector": DETECTOR_SHA, "pose": POSE_SHA},
        "loadMs": load_ms,
        "warmupMs": warmup_ms,
        "baselineReused": True,
        "baselineCosts": "previous measured full perception costs; not a contemporary speed comparison",
        "nativeQuality": "RTMPOSE_SIMCC_SCORE; numeric .5 projection unvalidated for legacy classifier",
        "onlineOrientationPolicy": None,
        "rows": rows,
    }
    (output / "comparison.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "cache", "protocol", "vendor", "detector", "pose"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare(
        args.reference,
        args.cache,
        args.protocol,
        args.vendor,
        args.detector,
        args.pose,
        args.output,
    )
    print(
        json.dumps(
            {
                "rows": len(result["rows"]),
                "detectorCalls": sum(r["detectorCalls"] for r in result["rows"]),
                "poseCalls": sum(r["poseCalls"] for r in result["rows"]),
            }
        )
    )


if __name__ == "__main__":
    main()
