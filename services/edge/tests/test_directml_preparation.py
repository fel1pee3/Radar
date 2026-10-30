"""GPU preparation preserves processing choices without inference, capture or delivery."""

import hashlib
import importlib.util
import json
from pathlib import Path

import httpx
import pytest
import yaml
from temporal_support import CAMERA, calibration

from radar_edge.config import EdgeConfig, load_config
from radar_edge.posture import calibration_digest

ROOT = Path(__file__).resolve().parents[3]
ALLOWED = ("RTMO_ADAPTIVE_V3", "RTMO_PREFERRED_V2")


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/validation" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def preparation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    private = Path(".local")
    private.mkdir()
    floor = {**calibration(), "cameraId": CAMERA}
    (private / "calibration.json").write_text(json.dumps(floor), encoding="utf-8")
    (private / "clip.mp4").write_bytes(b"synthetic pinned input; never decoded")
    (private / "weights.onnx").write_bytes(b"synthetic weights; never loaded")
    (private / "classifier.json").write_text("{}", encoding="utf-8")
    credential = private / "credential.json"
    credential.write_text(
        json.dumps(
            {
                "cameraId": CAMERA,
                "deviceToken": "Synthetic-local-preparation-only-token",
                "apiUrl": "http://127.0.0.1:1/v1",
            }
        ),
        encoding="utf-8",
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Preparation must never open capture or send HTTP")

    import cv2

    monkeypatch.setattr(cv2, "VideoCapture", forbidden)
    monkeypatch.setattr(httpx.Client, "request", forbidden)

    def base(
        mode,
        recovery="RTMO_ADAPTIVE_V3",
        executor="CPU",
        profile="REFERENCE_4_SPIN",
        variant="rtmo-s",
    ):
        source = (
            {"kind": "WEBCAM", "index": 0, "authorized": True}
            if mode == "demo"
            else {
                "kind": "FILE",
                "path": ".local/clip.mp4",
                "videoId": "preparation",
                "authorized": True,
            }
        )
        c = EdgeConfig.model_validate(
            {
                "cameraId": CAMERA,
                "purpose": "RADAR_LIVE_POSE" if mode == "demo" else "RADAR_FILE_POSE",
                "source": source,
                "model": {
                    "variant": variant,
                    "path": ".local/weights.onnx",
                    "executor": executor,
                    "recovery": recovery,
                    "runtimeProfile": profile,
                },
                "posture": {
                    "method": "MULTICLASS_CONTEXT_V4",
                    "artifactPath": ".local/classifier.json",
                    "artifactSha256": hashlib.sha256(b"{}").hexdigest(),
                    "installationId": "preparation-test",
                    "calibrationSha256": calibration_digest(floor),
                    "operatorConfirmed": True,
                },
                "events": {
                    "enabled": False,
                    "policy": {
                        "version": "floor-rtmo-score-posture-context-v4-preparation",
                        "qualitySource": "RTMO_KEYPOINT_SCORE",
                        "temporalMode": "EVIDENCE_V2",
                        "transitionEvidence": "POSTURE_DYNAMICS_V3",
                    },
                },
            }
        )
        path = private / "base.yaml"
        path.write_text(yaml.safe_dump(c.model_dump()), encoding="utf-8")
        return path, c

    return base, credential


def invoke(mode, monkeypatch, base, credential, output):
    m = script("prepare-directml-" + mode + ".py")
    if mode == "demo":
        monkeypatch.setattr(m, "check_posture", lambda c: None)
        return m.prepare(base, str(credential), str(output), 600)
    pinned = [
        base,
        Path(".local/clip.mp4"),
        Path(".local/weights.onnx"),
        Path(".local/calibration.json"),
        Path(".local/classifier.json"),
    ]
    protocol = Path(".local/protocol.json")
    protocol.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "case",
                        "config": str(base),
                        "preservedFiles": {
                            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in pinned
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return m.prepare(protocol, "case", CAMERA, str(credential), str(output))


@pytest.mark.parametrize("mode", ["replay", "demo"])
@pytest.mark.parametrize("recovery", ALLOWED)
@pytest.mark.parametrize("executor", ["CPU", "DIRECTML"])
def test_preparation_preserves_explicit_recovery_and_reference(
    mode, recovery, executor, preparation, monkeypatch
):
    factory, credential = preparation
    base, original = factory(mode, recovery, executor)
    preserved = {p: p.read_bytes() for p in [base, credential, Path(".local/calibration.json")]}
    output = Path(".local/prepared")
    path = invoke(mode, monkeypatch, base, credential, output)
    actual = load_config(path)
    assert actual.model.recovery == recovery
    assert actual.model.executor == "DIRECTML" and actual.model.runtimeProfile == "REFERENCE_4_SPIN"
    assert (
        actual.model.path == original.model.path and actual.events.policy == original.events.policy
    )
    assert actual.processing.targetAnalysisFps == original.processing.targetAnalysisFps
    assert actual.processing.minKeypointScore == original.processing.minKeypointScore
    assert actual.events.delivery.enabled and not actual.events.snapshotAuthorized
    assert actual.events.evidenceMode == "skeleton"
    assert all(p.read_bytes() == content for p, content in preserved.items())
    receipt_name = "preparation.json" if mode == "demo" else "provenance.json"
    receipt = json.loads((output / receipt_name).read_text(encoding="utf-8"))
    assert receipt["sourceExecutor"] == executor
    assert receipt["requestedExecution"] == {
        "executor": "DIRECTML",
        "recovery": recovery,
        "runtimeProfile": "REFERENCE_4_SPIN",
        "initialized": False,
        "pythonEnvironmentSelected": False,
    }
    assert receipt["cameraOpened"] is False and receipt["httpSent"] is False
    if mode == "demo":
        assert actual.processing.maxRunSeconds == 600
    else:
        assert actual.source.kind == "FILE" and not actual.processing.preview
    with pytest.raises((ValueError, FileExistsError)):
        invoke(mode, monkeypatch, base, credential, output)
    assert all(p.read_bytes() == content for p, content in preserved.items())


@pytest.mark.parametrize("mode", ["replay", "demo"])
@pytest.mark.parametrize(
    "changes",
    [
        {"recovery": "NONE"},
        {"recovery": "RTMO_ADAPTIVE_V2"},
        {"recovery": "RTMO_PREFERRED_V1"},
        {"profile": "CPU_2_SPIN"},
        {"variant": "full", "recovery": "NONE"},
    ],
)
def test_unsupported_processing_is_rejected_before_output(mode, changes, preparation, monkeypatch):
    factory, credential = preparation
    base, _ = factory(mode, **changes)
    original = base.read_bytes()
    output = Path(".local/not-created")
    with pytest.raises(ValueError, match="Preserve RTMO"):
        invoke(mode, monkeypatch, base, credential, output)
    assert not output.exists() and base.read_bytes() == original
