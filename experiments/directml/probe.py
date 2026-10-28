"""One frozen-frame batch with the unchanged RTMO recovery and classifier."""

# The isolated environment imports repository source after the explicit path bootstrap.
# ruff: noqa: E402

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, process_time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/edge/src"))

import cv2
import numpy as np
from radar_edge.calibration import load_calibration
from radar_edge.config import load_config, private_path
from radar_edge.features import QualityGate, extract_features
from radar_edge.model import get_model_spec
from radar_edge.observations import Observation, pose_quality
from radar_edge.policy import configured_policy
from radar_edge.posture import create_posture_classifier
from radar_edge.rtmo import RtmoEstimator
from radar_edge.source import Frame, Geometry
from runtime import HostReadySession, create_session, process_memory, profile_summary


def frame_context(item):
    image = cv2.imread(item["imagePath"])
    if image is None or hashlib.sha256(image.tobytes()).hexdigest() != item["frameSha256"]:
        raise ValueError("Frozen source pixels differ")
    if hashlib.sha256(Path(item["configPath"]).read_bytes()).hexdigest() != item["configSha256"]:
        raise ValueError("Reference configuration changed")
    config = load_config(item["configPath"])
    if (
        config.source.kind != "FILE"
        or not config.source.authorized
        or config.model.variant != "rtmo-s"
        or config.model.runtimeProfile != "REFERENCE_4_SPIN"
        or config.model.recovery != "RTMO_ADAPTIVE_V3"
    ):
        raise ValueError("Require the unchanged authorized RTMO reference")
    calibration = load_calibration(config.calibrationPath)
    policy = configured_policy(config.events.policy)
    spec = get_model_spec("rtmo-s")
    classifier = create_posture_classifier(config.posture, calibration, spec, policy)
    h, w = image.shape[:2]
    geometry = calibration["geometry"]
    frame = Frame(
        item["frameIndex"],
        item["timestampMs"],
        "SOURCE_PTS",
        image,
        Geometry(
            geometry.get("rawWidth", w),
            geometry.get("rawHeight", h),
            geometry.get("orientedWidth", w),
            geometry.get("orientedHeight", h),
            w,
            h,
            geometry["rotation"],
        ),
    )
    return frame, config, calibration, policy, classifier, spec


def one_analysis(item, broker, output):
    frame, config, calibration, policy, classifier, spec = frame_context(item)
    model = RtmoEstimator(
        config.model.path,
        recovery="RTMO_ADAPTIVE_V3",
        runtime_profile="REFERENCE_4_SPIN",
    )
    model.session = broker
    begin = perf_counter()
    poses, estimate_ms = model.estimate(frame)
    estimated = perf_counter()
    state, reasons = pose_quality(poses, 0.5)
    observation = Observation(
        schemaVersion=1,
        runId=str(uuid4()),
        cameraId=config.cameraId,
        mode="REPLAY",
        frameIndex=frame.index,
        timestampMs=frame.timestamp_ms,
        timestampSource=frame.timestamp_source,
        width=frame.geometry.width,
        height=frame.geometry.height,
        rotation=frame.geometry.rotation,
        poses=poses,
        poseCount=len(poses),
        inferenceState=state,
        qualityReasons=reasons,
        meanLuminance=float(cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY).mean()),
        inferenceMs=estimate_ms,
        modelId=spec.model_id,
        calibrationId=calibration["calibrationId"],
        calibrationVersion=calibration["version"],
        personDetections=model.person_detections,
        perceptionPasses=model.perception_passes,
        personProposalScore=model.person_proposal_score,
    )
    features = QualityGate(policy).apply(
        observation, extract_features(observation, calibration["floorPolygon"], policy)
    )
    qualified = perf_counter()
    features = classifier.classify(observation, features)
    finished = perf_counter()
    # Hashing, archives and JSON happen after the full processing timer.
    calls = broker.drain()
    attempts = [a for a in model.perception_attempts if not a.get("skippedReason")]
    if len(calls) != len(attempts):
        raise ValueError("Native call accounting differs from unchanged recovery trace")
    call_records = []
    for index, (call, attempt) in enumerate(zip(calls, attempts, strict=True)):
        tensor = call["feed"]["input"]
        if tensor.dtype != np.float32 or tensor.shape != (1, 3, 640, 640):
            raise ValueError("Reference input tensor changed")
        archive = output / f"{item['id']}-pass{index}.npz"
        np.savez_compressed(archive, dets=call["outputs"][0], keypoints=call["outputs"][1])
        call_records.append(
            {
                "pass": attempt["pass"],
                "inputTensorSha256": hashlib.sha256(tensor.tobytes()).hexdigest(),
                "inputShape": tensor.shape,
                "inputDtype": str(tensor.dtype),
                "outputShapes": [a.shape for a in call["outputs"]],
                "outputDtypes": [str(a.dtype) for a in call["outputs"]],
                "cpuReady": True,
                "nativeSessionRunMs": call["sessionRunMs"],
                "extraCpuMaterializationMs": call["cpuMaterializationMs"],
                "rawOutputsPath": str(archive),
            }
        )
    return {
        "case": item["case"],
        "frameId": item["id"],
        "role": item["role"],
        "sourceTimestampMs": frame.timestamp_ms,
        "frameSha256": item["frameSha256"],
        "poseCount": len(poses),
        "poses": [asdict(p) for p in poses],
        "boxes": model.person_detections,
        "paths": model.perception_passes,
        "attempts": model.perception_attempts,
        "calls": call_records,
        "nativeCalls": len(calls),
        "poseState": state,
        "poseReasons": reasons,
        "posture": features.posture,
        "eligible": features.eligible,
        "candidate": features.candidate,
        "reasons": features.reasons,
        "postureClassScores": features.postureClassScores,
        "regionState": features.regionState,
        "estimatorMs": (estimated - begin) * 1000,
        "qualityMs": (qualified - estimated) * 1000,
        "classificationMs": (finished - qualified) * 1000,
        "fullProcessingMs": (finished - begin) * 1000,
        "timestampsUnchanged": True,
        "eventsCreated": 0,
    }


