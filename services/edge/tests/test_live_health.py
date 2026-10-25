"""Controlled clocks/current health; no camera or historical heartbeat queue."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from temporal_support import GEOMETRY, calibration, config, observation

from radar_edge.config import EdgeConfig
from radar_edge.delivery import Delivery, valid_ack
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime
from radar_edge.health import LiveHealth


def live_config():
    return EdgeConfig.model_validate(
        {
            "cameraId": config().cameraId,
            "purpose": "RADAR_LIVE_POSE",
            "source": {"kind": "WEBCAM", "index": 0, "authorized": True},
            "model": {"variant": "full", "path": ".local/models/pose_landmarker_full.task"},
            "events": {"enabled": True, "outboxPath": ".local/live.sqlite"},
        }
    )


def test_stalled_inference_is_not_healthy_and_pause_is_explicit():
    clock = [0.0]
    h = LiveHealth(live_config(), str(uuid4()), calibration(), clock=lambda: clock[0])
    assert "FRAME_TIMEOUT" in h.snapshot()["qualityFlags"]
    h.observation(observation(0))
    assert not h.snapshot()["qualityFlags"]
    clock[0] = 6.0
    assert {"FRAME_TIMEOUT", "LOW_FPS"} <= set(h.snapshot()["qualityFlags"])
    h.update(capture="PAUSED", flags=set())
    assert h.snapshot()["captureState"] == "PAUSED"


def test_replay_analysis_fps_uses_scene_time_instead_of_playback_wall_time():
    clock = [0.0]
    h = LiveHealth(config(), str(uuid4()), calibration(), clock=lambda: clock[0])
    for t in range(0, 1200, 200):
        clock[0] = t / 1000 * 2  # Half-speed playback: 2.5 observations/s on the wall clock.
        h.observation(observation(t))
    assert h.snapshot()["analysisFps"] == 5.0
    assert h.snapshot()["mode"] == "REPLAY"
    assert "LOW_FPS" not in h.snapshot()["qualityFlags"]


def test_live_payload_and_restart_preserve_episode_but_new_capture_session(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    c = live_config()
    with EventRuntime(c, calibration(), "WEBCAM", GEOMETRY, async_delivery=True) as r:
        capture = r.capture_run_id
        for t in range(0, 2400, 200):
            r.process(replace(observation(t), mode="LIVE"))
        event = r.store.events(r.run["run_id"])[0]
        assert event["mode"] == "LIVE" and event["sourceOffsetMs"] is None
        assert event["runId"] == capture and r.engine.state == "ACTIVE"
        original = r.store.db.execute("SELECT payload FROM outbox").fetchone()[0]
    with EventRuntime(c, calibration(), "WEBCAM", GEOMETRY, async_delivery=True) as r:
        assert r.capture_run_id != capture and r.engine.state == "ACTIVE"
        for t in range(10000, 14000, 200):
            r.process(replace(observation(t), mode="LIVE"))
        assert r.generated == 0
        assert r.store.db.execute("SELECT payload FROM outbox").fetchone()[0] == original


def test_capacity_stops_before_event_and_preserves_pending_and_prune_active(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    c = live_config()
    c.events.delivery.maxItems = 1
    with EventRuntime(c, calibration(), "WEBCAM", GEOMETRY) as r:
        for t in range(0, 2200, 200):
            r.process(replace(observation(t), mode="LIVE"))
        assert r.store.summary() == {"PENDING": 1}
        with pytest.raises(EdgeError, match="limite") as exc:
            r.process(observation(2400))
        assert exc.value.code == "STORAGE_FULL" and r.store.summary() == {"PENDING": 1}
        r.store.prune_confirmed()
        assert r.store.summary() == {"PENDING": 1}
        row = r.store.db.execute("SELECT event_id FROM outbox").fetchone()[0]
        r.store.update_delivery(row, "DELIVERED", 1, 0, ack={"synthetic": True})
        r.store.db.execute("UPDATE outbox SET delivered_at='2000-01-01T00:00:00.000Z'")
        r.store.db.commit()
        r.store.prune_confirmed()
        assert (
            r.store.summary() == {}
        )  # Confirmed visual payload expires; active checkpoint survives.
        assert r.engine.state == "ACTIVE"
        r.store.reset("synthetic_closed")
        r.store.prune_confirmed()
        assert r.store.summary() == {}
        assert r.store.db.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 1


def test_ack_accepts_live_classes_but_never_test_as_live():
    event = str(uuid4())
    ack = {
        "eventId": event,
        "incidentId": str(uuid4()),
        "duplicate": False,
        "receivedAt": "2026-10-21T12:00:00.000Z",
        "deliveryClass": "DELAYED",
    }
    assert valid_ack(ack, event, 201, "LIVE")
    assert not valid_ack(ack, event, 201, "REPLAY")
    assert not valid_ack({**ack, "deliveryClass": "TEST"}, event, 201, "LIVE")


def test_http_date_retry_and_jitter_are_bounded(tmp_path, monkeypatch):
    from email.utils import format_datetime

    import httpx

    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    monkeypatch.setenv("EDGE_API_URL", "http://127.0.0.1:3001/v1")
    monkeypatch.setenv("EDGE_DEVICE_TOKEN", "synthetic-private-token-for-retry")
    c = live_config()
    now = datetime.now(UTC).replace(microsecond=0)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                429, headers={"Retry-After": format_datetime(now + timedelta(seconds=20))}
            )
        )
    )
    with EventRuntime(c, calibration(), "WEBCAM", GEOMETRY) as r:
        for t in range(0, 2200, 200):
            r.process(replace(observation(t), mode="LIVE"))
        d = Delivery(
            r.store, c.events.delivery, client, clock=lambda: now.timestamp(), jitter=lambda a, b: b
        )
        d.flush()
        row = r.store.db.execute("SELECT * FROM outbox").fetchone()
        assert row["next_attempt"] == now.timestamp() + 20 and row["status"] == "PENDING"
    client.close()


def test_heartbeat_advances_while_event_http_and_inference_are_stalled(tmp_path, monkeypatch):
    import json
    import threading

    import httpx

    from radar_edge.health import NetworkWorker

    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    monkeypatch.setenv("EDGE_API_URL", "http://127.0.0.1:3001/v1")
    monkeypatch.setenv("EDGE_DEVICE_TOKEN", "synthetic-private-thread-token")
    c = live_config()
    c.events.delivery.enabled = True
    entered, release, degraded = threading.Event(), threading.Event(), threading.Event()
    heartbeats = []
    clock = [0.0]
    health = LiveHealth(c, str(uuid4()), calibration(), clock=lambda: clock[0])
    real_client = httpx.Client

    def handle(request):
        if request.url.path.endswith("/events"):
            entered.set()
            assert release.wait(4)
            raise httpx.ReadTimeout("Synthetic blocked POST")
        value = json.loads(request.content)
        heartbeats.append(value)
        if "LOW_FPS" in value["qualityFlags"]:
            degraded.set()
        return httpx.Response(200, json={"accepted": True, "ignored": False})

    monkeypatch.setattr(
        "radar_edge.health.httpx.Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs),
    )
    with EventRuntime(c, calibration(), "WEBCAM", GEOMETRY, async_delivery=True) as r:
        for t in range(0, 2200, 200):
            r.process(replace(observation(t), mode="LIVE"))
        network = NetworkWorker(c, health).__enter__()
        try:
            assert entered.wait(2)
            # No inference progress; acquisition/inference health cannot stay healthy.
            clock[0] = 6.0
            assert degraded.wait(2)
            assert heartbeats[-1]["qualityFlags"] == ["FRAME_TIMEOUT", "LOW_FPS"]
            assert not release.is_set()  # Heartbeat was sent before the POST unblocked.
        finally:
            release.set()
            network.close()
        assert heartbeats[-1]["captureState"] == "ENDED"
        assert [h["sequence"] for h in heartbeats] == list(range(1, len(heartbeats) + 1))
        assert r.store.summary() == {"PENDING": 1}


@pytest.mark.parametrize("status_failure", [False, True])
def test_live_terminal_pause_resume_stop_does_not_wait_on_released_capture(
    tmp_path, monkeypatch, status_failure
):
    from time import monotonic_ns
    from types import SimpleNamespace

    import numpy as np

    from radar_edge.live import run_live
    from radar_edge.source import Frame

    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    c = live_config()
    c.processing.preview = False
    c.diagnostics.exportDecisions = True
    floor = {
        **calibration(),
        "cameraId": c.cameraId,
        "geometry": vars(GEOMETRY),
        "sourceKind": "WEBCAM",
        "deviceIndex": 0,
    }
    monkeypatch.setattr("radar_edge.live.load_calibration", lambda _: floor)
    clock = [100.0]
    waits, actions = [], []
    commands = iter(
        [
            None,
            None,
            {"id": "p", "action": "pause"},
            {"id": "r", "action": "resume"},
            {"id": "s", "action": "stop"},
        ]
    )
    monkeypatch.setattr("radar_edge.live._control", lambda _: next(commands))
    monkeypatch.setattr("radar_edge.live.monotonic", lambda: clock[0])

    def wait(seconds):
        waits.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr("radar_edge.live.sleep", wait)

    class Source:
        def __init__(self, *_):
            self.start_utc = datetime.now(UTC)
            self.info = [0] * 14
            self.index = 0
            self.state = "RUNNING"
            self.exhausted = False
            self.stop = SimpleNamespace(wait=lambda _: pytest.fail("Capture stop is already set"))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

        def read(self):
            assert self.state == "RUNNING"
            self.last_acquired_ns = self.info[2] = self.info[12] = monotonic_ns()
            self.info[0], self.info[13] = 1, 128
            frame = Frame(
                self.index,
                self.index * 200,
                "HOST_MONOTONIC",
                np.full((GEOMETRY.height, GEOMETRY.width, 3), 128, dtype=np.uint8),
                GEOMETRY,
            )
            self.index += 1
            return frame

        snapshot = read

        def pause(self):
            actions.append("pause")
            self.state = "PAUSED"

        def resume(self):
            actions.append("resume")
            self.state = "RUNNING"

        def metadata(self):
            return {"kind": "SYNTHETIC_ADAPTER", "captureState": self.state}

        def close(self):
            self.state = "ENDED"

    class Estimator:
        def __init__(self, *_):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def estimate(self, frame):
            return observation(frame.timestamp_ms).poses, 1.0

    monkeypatch.setattr("radar_edge.live.WebcamSource", Source)
    monkeypatch.setattr("radar_edge.estimator.MediaPipeEstimator", Estimator)
    if status_failure:

        def fail_status(*_):
            raise RuntimeError("synthetic-private-status-secret")

        monkeypatch.setattr("radar_edge.live.publish_status", fail_status)
    report, code = run_live(c)
    import json

    trace = [
        json.loads(line) for line in Path(report["decisionExport"]["path"]).read_text().splitlines()
    ]
    assert trace[0]["capture"] == "OPENING"
    assert trace[-1]["capture"] == report["captureState"]
    assert "synthetic-private-status-secret" not in json.dumps(trace)
    if status_failure:
        assert code == 1 and report["captureState"] == "ERROR"
        assert report["error"]["code"] == "PROCESSING_ERROR"
        assert report["error"]["diagnostic"]["exceptionType"] == "RuntimeError"
        assert "synthetic-private-status-secret" not in json.dumps(report)
        assert report["heartbeat"]["captureState"] == "ERROR"
        assert "CAPTURE_ERROR" not in report["heartbeat"]["qualityFlags"]
        assert report["metrics"]["analyzedFrames"] == 0
        return
    assert code == 0 and report["error"] is None
    assert actions == ["pause", "resume"] and waits == [0.02, 0.02]
    assert any(row.get("capture") == "PAUSED" for row in trace)
    assert len([row for row in trace if row["recordType"] == "DECISION"]) == 1
    assert report["metrics"]["analyzedFrames"] == 1  # No analysis during the paused interval.
