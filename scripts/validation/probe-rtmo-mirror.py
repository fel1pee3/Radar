"""Finite current-frame RTMO mirror ablation. No events, HTTP, camera or images saved.

The input protocol and selection must be private frozen JSON files. Selection:
{"frames": [{"caseId": "case-id", "frameIndex": 12, "timestampMs": 400}]}
Only caseId/frameIndex are required; optional timestampMs/frameSha256 are checked.
The estimator and all acceptance thresholds are the existing production ones.
"""

import argparse
import copy
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/edge/src"))

import cv2  # noqa: E402
from radar_edge.config import load_config, private_path  # noqa: E402
from radar_edge.directml import DirectMlEstimator  # noqa: E402
from radar_edge.observations import ESSENTIAL, Pose, point_usable  # noqa: E402
from radar_edge.rtmo import DETECTION_THRESHOLD, NMS_THRESHOLD, RtmoEstimator  # noqa: E402
from radar_edge.source import FileSource  # noqa: E402

MIRROR_BODY_PAIRS = ((11, 12), (13, 14), (15, 16), (23, 24), (25, 26), (27, 28))
MIRROR_BODY_INDEX = {left: right for left, right in MIRROR_BODY_PAIRS} | {
    right: left for left, right in MIRROR_BODY_PAIRS
}
MAX_FRAMES = 12


def digest_file(filename):
    with Path(filename).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore_mirror(poses, boxes, width):
    """Pixel-center inverse and anatomical flip-pair exchange; no clamping.

    RTMO normalization divides pixel coordinates by width (not width-1), so a
    reflected x maps to (width-1)/width - x. Scores and all other data are kept.
    """
    if type(width) is not int or width <= 0:
        raise ValueError("Expected positive integer frame width")
    edge = (width - 1) / width
    restored = tuple(
        Pose(
            tuple(
                sorted(
                    (
                        replace(
                            point,
                            index=MIRROR_BODY_INDEX.get(point.index, point.index),
                            x=edge - point.x,
                        )
                        for point in pose.landmarks
                    ),
                    key=lambda point: point.index,
                )
            ),
            pose.qualitySource,
        )
        for pose in poses
    )
    restored_boxes = tuple((edge - b[2], b[1], edge - b[0], b[3], b[4]) for b in boxes)
    return restored, restored_boxes


def usable_per_pose(poses):
    return [
        sum(
            point.index in ESSENTIAL
            and point_usable(point, 0.5, pose.qualitySource)
            and 0 <= point.x <= 1
            and 0 <= point.y <= 1
            for point in pose.landmarks
        )
        for pose in poses
    ]


def observation_result(poses, boxes, score, attempts, passes, elapsed_ms):
    return {
        "poseCount": len(poses),
        "poses": [asdict(pose) for pose in poses],
        "personDetections": boxes,
        "acceptedPersonScores": [box[4] for box in boxes],
        "topPersonProposalScore": score,
        "usableEssentialCount": RtmoEstimator.valid_essential(poses),
        "usableEssentialsPerPose": usable_per_pose(poses),
        "singlePoseWithEightEssentials": len(poses) == 1
        and RtmoEstimator.valid_essential(poses) == 8,
        "modelCalls": sum("sessionRunMs" in attempt for attempt in attempts),
        "perceptionPasses": passes,
        "perceptionAttempts": attempts,
        "elapsedMs": elapsed_ms,
        "acceptanceScope": (
            "Existing person threshold 0.7 and keypoint score 0.5; no temporal decision"
        ),
    }


def read_json(filename):
    return json.loads(Path(filename).read_text(encoding="utf-8-sig"))


def validate_inputs(protocol_path, selection_path):
    protocol = read_json(private_path(protocol_path))
    selection = read_json(private_path(selection_path))
    entries = selection.get("frames") if isinstance(selection, dict) else selection
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FRAMES:
        raise ValueError("Select 1 to 12 distinct recorded FILE frames")
    cases = {case["id"]: case for case in protocol["cases"]}
    if len(cases) != len(protocol["cases"]):
        raise ValueError("Duplicate protocol case identity")
    grouped, configs = defaultdict(list), {}
    identities = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each selection entry must identify one recorded frame")
        case_id, index = entry.get("caseId"), entry.get("frameIndex")
        if not isinstance(case_id, str) or case_id not in cases:
            raise ValueError("Unknown protocol case")
        if type(index) is not int or index < 0 or (case_id, index) in identities:
            raise ValueError("Invalid or duplicate exact frame index")
        identities.add((case_id, index))
        grouped[case_id].append(entry)
    for case_id in grouped:
        item = cases[case_id]
        for filename, expected in item["preservedFiles"].items():
            if digest_file(filename) != expected:
                raise ValueError("Frozen protocol input changed")
        config = load_config(item["config"])
        if config.source.kind != "FILE" or not config.source.authorized:
            raise ValueError("Only explicitly authorized FILE; never webcam")
        if (
            config.model.variant != "rtmo-s"
            or config.model.recovery != "RTMO_ADAPTIVE_V3"
        ):
            raise ValueError("Preserve the RTMO V3 reference estimator")
        if config.model.runtimeProfile != "REFERENCE_4_SPIN":
            raise ValueError("Preserve REFERENCE_4_SPIN")
        if config.processing.minKeypointScore != 0.5:
            raise ValueError("Preserve the existing 0.5 keypoint score threshold")
        actual = digest_file(config.source.path)
        if item.get("videoSha256") != actual:
            raise ValueError("Video does not match the frozen protocol hash")
        configs[case_id] = config
    return protocol, grouped, configs


