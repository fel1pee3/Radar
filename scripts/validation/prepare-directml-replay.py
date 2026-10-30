"""Clone an authorized regression FILE into a new isolated integration session."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/edge/src"))
from radar_edge.config import load_config, private_path
from radar_edge.posture import calibration_digest


def prepare(protocol, case_id, camera_id, credential, output):
    item = next(
        c
        for c in json.loads(protocol.read_text(encoding="utf-8"))["cases"]
        if c["id"] == case_id
    )
    for path, expected in item["preservedFiles"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("Regression input changed")
    c = load_config(item["config"])
    if c.source.kind != "FILE" or not c.source.authorized:
        raise ValueError("Only existing authorized FILE; never webcam")
    if (
        c.model.variant != "rtmo-s"
        or c.model.recovery not in {"RTMO_ADAPTIVE_V3", "RTMO_PREFERRED_V2"}
        or c.model.runtimeProfile != "REFERENCE_4_SPIN"
    ):
        raise ValueError(
            "Preserve RTMO_ADAPTIVE_V3/RTMO_PREFERRED_V2 com REFERENCE_4_SPIN"
        )
    source_executor = c.model.executor
    c.model.executor = "DIRECTML"
    credential = private_path(credential)
    auth = json.loads(credential.read_text(encoding="utf-8"))
    if auth["cameraId"] != camera_id:
        raise ValueError("Camera credential mismatch")
    c.cameraId = camera_id
    c.processing.preview = c.processing.previewStartPaused = False
    c.processing.replaySpeed = 1.0
    c.events.enabled = True
    c.events.evidenceMode = "skeleton"
    c.events.snapshotAuthorized = False
    c.events.delivery.enabled = True
    c.events.delivery.credentialFile = str(credential)
    out = private_path(output)
    out.mkdir(parents=True, exist_ok=False)
    cal = json.loads(private_path(c.calibrationPath).read_text(encoding="utf-8"))
    cal["cameraId"] = camera_id
    c.calibrationPath = str(out / "calibration.json")
    (out / "calibration.json").write_text(json.dumps(cal, indent=2), encoding="utf-8")
    c.posture.calibrationSha256 = calibration_digest(cal)
    c.events.outboxPath = str(out / "outbox.sqlite")
    c.diagnostics.outputDirectory = str(out / "results")
    c.diagnostics.exportDecisions = c.diagnostics.profileProcessing = True
    c.diagnostics.profileOperators = True
    path = out / "config.yaml"
    path.write_text(yaml.safe_dump(c.model_dump(), sort_keys=False), encoding="utf-8")
    load_config(path)
    (out / "provenance.json").write_text(
        json.dumps(
            {
                "scope": "AUTOMATED_REPLAY_TEST_NOT_HUMAN_REVIEW",
                "sourceConfig": item["config"],
                "sourceExecutor": source_executor,
                "requestedExecution": {
                    "executor": c.model.executor,
                    "recovery": c.model.recovery,
                    "runtimeProfile": c.model.runtimeProfile,
                    "initialized": False,
                    "pythonEnvironmentSelected": False,
                },
                "cameraOpened": False,
                "httpSent": False,
                "sourceVideoSha256": hashlib.sha256(
                    Path(c.source.path).read_bytes()
                ).hexdigest(),
                "geometryAndPolygonsUnchanged": True,
                "cameraIdentityClonedForIsolatedDatabase": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True, type=Path)
    ap.add_argument("--case", required=True)
    ap.add_argument("--camera-id", required=True)
    ap.add_argument("--credential", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    print(
        json.dumps(
            {"config": prepare(a.protocol, a.case, a.camera_id, a.credential, a.output)}
        )
    )