def run(protocol_path, backend, output, repetition=1, profiling=False):
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    output = private_path(output)
    output.mkdir(parents=True, exist_ok=False)
    model_path = ROOT / ".local/models/rtmo_s_body7_640.onnx"
    if hashlib.sha256(model_path.read_bytes()).hexdigest() != protocol["modelSha256"]:
        raise ValueError("Pinned RTMO bytes differ")
    native, session_info = create_session(
        model_path, backend, output / "ort-profile" if profiling else None
    )
    broker = HostReadySession(native)
    warmup = []
    synthetic = np.full((1, 3, 640, 640), 114, np.float32)
    for _ in range(protocol["syntheticWarmupCalls"]):
        start = perf_counter()
        ready = [
            np.array(a, copy=True) for a in native.run(["dets", "keypoints"], {"input": synthetic})
        ]
        assert all(a.dtype == np.float32 for a in ready)
        warmup.append((perf_counter() - start) * 1000)
    cpu_started, wall_started = process_time(), perf_counter()
    memory_before = process_memory()
    cases = protocol["cases"] if repetition % 2 else list(reversed(protocol["cases"]))
    rows = []
    try:
        for item in cases:
            rows.append(one_analysis(item, broker, output))
    except Exception:
        (output / "native-error.json").write_text(
            json.dumps(
                {"lastNativeError": broker.last_error, "session": session_info},
                indent=2,
            ),
            encoding="utf-8",
        )
        raise
    elapsed, cpu_seconds = perf_counter() - wall_started, process_time() - cpu_started
    profile = None
    if profiling:
        profile_path = native.end_profiling()
        profile = {"path": profile_path, "summary": profile_summary(profile_path)}
    result = {
        "scope": "DEVELOPMENT_FROZEN_FRAMES_RTMO_NO_CAMERA_OR_EVENTS",
        "backend": backend,
        "repetition": repetition,
        "profiling": profiling,
        "session": session_info,
        "syntheticWarmupMs": warmup,
        "profile": profile,
        "rows": rows,
        "resources": {
            "wallSecondsIncludingExport": elapsed,
            "processCpuSeconds": cpu_seconds,
            "averageCpuPercentAllLogicalCpus": 100 * cpu_seconds / elapsed / os.cpu_count(),
            "logicalCpuCount": os.cpu_count(),
            "before": memory_before,
            "after": process_memory(),
            "limit": (
                "includes frame loads/hash/compression and retained profiling tensors; "
                "no complete GPU memory accounting"
            ),
        },
        "modelSha256": protocol["modelSha256"],
        "referenceAlgorithm": protocol["reference"],
        "cameraOpened": False,
        "eventsCreated": 0,
        "numericalPolicyOrTimerChanged": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "backend": backend,
                "repetition": repetition,
                "cases": [
                    {
                        "id": r["frameId"],
                        "ms": round(r["fullProcessingMs"], 3),
                        "paths": r["paths"],
                        "posture": r["posture"],
                    }
                    for r in rows
                ],
                "profiling": profiling,
            }
        )
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument(
        "--backend", choices=("cpu-reference", "cpu-matched", "directml"), required=True
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    run(args.protocol, args.backend, args.output, args.repetition, args.profile)


if __name__ == "__main__":
    main()
