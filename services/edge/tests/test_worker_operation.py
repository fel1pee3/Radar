"""Operation selection and duration preparation without capture or HTTP."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/validation" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "executor,project", [("CPU", "services/edge"), ("DIRECTML", "experiments/directml")]
)
def test_worker_environment_is_explicit(monkeypatch, executor, project):
    m = script("select-worker.py")
    monkeypatch.setattr(
        m,
        "load_config",
        lambda _: SimpleNamespace(cameraId="camera", model=SimpleNamespace(executor=executor)),
    )
    selection = m.arguments(Path(".local/private.yaml"))
    assert selection["project"] == project and not selection["sourceOpened"]
    assert selection["arguments"][2] == project
    assert "--frozen" in selection["arguments"]


@pytest.mark.parametrize("duration", [60, 600])
def test_prepare_preserves_original_and_short_option(tmp_path, monkeypatch, duration):
    from test_live_health import live_config

    m = script("prepare-directml-demo.py")
    c = live_config()
    c.model.recovery = "RTMO_ADAPTIVE_V3"
    c.model.runtimeProfile = "REFERENCE_4_SPIN"
    base = tmp_path / "base.yaml"
    base.write_text("original")
    output = tmp_path / "prepared"
    calls = []
    monkeypatch.setattr(m, "load_config", lambda _: c)
    monkeypatch.setattr(m, "private_path", lambda value: Path(value))
    monkeypatch.setattr(m, "credentials", lambda *args: calls.append("local credential validation"))
    monkeypatch.setattr(m, "check_posture", lambda _: calls.append("local posture validation"))
    m.prepare(base, ".local/private.json", str(output), duration)
    assert c.processing.maxRunSeconds == duration
    assert c.events.delivery.enabled and not c.events.snapshotAuthorized
    assert c.events.evidenceMode == "skeleton"
    assert c.model.executor == "DIRECTML"
    assert base.read_text() == "original"
    assert calls == ["local credential validation", "local posture validation"]
    with pytest.raises(ValueError, match="Destino existente"):
        m.prepare(base, ".local/private.json", str(output), duration)
