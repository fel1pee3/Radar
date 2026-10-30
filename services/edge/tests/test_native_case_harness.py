"""Synthetic safety preflight tests; never opens capture, HTTP or an estimator."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/validation" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    private = tmp_path / ".local"
    private.mkdir()
    files = {}
    for name in ("config.yaml", "source.mp4", "weights.onnx", "floor.json", "posture.json"):
        filename = private / name
        filename.write_bytes(name.encode())
        files[str(filename)] = hashlib.sha256(filename.read_bytes()).hexdigest()
    config = SimpleNamespace(
        source=SimpleNamespace(kind="FILE", authorized=True, path=str(private / "source.mp4")),
        model=SimpleNamespace(path=str(private / "weights.onnx"), executor="DIRECTML"),
        calibrationPath=str(private / "floor.json"),
        posture=SimpleNamespace(artifactPath=str(private / "posture.json")),
        processing=SimpleNamespace(
            maxRunSeconds=None,
            maxObservations=None,
            preview=True,
            previewStartPaused=True,
            replaySpeed=1,
        ),
        events=SimpleNamespace(
            delivery=SimpleNamespace(enabled=False),
            snapshotAuthorized=False,
            evidenceMode="skeleton",
            outboxPath="unused",
        ),
        diagnostics=SimpleNamespace(
            outputDirectory="unused", exportDecisions=False, profileProcessing=False
        ),
        model_dump=lambda: {"syntheticSafetyTest": True},
    )
    protocol = {
        "outputRoot": str(private / "new-results"),
        "cases": [
            {
                "id": "case-01",
                "config": str(private / "config.yaml"),
                "targets": [],
                "negativeExpectedPerson": True,
                "preservedFiles": files,
            }
        ],
    }
    path = private / "protocol.json"
    module = script("evaluate-native-case.py")
    monkeypatch.setattr(module, "load_config", lambda _: config)
    calls = []

    def forbidden(_):
        calls.append("capture/inference invoked")
        pytest.fail("Invalid protocol must be rejected before the worker is invoked")

    monkeypatch.setattr(module, "run_pipeline", forbidden)

    def save():
        path.write_text(json.dumps(protocol), encoding="utf-8")
        return path

    return SimpleNamespace(
        module=module,
        config=config,
        protocol=protocol,
        path=path,
        save=save,
        private=private,
        calls=calls,
    )


def assert_rejected(case, message):
    with pytest.raises((ValueError, TypeError, RuntimeError), match=message):
        case.module.evaluate(case.save(), "case-01")
    assert not case.calls
    assert not Path(case.protocol["outputRoot"]).exists()


@pytest.mark.parametrize("kind,authorized", [("WEBCAM", True), ("FILE", False)])
def test_native_harness_rejects_camera_and_unauthorized_file(case, kind, authorized):
    case.config.source.kind = kind
    case.config.source.authorized = authorized
    assert_rejected(case, "Authorized FILE required")


@pytest.mark.parametrize("field", ["delivery", "snapshot", "evidence", "seconds", "observations"])
def test_native_harness_rejects_external_delivery_images_and_truncated_horizon(case, field):
    if field == "delivery":
        case.config.events.delivery.enabled = True
    elif field == "snapshot":
        case.config.events.snapshotAuthorized = True
    elif field == "evidence":
        case.config.events.evidenceMode = "snapshot"
    elif field == "seconds":
        case.config.processing.maxRunSeconds = 1
    else:
        case.config.processing.maxObservations = 1
    assert_rejected(case, "disable HTTP|Skeleton-only|Full file horizon")


@pytest.mark.parametrize(
    "name", ["config.yaml", "source.mp4", "weights.onnx", "floor.json", "posture.json"]
)
def test_native_harness_requires_every_behavioral_input_pinned(case, name):
    del case.protocol["cases"][0]["preservedFiles"][str(case.private / name)]
    assert_rejected(case, "must be pinned")


def test_native_harness_checks_pinned_bytes_before_starting_worker(case):
    (case.private / "source.mp4").write_bytes(b"modified")
    assert_rejected(case, "Pinned input changed")


@pytest.mark.parametrize(
    "annotation", [None, [{"kind": "PERSON_ON_FLOOR", "startMs": 2000, "endMs": 1000}]]
)
def test_annotations_must_be_valid_before_capture(case, annotation):
    case.protocol["cases"][0]["targets"] = annotation
    assert_rejected(case, "targets required|Invalid interval|greater than")


@pytest.mark.parametrize("annotation", [None, "false", 1])
def test_negative_person_annotation_must_be_explicit_boolean(case, annotation):
    case.protocol["cases"][0]["negativeExpectedPerson"] = annotation
    assert_rejected(case, "Explicit boolean")


def test_target_cannot_be_annotated_as_empty_room(case):
    case.protocol["cases"][0].update(
        targets=[{"kind": "PERSON_ON_FLOOR", "startMs": 0, "endMs": 3000}],
        negativeExpectedPerson=False,
    )
    assert_rejected(case, "requires expected person")


@pytest.mark.parametrize("identity", ["../escape", "nested/case", "C:\\escape", ".", ""])
def test_case_identity_never_becomes_a_filesystem_path(case, identity):
    with pytest.raises(ValueError, match="simple case identity"):
        case.module.evaluate(case.save(), identity)
    assert not case.calls
    assert not Path(case.protocol["outputRoot"]).exists()


def test_native_harness_preserves_existing_result(case):
    output = Path(case.protocol["outputRoot"]) / "functional/directml/case-01"
    output.mkdir(parents=True)
    sentinel = output / "original.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError):
        case.module.evaluate(case.save(), "case-01")
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert not case.calls


def test_native_harness_output_must_remain_private(case):
    case.protocol["outputRoot"] = str(case.private.parent / "escaped")
    from radar_edge.errors import EdgeError

    with pytest.raises(EdgeError, match=".local"):
        case.module.evaluate(case.save(), "case-01")
    assert not case.calls
    assert not Path(case.protocol["outputRoot"]).exists()


def test_valid_file_uses_full_source_horizon_and_new_private_outputs(case, monkeypatch):
    def fake_pipeline(config):
        assert config.processing.preview is False
        assert config.processing.previewStartPaused is False
        assert config.processing.replaySpeed == 0
        assert config.processing.maxRunSeconds is None
        assert config.processing.maxObservations is None
        assert config.events.delivery.enabled is False
        assert config.events.snapshotAuthorized is False
        output = Path(config.events.outboxPath).parent
        assert output.is_relative_to(case.private)
        assert config.diagnostics.outputDirectory == str(output / "results")
        return {
            "source": {"durationMsEstimate": 1200},
            "temporal": {
                "events": [],
                "eligibleMediaMs": 1000,
                "observedMediaMs": 1000,
                "captureEligibleMs": 1000,
            },
            "reportPath": str(output / "report.json"),
            "metrics": {},
            "model": {"executor": {"provider": "DmlExecutionProvider"}},
        }, 0

    monkeypatch.setattr(case.module, "run_pipeline", fake_pipeline)
    result = case.module.evaluate(case.save(), "case-01")
    assert result["scope"] == "DEVELOPMENT_FILE_REGRESSION_NOT_REALTIME_OR_INDEPENDENT"
    assert result["score"]["evaluatedDurationMs"] == 1200
    assert result["score"]["negativeResult"] == "PASS"
    assert (
        Path(case.protocol["outputRoot"]) / "functional/directml/case-01/evaluation.json"
    ).exists()


@pytest.mark.parametrize("fault", ["path-id", "duplicate", "outside", "tamper"])
def test_batch_preflight_rejects_bad_identity_location_and_input_before_subprocess(
    case, monkeypatch, fault
):
    module = script("run-candidate-regression.py")
    if fault == "path-id":
        case.protocol["cases"][0]["id"] = "../escape"
    elif fault == "duplicate":
        case.protocol["cases"].append(dict(case.protocol["cases"][0]))
    elif fault == "outside":
        case.protocol["outputRoot"] = str(case.private.parent / "outside")
    else:
        (case.private / "source.mp4").write_bytes(b"changed")
    monkeypatch.setattr(
        module.subprocess, "run", lambda *a, **k: pytest.fail("Must not launch a worker")
    )
    with pytest.raises(ValueError):
        module.execute(case.save(), native_only=True)
    assert not Path(case.protocol["outputRoot"]).exists()
