"""New executor and exit regressions. Synthetic adapters never open a webcam."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic_ns

import numpy as np
import pytest
from temporal_support import GEOMETRY, calibration, observation
from test_live_health import live_config

from radar_edge.config import ModelConfig
from radar_edge.errors import EdgeError
from radar_edge.estimator import create_estimator
from radar_edge.event_runtime import EventRuntime
from radar_edge.live import run_live
from radar_edge.source import Frame


def test_directml_wrong_environment_is_explicit_without_cpu_substitution(monkeypatch):
    from radar_edge import directml

    monkeypatch.setattr(directml.metadata, "distributions", lambda: [])
    estimator = create_estimator(
        ".local/weights.onnx", "rtmo-s", "RTMO_ADAPTIVE_V3", executor="DIRECTML"
    )
    with pytest.raises(EdgeError) as error:
        estimator.__enter__()
    assert error.value.code == "DIRECTML_INITIALIZATION_FAILED"
    assert estimator.session is None and ModelConfig().executor == "CPU"
    with pytest.raises(ValueError):
        ModelConfig(executor="DIRECTML")


def test_capture_anchor_and_immutable_resume(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = live_config()
    origin = datetime.now(UTC) - timedelta(seconds=10)
    with EventRuntime(c, calibration(), "WEBCAM", GEOMETRY, capture_origin_utc=origin) as r:
        for t in range(2000, 4400, 200):
            r.process(replace(observation(t), mode="LIVE"))
        event = r.store.events(r.run["run_id"])[0]
        detected = datetime.fromisoformat(event["detectedAt"].replace("Z", "+00:00"))
        assert detected < datetime.now(UTC)
        assert abs((detected - origin).total_seconds() - 4) < 0.002
        created = datetime.fromisoformat(r.run["created_at"].replace("Z", "+00:00"))
        assert (created - origin).total_seconds() > 9
        anchor = r.run["anchor"]
        raw = r.store.db.execute("SELECT payload FROM outbox").fetchone()[0]
    with EventRuntime(
        c, calibration(), "WEBCAM", GEOMETRY, capture_origin_utc=datetime.now(UTC)
    ) as r:
        assert r.resumed and r.run["anchor"] == anchor
        assert r.store.db.execute("SELECT payload FROM outbox").fetchone()[0] == raw


@pytest.mark.parametrize("ending", ["preview", "interrupt", "limit", "duration"])
def test_last_decision_profile_final_health_and_pending(tmp_path, monkeypatch, ending):
    monkeypatch.chdir(tmp_path)
    c = live_config()
    c.processing.maxObservations = 12 if ending == "limit" else None
    c.processing.maxRunSeconds = 3.0 if ending == "duration" else None
    c.diagnostics.exportDecisions = c.diagnostics.profileProcessing = True
    floor = {
        **calibration(),
        "cameraId": c.cameraId,
        "geometry": vars(GEOMETRY),
        "sourceKind": "WEBCAM",
        "deviceIndex": 0,
    }
    monkeypatch.setattr("radar_edge.live.load_calibration", lambda _: floor)
    clock = [100.0]
    monkeypatch.setattr("radar_edge.live.monotonic", lambda: clock[0])
    monkeypatch.setattr("radar_edge.live.sleep", lambda dt: clock.__setitem__(0, clock[0] + dt))
    monkeypatch.setattr("radar_edge.live._control", lambda _: None)

    class Source:
        def __init__(self, *_):
            self.start_utc = datetime.now(UTC) - timedelta(seconds=5)
            self.info, self.index, self.exhausted, self.state = [0.0] * 14, 0, False, "RUNNING"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

        def read(self):
            self.last_acquired_ns = self.info[2] = self.info[12] = monotonic_ns()
            self.info[0], self.info[13] = 1, 128
            f = Frame(
                self.index,
                self.index * 200,
                "HOST_MONOTONIC",
                np.full((360, 640, 3), 128, dtype=np.uint8),
                GEOMETRY,
            )
            self.index += 1
            clock[0] += 0.201
            return f

        snapshot = read

        def close(self):
            self.state = "ENDED"

        def metadata(self):
            return {"captureState": self.state}

    class Estimator:
        def __init__(self, *_):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def estimate(self, f):
            return observation(f.timestamp_ms).poses, 1.0

    class Preview:
        def __init__(self, *_):
            self.count, self.paused_seconds = 0, 0.0

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def poll(self):
            return True

        def show(self, *_):
            self.count += 1
            if self.count == 12:
                if ending == "interrupt":
                    raise KeyboardInterrupt()
                if ending == "preview":
                    return False
            return True

    monkeypatch.setattr("radar_edge.live.WebcamSource", Source)
    monkeypatch.setattr("radar_edge.estimator.MediaPipeEstimator", Estimator)
    monkeypatch.setattr("radar_edge.live.LocalPreview", Preview)
    r, code = run_live(c)
    assert code == (130 if ending == "interrupt" else 0)
    rows = [json.loads(x) for x in Path(r["decisionExport"]["path"]).read_text().splitlines()]
    ds = [x["timestampMs"] for x in rows if x["recordType"] == "DECISION"]
    ps = [x["timestampMs"] for x in rows if x["recordType"] == "PROCESSING_PROFILE"]
    assert len(ds) >= 12 and ds == ps
    assert (
        r["stopReason"]
        == {
            "preview": "PREVIEW_EXIT",
            "interrupt": "KEYBOARD_INTERRUPT",
            "limit": "MAX_OBSERVATIONS",
            "duration": "MAX_RUN_SECONDS",
        }[ending]
    )
    final = json.loads(Path(f".local/edge-control/{c.cameraId}-status.json").read_text())
    assert final["final"] and final["heartbeat"]["outboxPending"] == 1
    assert r["source"]["captureState"] == r["heartbeat"]["captureState"] == "ENDED"
    assert r["heartbeat"]["outboxPending"] == 1 and r["temporal"]["outbox"] == {"PENDING": 1}


def test_failed_directml_metadata_never_claims_cpu():
    from radar_edge.estimator import executed_model_metadata
    from radar_edge.model import get_model_spec

    result = executed_model_metadata(get_model_spec("rtmo-s"), None, "DIRECTML")
    assert result["delegate"] is None
    assert result["executor"]["initialized"] is False
    assert result["executor"]["providers"] == []


def test_network_cleanup_stops_even_if_final_database_query_fails(monkeypatch):
    import sqlite3

    from radar_edge.health import LiveHealth, NetworkWorker

    h = LiveHealth(live_config(), "synthetic-run", calibration())

    def fail():
        raise sqlite3.OperationalError("synthetic database failure")

    monkeypatch.setattr(h, "refresh_pending", fail)
    worker = NetworkWorker(live_config(), h)
    with pytest.raises(sqlite3.OperationalError):
        worker.close()
    assert worker.stop.is_set()
    worker.close()  # idempotent cleanup does not repeat the failed read
