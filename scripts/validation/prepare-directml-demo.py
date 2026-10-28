"""Prepare the normal worker's explicit GPU demo. No capture, HTTP or token rotation."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/edge/src"))
from radar_edge.config import load_config, private_path
from radar_edge.delivery import credentials
from radar_edge.posture import check_posture


def prepare(base, credential, output):
    original = base.read_bytes()
    c = load_config(base)
    if c.source.kind != "WEBCAM" or not c.source.authorized:
        raise ValueError("Use a webcam previamente autorizada e calibrada")
    c.model.executor = "DIRECTML"
    if c.model.recovery != "RTMO_ADAPTIVE_V3" or c.model.runtimeProfile != "REFERENCE_4_SPIN":
        raise ValueError("Preserve a referencia existente")
    c.events.delivery.enabled = True
    c.events.delivery.credentialFile = str(private_path(credential))
    credentials(c.events.delivery, c.cameraId)  # Validate locally; never send or print token.
    c.events.evidenceMode = "skeleton"
    c.events.snapshotAuthorized = False
    c.processing.preview = True
    c.processing.previewStartPaused = False
    if c.processing.maxRunSeconds != 60.0:
        raise ValueError("Preserve os 60 segundos da demonstracao")
    c.diagnostics.exportDecisions = c.diagnostics.profileProcessing = True
    c.diagnostics.profileOperators = False
    target = private_path(output)
    if target.exists():
        raise ValueError("Destino existente preservado. Use uma pasta nova.")
    c.events.outboxPath = str(target / "outbox.sqlite")
    c.diagnostics.outputDirectory = str(target / "results")
    check_posture(c)
    target.mkdir(parents=True, exist_ok=False)
    path = target / "config.yaml"
    path.write_text(yaml.safe_dump(c.model_dump(), sort_keys=False), encoding="utf-8")
    load_config(path)
    assert base.read_bytes() == original
    (target / "preparation.json").write_text(
        json.dumps(
            {
                "scope": "PREPARED_EXPERIMENTAL_PHYSICAL_DEMO_NOT_EXECUTED",
                "baseConfig": str(base),
                "baseConfigSha256": hashlib.sha256(original).hexdigest(),
                "cameraId": c.cameraId,
                "durationSeconds": 60,
                "deliveryEnabled": True,
                "snapshotAuthorized": False,
                "cameraOpened": False,
                "httpSent": False,
                "credentialPath": c.events.delivery.credentialFile,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--credential", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    print(
        json.dumps(
            {
                "status": "prepared",
                "config": prepare(a.base, a.credential, a.output),
                "cameraOpened": False,
                "httpSent": False,
            }
        )
    )
