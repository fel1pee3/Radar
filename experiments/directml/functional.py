"""Functional FILE regression using existing annotations and unchanged event runtime."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "edge" / "src"))

import yaml  # noqa: E402
from stream import experimental_factory  # noqa: E402


def evaluate(protocol_path, backend, case_id):
    from radar_edge.config import load_config
    from radar_edge.evaluation import Target, match_floor_acceptance
    from radar_edge.pipeline import run_pipeline

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    item = next(c for c in protocol["cases"] if c["id"] == case_id)
    for path, expected in item["preservedFiles"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Preserved regression input changed: {path}")
    config = load_config(item["config"])
    if config.source.kind != "FILE" or not config.source.authorized:
        raise ValueError("Only authorized FILE regression; never a camera")
    directory = Path(protocol["outputRoot"]) / "functional" / backend / case_id
    directory.mkdir(parents=True, exist_ok=False)
    config.model.runtimeProfile = "REFERENCE_4_SPIN"
    if config.model.recovery != "RTMO_ADAPTIVE_V3":
        raise ValueError("Reference recovery changed")
    config.processing.preview = False
    config.processing.previewStartPaused = False
    config.processing.replaySpeed = 0
    config.processing.maxObservations = None
    config.processing.maxRunSeconds = None
    config.events.outboxPath = str(directory / "outbox.sqlite")
    config.events.delivery.enabled = False
    config.events.delivery.credentialFile = None
    config.events.evidenceMode = "skeleton"
    config.events.snapshotAuthorized = False
    config.diagnostics.outputDirectory = str(directory / "results")
    config.diagnostics.exportDecisions = True
    config.diagnostics.profileProcessing = False
    (directory / "config.yaml").write_text(
        yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8"
    )
    sessions = []
    with experimental_factory(backend, sessions):
        report, code = run_pipeline(config)
    temporal = report.get("temporal", {})
    if item["targets"] is not None:
        targets = [Target(**t) for t in item["targets"]]
    elif item.get("expectedFloor"):
        targets = [
            Target(
                startMs=3000 if case_id == "controlled-lying" else 0,
                endMs=round(report["source"]["durationMsEstimate"]),
                kind="PERSON_ON_FLOOR",
            )
        ]
    else:
        targets = []
    score = match_floor_acceptance(
        temporal.get("events", []),
        targets,
        [],
        temporal.get("eligibleMediaMs", 0),
        temporal.get("observedMediaMs", 0),
        not code,
        negative_expected_person=case_id not in ("intake16-14", "intake16-15"),
        capture_eligible_ms=temporal.get("captureEligibleMs"),
        evaluation_duration_ms=report["source"]["durationMsEstimate"],
    )
    result = {
        "id": case_id,
        "backend": backend,
        "code": code,
        "error": report.get("error"),
        "score": score,
        "source": report["source"],
        "reportPath": report["reportPath"],
        "temporal": temporal,
        "metrics": report["metrics"],
        "sessions": sessions,
        "scope": "DEVELOPMENT_FILE_REGRESSION_NOT_REALTIME_OR_INDEPENDENT",
    }
    (directory / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "case": case_id,
                "backend": backend,
                "code": code,
                "approved": score["approved"],
                "missed": score["missed"],
                "negative": score["negativeResult"],
                "events": score["eventKinds"],
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--backend", choices=("cpu-reference", "directml"), required=True)
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    raise SystemExit(evaluate(args.protocol, args.backend, args.case)["code"])
