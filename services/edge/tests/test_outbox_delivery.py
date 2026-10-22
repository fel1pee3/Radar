import json
import sqlite3
from uuid import uuid4

import httpx
import pytest
from temporal_support import CAMERA, GEOMETRY, calibration, config, observation

from radar_edge.config import DeliveryConfig
from radar_edge.delivery import Delivery
from radar_edge.engine import TemporalEngine
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime, event_payload
from radar_edge.features import extract_features
from radar_edge.outbox import FileLock, Outbox


@pytest.fixture
def local(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".local").mkdir()
    monkeypatch.setenv("EDGE_API_URL", "http://127.0.0.1:3001/v1")
    monkeypatch.setenv("EDGE_DEVICE_TOKEN", "Synthetic-Token-Should-Not-Appear")
    return config()


def create_event(store):
    run, _ = store.execution("synthetic")
    engine = TemporalEngine()
    value = None
    for t in range(0, 2200, 200):
        o = observation(t)
        f = extract_features(o, calibration()["floorPolygon"])
        emission = engine.step(f)
        if emission:
            value = event_payload(o, f, emission, run, engine.policy, "skeleton")
        store.checkpoint(run["run_id"], o, engine, value)
    return run, value


def test_atomic_episode_event_and_checkpoint_rollback(local):
    with Outbox(local.events.outboxPath, CAMERA) as store:
        run, _ = store.execution("synthetic")
        store.db.execute(
            "CREATE TRIGGER reject_event BEFORE INSERT ON outbox "
            "BEGIN SELECT RAISE(ABORT,'injected disk failure'); END;"
        )
        store.db.commit()
        engine = TemporalEngine()
        for t in range(0, 2000, 200):
            engine.step(extract_features(observation(t), calibration()["floorPolygon"]))
        o = observation(2000)
        f = extract_features(o, calibration()["floorPolygon"])
        e = engine.step(f)
        with pytest.raises(sqlite3.Error):
            store.checkpoint(
                run["run_id"], o, engine, event_payload(o, f, e, run, engine.policy, "skeleton")
            )
        assert store.db.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 0
        assert store.summary() == {}
        assert store.execution("synthetic")[0]["frame_index"] == -1


def test_restart_payload_stable_checkpoint_and_explicit_reset_history(local):
    c = local
    with EventRuntime(c, calibration(), "hash", GEOMETRY) as runtime:
        for t in range(0, 4000, 200):
            runtime.process(observation(t))
        assert runtime.generated == 1
        event = runtime.store.events(runtime.run["run_id"])[0]
        run_id = runtime.run["run_id"]
    with EventRuntime(c, calibration(), "hash", GEOMETRY) as runtime:
        assert runtime.resumed and runtime.run["frame_index"] == 19
        assert runtime.run["run_id"] == run_id and runtime.engine.state == "ACTIVE"
        for t in range(4000, 5000, 200):
            runtime.process(observation(t, False))
    with EventRuntime(c, calibration(), "hash", GEOMETRY) as runtime:
        assert runtime.engine.state == "ACTIVE"
        for t in range(5000, 8000, 200):
            runtime.process(observation(t, False))
        assert runtime.engine.state == "REARMING"
        runtime.process(observation(8000, False))
        for t in range(8200, 10600, 200):
            runtime.process(observation(t))
        events = runtime.store.events(run_id)
        assert len(events) == 2 and events[0] == event
        assert events[0]["eventId"] != events[1]["eventId"]
        with pytest.raises(sqlite3.Error):
            runtime.store.db.execute("UPDATE outbox SET payload='{}'")
        runtime.store.db.rollback()
        runtime.store.reset("intentional_evaluation")
        assert runtime.store.db.execute("SELECT COUNT(*) FROM resets").fetchone()[0] == 1
        new, _ = runtime.store.execution("new-context")
        assert new["run_id"] != run_id and len(runtime.store.events(run_id)) == 2


def test_storage_failure_is_visible_and_no_http_after_failed_commit(local):
    with EventRuntime(local, calibration(), "hash", GEOMETRY) as runtime:
        runtime.store.db.execute(
            "CREATE TRIGGER fail BEFORE UPDATE ON executions BEGIN SELECT RAISE(ABORT,'disk'); END;"
        )
        runtime.store.db.commit()
        with pytest.raises(EdgeError, match="persistir") as exc:
            runtime.process(observation(0))
        assert exc.value.code == "STORAGE_ERROR"


def test_summary_distinguishes_initial_and_committed_checkpoint_after_resume(local):
    with EventRuntime(local, calibration(), "hash", GEOMETRY) as runtime:
        initial = runtime.summary()
        assert initial["initialCheckpointFrame"] == -1
        assert initial["lastPersistedCheckpointFrame"] == -1
        assert initial["lastPersistedCheckpointTimestampMs"] == -1
        for t in range(0, 1400, 200):
            runtime.process(observation(t))
        current = runtime.summary()
        assert current["initialCheckpointFrame"] == -1
        assert current["lastPersistedCheckpointFrame"] == 6
        assert current["lastPersistedCheckpointTimestampMs"] == 1200

    with EventRuntime(local, calibration(), "hash", GEOMETRY) as runtime:
        runtime.process(observation(1400))
        resumed = runtime.summary()
        assert resumed["initialCheckpointFrame"] == 6
        assert resumed["lastPersistedCheckpointFrame"] == 7
        assert resumed["lastPersistedCheckpointTimestampMs"] == 1400
        runtime.store.db.execute(
            "CREATE TRIGGER fail BEFORE UPDATE ON executions BEGIN SELECT RAISE(ABORT,'disk'); END;"
        )
        runtime.store.db.commit()
        with pytest.raises(EdgeError):
            runtime.process(observation(1600))
        failed = runtime.summary()
        assert failed["initialCheckpointFrame"] == 6
        assert failed["lastPersistedCheckpointFrame"] == 7
        assert failed["lastPersistedCheckpointTimestampMs"] == 1400