def execute(protocol_path, selection_path, output):
    protocol, grouped, configs = validate_inputs(protocol_path, selection_path)
    output = private_path(output)
    if output.exists():
        raise ValueError("Use a new output folder; previous evidence is preserved")
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "schemaVersion": 1,
        "scope": "FINITE_DEVELOPMENT_MIRROR_ABLATION_NOT_TEMPORAL_OR_INDEPENDENT",
        "pythonVersion": sys.version,
        "pythonExecutable": sys.executable,
        "cameraOpened": False,
        "httpSent": False,
        "eventsGenerated": 0,
        "imagesSaved": False,
        "absenceDoesNotConfirmEmptyScene": True,
        "maxSelectedFrames": MAX_FRAMES,
        "detectorThreshold": DETECTION_THRESHOLD,
        "keypointThreshold": 0.5,
        "nmsThreshold": NMS_THRESHOLD,
        "protocolSha256": digest_file(protocol_path),
        "selectionSha256": digest_file(selection_path),
        "protocolScope": protocol.get("scope"),
        "restoration": (
            "x=(width-1)/width-x; anatomical flip-pairs; "
            "no clamping or synthetic joints"
        ),
        "sessions": [],
        "frames": [],
        "complete": False,
    }
    with (output / "frames.jsonl").open("x", encoding="utf-8") as records:
        for position, (case_id, entries) in enumerate(grouped.items()):
            config = configs[case_id]
            requested = {entry["frameIndex"]: entry for entry in entries}
            source_hash = digest_file(config.source.path)
            profile_prefix = str(output / ("ort-case-" + str(position)))
            estimator = DirectMlEstimator(
                config.model.path,
                "RTMO_ADAPTIVE_V3",
                "REFERENCE_4_SPIN",
                device_id=config.model.deviceId,
                profile_prefix=profile_prefix,
            )
            with (
                FileSource(config.source, config.processing.maxWidth) as source,
                estimator,
            ):
                while requested:
                    frame = source.read()
                    if frame is None:
                        raise ValueError(
                            "Exact selected frame was not found before verified EOF"
                        )
                    if frame.index not in requested:
                        continue
                    selected = requested.pop(frame.index)
                    frame_hash = hashlib.sha256(frame.bgr.tobytes()).hexdigest()
                    if (
                        "timestampMs" in selected
                        and selected["timestampMs"] != frame.timestamp_ms
                    ):
                        raise ValueError("Selected frame timestamp changed")
                    if (
                        "frameSha256" in selected
                        and selected["frameSha256"] != frame_hash
                    ):
                        raise ValueError("Selected frame pixels changed")
                    poses, baseline_ms = estimator.estimate(frame)
                    baseline = observation_result(
                        poses,
                        estimator.person_detections,
                        estimator.person_proposal_score,
                        copy.deepcopy(estimator.perception_attempts),
                        estimator.perception_passes,
                        baseline_ms,
                    )
                    estimator.perception_attempts = []
                    mirror_start = perf_counter()
                    flipped = cv2.flip(frame.bgr, 1)
                    flipped_at = perf_counter()
                    mirror_poses, mirror_boxes, mirror_score = estimator.infer_image(
                        flipped
                    )
                    inferred_at = perf_counter()
                    mirror_poses, mirror_boxes = restore_mirror(
                        mirror_poses, mirror_boxes, frame.bgr.shape[1]
                    )
                    restored_at = perf_counter()
                    attempts = copy.deepcopy(estimator.perception_attempts)
                    if len(attempts) != 1 or "sessionRunMs" not in attempts[0]:
                        raise RuntimeError(
                            "The mirror ablation must make exactly one current inference"
                        )
                    attempts[0]["pass"] = "HORIZONTAL_MIRROR_SINGLE"
                    mirrored = observation_result(
                        mirror_poses,
                        mirror_boxes,
                        mirror_score,
                        attempts,
                        ("HORIZONTAL_MIRROR_SINGLE",),
                        (restored_at - mirror_start) * 1000,
                    )
                    mirrored.update(
                        {
                            "flipMs": (flipped_at - mirror_start) * 1000,
                            "inferenceAndDecodeMs": (inferred_at - flipped_at) * 1000,
                            "restoreMs": (restored_at - inferred_at) * 1000,
                        }
                    )
                    row = {
                        "caseId": case_id,
                        "frameIndex": frame.index,
                        "timestampMs": frame.timestamp_ms,
                        "timestampSource": frame.timestamp_source,
                        "videoSha256": source_hash,
                        "frameSha256": frame_hash,
                        "mirroredFrameSha256": hashlib.sha256(
                            flipped.tobytes()
                        ).hexdigest(),
                        "geometry": asdict(frame.geometry),
                        "baseline": baseline,
                        "mirror": mirrored,
                        "observationOrigin": "REAL_INFERENCE_ON_THE_SELECTED_CURRENT_PIXELS",
                    }
                    result["frames"].append(row)
                    records.write(json.dumps(row, allow_nan=False) + "\n")
                    records.flush()
            if digest_file(config.source.path) != source_hash:
                raise ValueError("Source video changed during the probe")
            result["sessions"].append(
                {
                    "caseId": case_id,
                    "configRequestedExecutor": config.model.executor,
                "processingMaximumWidth": config.processing.maxWidth,
                "sourceVideoSha256": source_hash,
                    "effectiveExecutor": copy.deepcopy(estimator.executor_metadata),
                    "modelSha256": digest_file(config.model.path),
                }
            )
    result["complete"] = True
    (output / "result.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "frames": len(result["frames"]),
                "cameraOpened": False,
                "httpSent": False,
                "eventsGenerated": 0,
                "resultPath": str(output / "result.json"),
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    execute(args.protocol, args.selection, args.output)
