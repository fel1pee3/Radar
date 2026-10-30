"""Evaluate one pinned, explicitly annotated FILE case through the normal worker."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/edge/src"))

import yaml
from radar_edge.config import load_config, private_path
from radar_edge.evaluation import Target, match_floor_acceptance
from radar_edge.pipeline import run_pipeline


def evaluate(protocol_path, case_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", case_id):
        raise ValueError("Use a simple case identity, never a filesystem path")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8-sig"))
    matches = [case for case in protocol["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise ValueError(
            "Case identity must be unique and present in the frozen protocol"
        )
    item = matches[0]
    if not isinstance(item.get("targets"), list):
        raise TypeError(
            "Explicit inherited human/source targets required; no prediction-derived onset"
        )
    targets = [Target(**target) for target in item["targets"]]
    if type(item.get("negativeExpectedPerson")) is not bool:
        raise ValueError("Explicit boolean negativeExpectedPerson annotation required")
    if targets and not item["negativeExpectedPerson"]:
        raise ValueError("A target episode requires expected person presence")
    for filename, expected in item["preservedFiles"].items():
        with Path(filename).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                raise ValueError("Pinned input changed: " + filename)
    config = load_config(item["config"])
    if config.source.kind != "FILE" or not config.source.authorized:
        raise ValueError("Authorized FILE required; webcam is never permitted")
    pinned = {Path(filename).resolve() for filename in item["preservedFiles"]}
    required = [
        item["config"],
        config.source.path,
        config.model.path,
        config.calibrationPath,
    ]
    if config.posture.artifactPath:
        required.append(config.posture.artifactPath)
    if any(Path(filename).resolve() not in pinned for filename in required):
        raise ValueError(
            "Config, source, weights, calibration and classifier must be pinned"
        )
    if config.events.delivery.enabled or config.events.snapshotAuthorized:
        raise ValueError("Regression must explicitly disable HTTP and snapshots")
    if config.events.evidenceMode != "skeleton":
        raise ValueError("Skeleton-only evidence required")
    if config.processing.maxRunSeconds or config.processing.maxObservations:
        raise ValueError("Full file horizon required; no observation/time truncation")
    output = (
        private_path(protocol["outputRoot"])
        / "functional"
        / config.model.executor.lower()
        / case_id
    )
    output.mkdir(parents=True, exist_ok=False)
    config.processing.preview = config.processing.previewStartPaused = False
    config.processing.replaySpeed = 0
    config.events.outboxPath = str(output / "outbox.sqlite")
    config.diagnostics.outputDirectory = str(output / "results")
    config.diagnostics.exportDecisions = True
    config.diagnostics.profileProcessing = True
    (output / "config.yaml").write_text(
        yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8"
    )
    report, code = run_pipeline(config)
    temporal = report.get("temporal", {})
    score = match_floor_acceptance(
        temporal.get("events", []),
        targets,
        [],
        temporal.get("eligibleMediaMs", 0),
        temporal.get("observedMediaMs", 0),
        code == 0,
        negative_expected_person=item["negativeExpectedPerson"],
        capture_eligible_ms=temporal.get("captureEligibleMs"),
        evaluation_duration_ms=report["source"]["durationMsEstimate"],
    )
    result = {
        "id": case_id,
        "backend": config.model.executor.lower(),
        "code": code,
        "error": report.get("error"),
        "score": score,
        "source": report["source"],
        "reportPath": report["reportPath"],
        "temporal": temporal,
        "metrics": report["metrics"],
        "sessions": [report["model"].get("executor")],
        "runtimeEnvironment": report.get("runtimeEnvironment"),
        "scope": "DEVELOPMENT_FILE_REGRESSION_NOT_REALTIME_OR_INDEPENDENT",
    }
    (output / "evaluation.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({"case": case_id, "code": code, "score": score}), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    result = evaluate(args.protocol, args.case)
    raise SystemExit(result["code"])
