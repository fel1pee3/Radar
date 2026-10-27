"""Counterfactual FILE audit; alternatives are never input to an online policy."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from pydantic import Field
from radar_edge.calibration import load_calibration
from radar_edge.config import StrictModel, load_config, private_path
from radar_edge.features import QualityGate, extract_features
from radar_edge.model import get_model_spec
from radar_edge.observations import Observation, pose_quality
from radar_edge.policy import configured_policy
from radar_edge.posture import create_posture_classifier
from radar_edge.preferred_rtmo import PreferredRtmoEstimator
from radar_edge.source import FileSource, Frame, FrameSource

PATHS = ("PERSON_PROPOSAL_CROP", "CENTER_80", "ROTATE_270", "ROTATE_90", "ROTATE_180")


class AuditCase(StrictModel):
    caseId: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    configPath: str
    timestampMs: int = Field(ge=0)


class Manifest(StrictModel):
    cases: list[AuditCase] = Field(min_length=1, max_length=100)


def exact_frame(source: FrameSource, timestamp_ms: int) -> Frame:
    while (frame := source.read()) is not None:
        if frame.timestamp_ms == timestamp_ms:
            return frame
        if frame.timestamp_ms > timestamp_ms:
            break
    raise ValueError(
        f"Timestamp exato {timestamp_ms} ms não encontrado; sem aproximação."
    )


def digest(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(case: AuditCase, repeats: int) -> dict[str, Any]:
    if not 1 <= repeats <= 5:
        raise ValueError("Use entre uma e cinco repetições, sem execução ilimitada.")
    config = load_config(case.configPath)
    if config.source.kind != "FILE" or config.model.variant != "rtmo-s":
        raise ValueError(
            "A auditoria exige FILE autorizado e modelo rtmo-s; não abre câmera."
        )
    if config.posture.method != "MULTICLASS_BODY_V3":
        raise ValueError(
            "Use o contexto multiclasse existente, sem alterar seus critérios."
        )
    calibration = load_calibration(config.calibrationPath)
    policy = configured_policy(config.events.policy)
    spec = get_model_spec(config.model.variant)
    classifier = create_posture_classifier(config.posture, calibration, spec, policy)
    identities = {
        "configuration": digest(case.configPath),
        "video": digest(config.source.path),
        "model": digest(config.model.path),
        "calibration": digest(config.calibrationPath),
        "classifier": digest(config.posture.artifactPath),
    }
    rows: list[dict[str, Any]] = []
    with (
        FileSource(config.source, config.processing.maxWidth) as source,
        PreferredRtmoEstimator(
            config.model.path, runtime_profile=config.model.runtimeProfile
        ) as estimator,
    ):
        warm_start = perf_counter()
        estimator.infer_image(np.full((640, 640, 3), 114, dtype=np.uint8))
        warmup_ms = (perf_counter() - warm_start) * 1000
        frame = exact_frame(source, case.timestampMs)
        height, width = frame.bgr.shape[:2]
        import cv2

        luminance = float(cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY).mean())
        for repeat in range(repeats):
            estimator.perception_attempts = []
            started = perf_counter()
            original = estimator._run_path("ORIGINAL", frame, None)
            original_ms = (perf_counter() - started) * 1000
            proposal = (
                estimator.proposal.copy() if estimator.proposal is not None else None
            )
            original_attempt = dict(estimator.perception_attempts[-1])
            signals = {
                "attempt": original_attempt,
                "proposalNormalized": (
                    (proposal / np.array([width, height, width, height])).tolist()
                    if proposal is not None
                    else None
                ),
            }
            shift = repeat % len(PATHS)
            for path in ("ORIGINAL", *PATHS[shift:], *PATHS[:shift]):
                if path == "PERSON_PROPOSAL_CROP" and proposal is None:
                    rows.append(
                        {
                            "repeat": repeat + 1,
                            "path": path,
                            "skipped": "NO_CURRENT_ROI",
                        }
                    )
                    continue
                started = perf_counter()
                result = (
                    original
                    if path == "ORIGINAL"
                    else estimator._run_path(path, frame, proposal)
                )
                elapsed_ms = (
                    original_ms
                    if path == "ORIGINAL"
                    else (perf_counter() - started) * 1000
                )
                poses, boxes, score = result
                attempt = (
                    original_attempt
                    if path == "ORIGINAL"
                    else dict(estimator.perception_attempts[-1])
                )
                state, reasons = pose_quality(poses, config.processing.minKeypointScore)
                observation = Observation(
                    schemaVersion=1,
                    runId="counterfactual-not-a-capture-run",
                    cameraId=config.cameraId,
                    mode="REPLAY",
                    frameIndex=frame.index,
                    timestampMs=frame.timestamp_ms,
                    timestampSource=frame.timestamp_source,
                    width=width,
                    height=height,
                    rotation=frame.geometry.rotation,
                    poses=poses,
                    poseCount=len(poses),
                    inferenceState=state,
                    qualityReasons=reasons,
                    meanLuminance=luminance,
                    inferenceMs=elapsed_ms,
                    modelId=spec.model_id,
                    calibrationId=calibration["calibrationId"],
                    calibrationVersion=calibration["version"],
                    personDetections=boxes,
                    perceptionPasses=(path,),
                    personProposalScore=score,
                )
                # Each alternative is isolated. Sparse/repeated timestamps are not a
                # chronological session and cannot be fed to a shared FPS gate.
                features = QualityGate(policy).apply(
                    observation,
                    extract_features(observation, calibration["floorPolygon"], policy),
                )
                classified = classifier.classify(observation, features)
                rows.append(
                    {
                        "repeat": repeat + 1,
                        "path": path,
                        "attempt": attempt,
                        "elapsedMs": elapsed_ms,
                        "essentialCount": estimator.valid_essential(poses),
                        "poseCount": len(poses),
                        "inferenceState": state,
                        "decisionEligibleWithoutTemporalHistory": classified.eligible,
                        "posture": classified.posture,
                        "classScores": classified.postureClassScores,
                        "reasons": classified.reasons,
                        "poses": [asdict(pose) for pose in poses],
                        "boxes": boxes,
                        "originalSignals": signals,
                    }
                )
    if identities["video"] != digest(config.source.path):
        raise ValueError(
            "O vídeo mudou durante a auditoria; resultados não comparáveis."
        )
    return {
        "case": case.model_dump(),
        "hashes": identities,
        "frameIndex": frame.index,
        "frameSha256": hashlib.sha256(frame.bgr.tobytes()).hexdigest(),
        "geometry": asdict(frame.geometry),
        "warmupSyntheticExcludedMs": warmup_ms,
        "rows": rows,
        "temporalAcceptanceEvaluated": False,
        "policyMayNotUseCounterfactualOutcomes": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    manifest = Manifest.model_validate_json(Path(args.manifest).read_bytes())
    output = private_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for case in manifest.cases:
        result = audit(case, args.repeats)
        results.append(result)
        (output / "audit.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {"case": case.caseId, "timestampMs": case.timestampMs, "status": "ok"}
            )
        )
    print(
        json.dumps({"cases": len(results), "cameraOpened": False, "httpEnabled": False})
    )


if __name__ == "__main__":
    main()
