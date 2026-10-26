"""Explicit operator confirmation; preserve previous config and queues, never capture."""

import json
import os
from uuid import uuid4

import yaml

from radar_edge.calibration import load_calibration
from radar_edge.config import load_config, private_path
from radar_edge.errors import EdgeError
from radar_edge.model import get_model_spec, verify_model
from radar_edge.policy import configured_policy
from radar_edge.posture import calibration_digest, create_posture_classifier


def confirm_context(filename, confirmed=False):
    if not confirmed:
        raise EdgeError(
            "CONTEXT_CONFIRMATION_REQUIRED", "Confira o piso antes de confirmar contexto."
        )
    path = private_path(filename)
    original = path.read_bytes()
    config = load_config(path)
    if config.posture.method != "MULTICLASS_BODY_V3":
        raise EdgeError("POSTURE_CONTEXT_UNSUPPORTED", "Este preparador atende ao candidato V3.")
    cal = load_calibration(config.calibrationPath)
    if cal["cameraId"] != config.cameraId:
        raise EdgeError("CALIBRATION_CAMERA_MISMATCH", "Calibracao pertence a outra camera.")
    config.posture.calibrationSha256 = calibration_digest(cal)
    config.posture.operatorConfirmed = True
    verify_model(config.model.path, config.model.variant)
    create_posture_classifier(
        config.posture,
        cal,
        get_model_spec(config.model.variant),
        configured_policy(config.events.policy),
    )
    root = private_path(".local/detector-evolution/context-confirmations") / str(uuid4())
    root.mkdir(parents=True)
    (root / "previous.yaml").write_bytes(original)
    previous_queue = config.events.outboxPath
    config.events.outboxPath = str(root / "outbox.sqlite")
    config.diagnostics.outputDirectory = str(root / "results")
    temporary = root / "confirmed.yaml"
    temporary.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")
    if path.read_bytes() != original:
        raise EdgeError("CONFIG_CHANGED", "Configuracao mudou; confira antes de repetir.")
    os.replace(temporary, path)
    result = {
        "status": "ok",
        "configuration": str(path),
        "previousConfiguration": str(root / "previous.yaml"),
        "previousOutboxPreserved": previous_queue,
        "outbox": config.events.outboxPath,
        "calibrationSha256": config.posture.calibrationSha256,
        "sourceOpened": False,
        "cameraOpened": False,
        "trained": False,
    }
    (root / "confirmation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