def test_conflicting_source_or_camera_requires_reset_and_preserves_history(local):
    with Outbox(local.events.outboxPath, CAMERA) as store:
        store.execution("hash-1")
        with pytest.raises(EdgeError) as exc:
            store.execution("hash-2")
        assert exc.value.code == "SOURCE_CONFIG_CONFLICT"
    with pytest.raises(EdgeError) as exc:
        with Outbox(local.events.outboxPath, str(uuid4())):
            pass
    assert exc.value.code == "OUTBOX_CAMERA_CONFLICT"


def test_same_camera_different_outboxes_and_same_outbox_are_exclusive(local):
    with EventRuntime(local, calibration(), "hash", GEOMETRY):
        other = local.model_copy(deep=True)
        other.events.outboxPath = ".local/other.sqlite"
        with pytest.raises(EdgeError) as exc:
            with EventRuntime(other, calibration(), "hash", GEOMETRY):
                pass
        assert exc.value.code == "WORKER_LOCKED"
        with pytest.raises(EdgeError):
            with FileLock(__import__("pathlib").Path(local.events.outboxPath + ".lock")):
                pass


def ack(event, status=201, **changes):
    return {
        "eventId": event["eventId"],
        "incidentId": str(uuid4()),
        "receivedAt": "2026-10-21T12:00:00.000Z",
        "duplicate": status == 200,
        "deliveryClass": "TEST",
        **changes,
    }


def test_timeout_after_commit_reuses_identical_bytes_and_valid_ack(local):
    with Outbox(local.events.outboxPath, CAMERA) as store:
        _, event = create_event(store)
        sent = []
        clock = [100.0]

        def handler(request):
            sent.append(request.content)
            if len(sent) == 1:
                raise httpx.ReadTimeout("Synthetic transport failure", request=request)
            return httpx.Response(200, json=ack(event, 200))

        client = httpx.Client(transport=httpx.MockTransport(handler))
        delivery = Delivery(store, DeliveryConfig(), client, clock=lambda: clock[0])
        assert delivery.flush() == {"PENDING": 1}
        delivery.flush()
        assert len(sent) == 1
        clock[0] += 2
        assert delivery.flush() == {"DELIVERED": 1}
        assert len(sent) == 2 and sent[0] == sent[1]
        assert json.loads(sent[0]) == event
        assert store.db.execute("SELECT attempts FROM outbox").fetchone()[0] == 2
        client.close()


@pytest.mark.parametrize(
    "status,expected",
    [
        (408, "PENDING"),
        (429, "PENDING"),
        (500, "PENDING"),
        (503, "PENDING"),
        (400, "PERMANENT_ERROR"),
        (409, "PERMANENT_ERROR"),
        (410, "PERMANENT_ERROR"),
        (422, "PERMANENT_ERROR"),
        (401, "AUTH_BLOCKED"),
        (403, "AUTH_BLOCKED"),
        (302, "PERMANENT_ERROR"),
    ],
)
def test_delivery_error_classes_persist_and_never_retry_permanent(local, status, expected):
    with Outbox(local.events.outboxPath, CAMERA) as store:
        create_event(store)
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(
                status,
                headers={"Retry-After": "30"},
                json={"secret": "Must not persist error body"},
            )

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            delivery = Delivery(store, DeliveryConfig(), client, clock=lambda: 100.0)
            assert delivery.flush() == {expected: 1}
            delivery.flush()
            assert len(calls) == 1
            row = store.db.execute("SELECT * FROM outbox").fetchone()
            assert "secret" not in (row["error_code"] or "") and row["ack"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"eventId": str(uuid4())},
        {"deliveryClass": "CURRENT"},
        {"receivedAt": "bad"},
        {"duplicate": True},
        {"incidentId": "bad"},
    ],
)
def test_invalid_ack_never_marks_delivered(local, changes):
    with Outbox(local.events.outboxPath, CAMERA) as store:
        _, event = create_event(store)
        with httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(201, json=ack(event, **changes)))
        ) as client:
            assert Delivery(store, DeliveryConfig(), client, clock=lambda: 100.0).flush() == {
                "PENDING": 1
            }
            assert store.db.execute("SELECT error_code FROM outbox").fetchone()[0] == "INVALID_ACK"


def test_auth_requires_explicit_resume_and_evidence_none(local):
    c = local
    c.events.evidenceMode = "none"
    with EventRuntime(c, calibration(), "hash", GEOMETRY) as runtime:
        for t in range(0, 2200, 200):
            runtime.process(observation(t))
        event = runtime.store.events(runtime.run["run_id"])[0]
        assert event["pose"] == []
        calls = []

        def handler(r):
            calls.append(1)
            return (
                httpx.Response(401)
                if len(calls) == 1
                else httpx.Response(200, json=ack(event, 200))
            )

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            delivery = Delivery(runtime.store, DeliveryConfig(), client, clock=lambda: 100.0)
            assert delivery.flush() == {"AUTH_BLOCKED": 1}
            assert delivery.flush() == {"AUTH_BLOCKED": 1} and len(calls) == 1
            assert delivery.flush(resume_auth=True) == {"DELIVERED": 1}
