"""Synthetic pixels and controlled clocks only; never opens a camera."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import cv2
import httpx
import numpy as np
import pytest
from temporal_support import GEOMETRY, calibration, config, observation

from radar_edge.delivery import Delivery
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime
from radar_edge.outbox import Outbox


def image(t):
    o = observation(t)
    return SimpleNamespace(
        index=o.frameIndex,
        timestamp_ms=o.timestampMs,
        bgr=np.full((60, 80, 3), 125, dtype=np.uint8),
    )


def prepare(tmp_path, monkeypatch, mode="snapshot"):
    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir(exist_ok=True)
    monkeypatch.setenv("EDGE_API_URL", "http://127.0.0.1:3001/v1")
    monkeypatch.setenv("EDGE_DEVICE_TOKEN", "FICTITIOUS-DEVICE-SECRET-78429")
    c = config()
    c.events.evidenceMode = mode
    c.events.snapshotAuthorized = mode == "snapshot"
    return c


def emit(c, frame=True):
    with EventRuntime(c, calibration(), "synthetic", GEOMETRY, async_delivery=True) as r:
        for t in range(0, 2400, 200):
            r.process(observation(t), image(t) if frame else None)
        return r.store.events(r.run["run_id"])[0]


@pytest.mark.parametrize("mode", ["none", "skeleton"])
def test_non_image_modes_never_encode_or_persist_jpeg(tmp_path, monkeypatch, mode):
    c = prepare(tmp_path, monkeypatch, mode)
    monkeypatch.setattr(cv2, "imencode", lambda *_: pytest.fail("JPEG must not be encoded"))
    e = emit(c)
    assert bool(e["pose"]) == (mode == "skeleton")
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        assert store.snapshot_summary() == []
    assert not list(tmp_path.rglob("*.jpg"))


def test_snapshot_requires_explicit_local_permission(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch)
    c.events.snapshotAuthorized = False
    with pytest.raises(EdgeError) as exc:
        emit(c)
    assert exc.value.code == "SNAPSHOT_AUTHORIZATION_REQUIRED"


def test_exact_event_frame_saved_atomically_not_later_frame(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch)
    e = emit(c)
    assert e["evidenceMode"] == "snapshot" and e["pose"]
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        row = store.db.execute("SELECT * FROM snapshots").fetchone()
        assert row["status"] == "PENDING" and row["hash"] == hashlib.sha256(row["jpeg"]).hexdigest()
        decoded = cv2.imdecode(np.frombuffer(row["jpeg"], dtype=np.uint8), cv2.IMREAD_COLOR)
        assert decoded.shape == (60, 80, 3)
        assert store.db.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 1


def test_snapshot_failure_preserves_metadata_and_does_not_capture_later(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch)
    emit(c, False)
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        assert store.summary() == {"PENDING": 1}
        row = store.db.execute("SELECT * FROM snapshots").fetchone()
        assert row["jpeg"] is None and row["status"] == "PERMANENT_ERROR"
        assert row["error_code"] == "SNAPSHOT_CAPTURE_FAILED"


def test_worker_snapshot_ack_loss_restart_then_valid_ack_removes_bytes(
    tmp_path, monkeypatch, capsys
):
    c = prepare(tmp_path, monkeypatch)
    e = emit(c)
    incident = str(uuid4())
    order = []
    bad = [True]

    def handler(req):
        order.append(req.url.path)
        if req.url.path.endswith("/snapshot"):
            ack = {
                "eventId": e["eventId"],
                "incidentId": incident,
                "hash": hashlib.sha256(req.content).hexdigest(),
                "duplicate": True,
            }
            if bad[0]:
                raise httpx.ReadError("FICTITIOUS-DEVICE-SECRET-78429")
            return httpx.Response(201, json=ack)
        return httpx.Response(
            201,
            json={
                "eventId": e["eventId"],
                "incidentId": incident,
                "receivedAt": datetime.now(UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                "duplicate": False,
                "deliveryClass": "TEST",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    current = [datetime.now(UTC).timestamp()]
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        original = store.db.execute("SELECT payload FROM outbox").fetchone()[0]
        original_jpeg = store.db.execute("SELECT jpeg FROM snapshots").fetchone()[0]
        d = Delivery(store, c.events.delivery, client=client, clock=lambda: current[0])
        d.flush()
        assert store.summary() == {"DELIVERED": 1}
        assert store.snapshot_summary()[0]["status"] == "PENDING"
    bad[0] = False
    current[0] += 60
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        Delivery(store, c.events.delivery, client=client, clock=lambda: current[0]).flush()
        assert store.snapshot_summary()[0]["status"] == "DELIVERED"
        assert store.db.execute("SELECT jpeg FROM snapshots").fetchone()[0] is None
        assert store.db.execute("SELECT payload FROM outbox").fetchone()[0] == original
    assert order == [
        "/v1/edge/events",
        f"/v1/edge/events/{e['eventId']}/snapshot",
        f"/v1/edge/events/{e['eventId']}/snapshot",
    ]
    assert all(original_jpeg not in p.read_bytes() for p in Path(".local").rglob("*.sqlite*"))
    assert "FICTITIOUS-DEVICE-SECRET-78429" not in capsys.readouterr().out


@pytest.mark.parametrize("response_status", [400, 409, 410, 422])
def test_permanent_image_error_does_not_loop_or_lose_incident(
    tmp_path, monkeypatch, response_status
):
    c = prepare(tmp_path, monkeypatch)
    e = emit(c)
    incident = str(uuid4())
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        store.update_delivery(e["eventId"], "DELIVERED", 1, 0, ack={"incidentId": incident})
        calls = []
        client = httpx.Client(
            transport=httpx.MockTransport(
                lambda r: (calls.append(r), httpx.Response(response_status))[1]
            )
        )
        d = Delivery(store, c.events.delivery, client=client)
        d.flush()
        d.flush()
        assert len(calls) == 1 and store.snapshot_summary()[0]["status"] == "PERMANENT_ERROR"
        assert store.summary() == {"DELIVERED": 1}


def test_invalid_image_ack_keeps_blob_and_expiry_preserves_pending_envelope(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch)
    e = emit(c)
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        payload = store.db.execute("SELECT payload FROM outbox").fetchone()[0]
        store.update_delivery(e["eventId"], "DELIVERED", 1, 0, ack={"incidentId": str(uuid4())})
        client = httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(201, json={"hash": "bad"}))
        )
        Delivery(store, c.events.delivery, client=client).flush()
        assert store.snapshot_summary()[0]["error_code"] == "INVALID_SNAPSHOT_ACK"
        store.update_delivery(e["eventId"], "PENDING", 1, 0)
        store.prune_confirmed(now=datetime.now(UTC) + timedelta(days=2))
        assert store.snapshot_summary()[0]["bytes"] is None
        assert store.snapshot_summary()[0]["status"] == "EXPIRED"
        assert store.db.execute("SELECT payload FROM outbox").fetchone()[0] == payload


def test_confirmed_payload_expires_but_active_episode_restores(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch, "skeleton")
    e = emit(c)
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        store.update_delivery(e["eventId"], "DELIVERED", 1, 0, ack={"synthetic": True})
        store.prune_confirmed(now=datetime.now(UTC) + timedelta(days=8))
        assert store.summary() == {}
    with EventRuntime(c, calibration(), "synthetic", GEOMETRY, async_delivery=True) as r:
        assert r.engine.state == "ACTIVE"
        for t in range(10000, 13000, 200):
            r.process(observation(t))
        assert r.generated == 0


def test_diagnostic_pose_and_logs_expire_with_size_limit_and_no_source_deletion(
    tmp_path, monkeypatch
):
    import os

    from radar_edge.retention import cleanup_diagnostics

    monkeypatch.chdir(tmp_path)
    root = Path(".local/diagnostics")
    folder = root / str(uuid4())
    folder.mkdir(parents=True)
    visual = folder / "observations.jsonl"
    visual.write_text("synthetic-pose")
    report = folder / "report.json"
    report.write_text("{}")
    source = folder / "source.mp4"
    source.write_bytes(b"preserve")
    old = datetime.now(UTC).timestamp() - 8 * 86400
    os.utime(visual, (old, old))
    result = cleanup_diagnostics(str(root), max_bytes=1)
    assert result["removed"] == 2 and source.read_bytes() == b"preserve"
    assert cleanup_diagnostics(str(root))["removed"] == 0


def test_snapshot_quota_preserves_metadata_without_second_image_queue(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch)
    with EventRuntime(c, calibration(), "synthetic", GEOMETRY, async_delivery=True) as r:
        with r.store.transaction():
            for _ in range(100):
                e, ep = str(uuid4()), str(uuid4())
                r.store.db.execute(
                    "INSERT INTO episodes VALUES(?,?,?,?,NULL)", (ep, r.run["run_id"], e, "CLOSED")
                )
                r.store.db.execute(
                    "INSERT INTO snapshots(event_id,jpeg,created_at,expires_at) VALUES(?,?,?,?)",
                    (
                        e,
                        b"synthetic",
                        datetime.now(UTC).isoformat(),
                        (datetime.now(UTC) + timedelta(days=1)).isoformat(),
                    ),
                )
        for t in range(0, 2400, 200):
            r.process(observation(t), image(t))
        event = r.store.events(r.run["run_id"])[0]
        row = r.store.db.execute(
            "SELECT * FROM snapshots WHERE event_id=?", (event["eventId"],)
        ).fetchone()
        assert row["jpeg"] is None and row["error_code"] == "SNAPSHOT_STORAGE_FULL"
        assert r.store.summary() == {"PENDING": 1}


def test_snapshot_revoked_auth_requires_explicit_resume(tmp_path, monkeypatch):
    c = prepare(tmp_path, monkeypatch)
    e = emit(c)
    incident = str(uuid4())
    code = [401]
    calls = []

    def handle(req):
        calls.append(1)
        return httpx.Response(
            code[0],
            json={
                "eventId": e["eventId"],
                "incidentId": incident,
                "hash": hashlib.sha256(req.content).hexdigest(),
                "duplicate": True,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handle))
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        store.update_delivery(e["eventId"], "DELIVERED", 1, 0, ack={"incidentId": incident})
        sender = Delivery(store, c.events.delivery, client=client)
        sender.flush()
        assert store.snapshot_summary()[0]["status"] == "AUTH_BLOCKED"
        code[0] = 201
        sender.flush()
        assert len(calls) == 1
        sender.flush(resume_auth=True)
        assert store.snapshot_summary()[0]["status"] == "DELIVERED"
