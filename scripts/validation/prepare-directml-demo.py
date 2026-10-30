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


def prepare(base, credential, output, duration=60):
    original = base.read_bytes()
    c = load_config(base)
    if c.source.kind != "WEBCAM" or not c.source.authorized:
        raise ValueError("Use a webcam previamente autorizada e calibrada")
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
    c.events.delivery.enabled = True
    c.events.delivery.credentialFile = str(private_path(credential))
    credentials(
        c.events.delivery, c.cameraId
    )  # Validate locally; never send or print token.
    c.events.evidenceMode = "skeleton"
    c.events.snapshotAuthorized = False
    c.processing.preview = True
    c.processing.previewStartPaused = False
    if duration not in (60, 600):
        raise ValueError("Use 60 segundos curtos ou 600 segundos nominais (D51)")
    c.processing.maxRunSeconds = duration
    c.diagnostics.exportDecisions = c.diagnostics.profileProcessing = True
    c.diagnostics.profileOperators = False
    if duration == 600:
        # Bounded diagnostics for decisions + final profiles at 5 Hz; not video.
        # Does not change cadence, evidence or acceptance criteria.
        c.diagnostics.maxDecisionRecords = 10000
        c.diagnostics.maxDecisionBytes = 50 * 1024 * 1024
        c.diagnostics.maxDecisionDirectoryBytes = 100 * 1024 * 1024
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
                "sourceExecutor": source_executor,
                "requestedExecution": {
                    "executor": c.model.executor,
                    "recovery": c.model.recovery,
                    "runtimeProfile": c.model.runtimeProfile,
                    "initialized": False,
                    "pythonEnvironmentSelected": False,
                },
                "durationSeconds": duration,
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
    ap.add_argument("--duration", type=int, choices=(60, 600), default=60)
    a = ap.parse_args()
    print(
        json.dumps(
            {
                "status": "prepared",
                "config": prepare(a.base, a.credential, a.output, a.duration),
                "cameraOpened": False,
                "httpSent": False,
            }
        )
    )
