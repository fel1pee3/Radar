"""Repeated user commands preserve old SQLite/checkpoints and keep unchanged detector settings."""

import json
from contextlib import contextmanager
from pathlib import Path

import pytest
import worker
from radar_edge.config import EdgeConfig


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    base = tmp_path / ".local" / "physical-prepared"
    base.mkdir(parents=True)
    settings = EdgeConfig.model_validate(
        {
            "cameraId": "11111111-1111-4111-8111-111111111111",
            "source": {"kind": "WEBCAM", "index": 0, "authorized": True},
            "model": {
                "variant": "rtmo-s",
                "path": ".local/models/unit.onnx",
                "recovery": "RTMO_ADAPTIVE_V3",
                "runtimeProfile": "REFERENCE_4_SPIN",
            },
            "events": {"outboxPath": str(base / "outbox.sqlite")},
            "diagnostics": {"outputDirectory": str(base / "results")},
            "processing": {"maxRunSeconds": 60.0},
        }
    )
    source = base / "base.yaml"
    source.write_text("source configuration fixture", encoding="utf-8")
    return settings, source, base


def test_two_sessions_keep_old_outputs_and_detector_parameters(prepared):
    settings, source, base = prepared
    old = base / "outbox.sqlite"
    old.write_bytes(b"previous checkpoint, preserve exactly")
    result = base / "results" / "report.json"
    result.parent.mkdir()
    result.write_bytes(b"previous report")
    before = settings.model_dump()

    first, folder_a = worker.prepare_session(settings, source)
    second, folder_b = worker.prepare_session(settings, source)

    assert folder_a != folder_b
    assert first.events.outboxPath != second.events.outboxPath
    assert old.read_bytes() == b"previous checkpoint, preserve exactly"
    assert result.read_bytes() == b"previous report"
    assert settings.model_dump() == before
    for current in (first, second):
        actual = current.model_dump()
        actual["events"]["outboxPath"] = before["events"]["outboxPath"]
        actual["diagnostics"]["outputDirectory"] = before["diagnostics"]["outputDirectory"]
        assert actual == before
        assert not Path(current.events.outboxPath).exists()


def test_uuid_collision_refuses_to_touch_an_existing_session(prepared, monkeypatch):
    settings, source, _ = prepared
    monkeypatch.setattr(worker, "uuid4", lambda: "fixed-test-session")
    current, folder = worker.prepare_session(settings, source)
    marker = folder / "operator-note.txt"
    marker.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        worker.prepare_session(settings, source)
    assert marker.read_bytes() == b"keep"
    assert not Path(current.events.outboxPath).exists()


def test_invalid_reference_stops_before_any_new_session(prepared):
    settings, source, base = prepared
    settings.model.recovery = "RTMO_PREFERRED_V1"
    with pytest.raises(ValueError, match="Preserve"):
        worker.prepare_session(settings, source)
    assert not (base / "sessions").exists()


def test_execute_twice_uses_distinct_configs_without_real_camera(prepared, monkeypatch):
    from radar_edge import config, live

    settings, source, _ = prepared
    calls = []

    @contextmanager
    def fake_factory(backend, sessions):
        assert backend == "directml"
        sessions.append({"fake": True})
        yield

    def fake_live(current):
        calls.append(current)
        destination = Path(current.diagnostics.outputDirectory) / "report.json"
        destination.parent.mkdir()
        destination.write_text("{}", encoding="utf-8")
        return {"reportPath": str(destination)}, 0

    monkeypatch.setattr(config, "load_config", lambda _: settings)
    monkeypatch.setattr(worker, "experimental_factory", fake_factory)
    monkeypatch.setattr(live, "run_live", fake_live)
    assert worker.execute(source) == 0
    assert worker.execute(source) == 0
    assert len(calls) == 2
    assert calls[0].events.outboxPath != calls[1].events.outboxPath
    for current in calls:
        report = json.loads((Path(current.diagnostics.outputDirectory) / "report.json").read_text())
        assert report["experimentalExecutor"]["sourceConfig"] == str(source)
