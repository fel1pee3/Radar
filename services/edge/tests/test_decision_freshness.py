"""Injected clock interruptions, never physical suspension or camera evidence."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from temporal_support import CAMERA, GEOMETRY, calibration, config, observation

from radar_edge.config import DeliveryConfig
from radar_edge.delivery import Delivery
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime
from radar_edge.freshness import delivery_freshness
from radar_edge.outbox import Outbox


class Clock:
    session_id = "deterministic-test-process"

    def __init__(self):
        self.ns = 10**12
        self.wall = 0.0

    def monotonic_ns(self):
        return self.ns

    def time(self):
        return self.wall

    def advance(self, ms, wall_ms=None):
        self.ns += round(ms * 1e6)
        self.wall += (ms if wall_ms is None else wall_ms) / 1000


@pytest.fixture
def local(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".local").mkdir()
    monkeypatch.setenv("EDGE_API_URL", "http://127.0.0.1:3001/v1")
    monkeypatch.setenv("EDGE_DEVICE_TOKEN", "Synthetic-Local-Token-Never-Logged")
    return config()


def begin(runtime, clock):
    clock.wall = datetime.fromisoformat(runtime.run["anchor"].replace("Z", "+00:00")).timestamp()


def feed(runtime, clock, start, end):
    for t in range(start, end, 200):
        if t:
            clock.advance(200)
        runtime.process(observation(t, mode="LIVE"), acquired_ns=clock.ns)


def sender(runtime, clock, received):
    def transport(request):
        received.append((request.content, request.headers.get("x-radar-delivery-state")))
        event = json.loads(request.content)
        return httpx.Response(
            201,
            json={
                "eventId": event["eventId"],
                "incidentId": str(uuid4()),
                "receivedAt": datetime.fromtimestamp(clock.time(), UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                "duplicate": False,
                "deliveryClass": request.headers.get("x-radar-delivery-state", "CURRENT"),
            },
        )

    return Delivery(
        runtime.store,
        DeliveryConfig(enabled=True),
        client=httpx.Client(transport=httpx.MockTransport(transport)),
        clock=clock.time,
        freshness_clock=clock.time,
        jitter=lambda *_: 1,
        monotonic_clock=clock.monotonic_ns,
        clock_session=clock.session_id,
    )


def test_stale_frame_before_engine_cannot_finish_old_suspicion(local):
    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2000)
        clock.advance(200)
        acquired = clock.ns
        clock.advance(3000)
        f = runtime.process(observation(2000, mode="LIVE"), acquired_ns=acquired)
        assert not f.eligible and runtime.generated == 0
        assert runtime.engine.start is None
        assert (
            runtime.store.db.execute("SELECT reason FROM timing_audit").fetchone()[0]
            == "STALE_BEFORE_DECISION"
        )
        feed(runtime, clock, 2200, 4200)
        assert runtime.generated == 0
        feed(runtime, clock, 4200, 4400)
        assert runtime.generated == 1


def test_interruption_before_checkpoint_does_not_persist_tentative_event(local, monkeypatch):
    import radar_edge.event_runtime as module

    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2000)
        original = module.event_payload

        def slow_payload(*args, **kwargs):
            value = original(*args, **kwargs)
            clock.advance(2100)
            return value

        monkeypatch.setattr(module, "event_payload", slow_payload)
        feed(runtime, clock, 2000, 2200)
        assert runtime.store.summary() == {}
        assert runtime.engine.state == "OBSERVING"
        assert runtime.engine.start is None


def test_suspend_inside_transaction_preserves_commit_and_downgrades_delivery(local):
    clock, received = Clock(), []
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2000)
        original = runtime.store.transaction
        inject = [True]

        @contextmanager
        def paused_commit():
            with original():
                yield
                if inject[0]:
                    inject[0] = False
                    clock.advance(125000)

        runtime.store.transaction = paused_commit
        feed(runtime, clock, 2000, 2200)
        row = runtime.store.db.execute("SELECT * FROM outbox").fetchone()
        payload = row["payload"]
        assert runtime.generated == 1 and runtime.engine.state == "ACTIVE"
        assert runtime.store.delivery_timing(row["event_id"]) is not None
        audit = runtime.store.db.execute(
            "SELECT * FROM timing_audit WHERE stage='AFTER_CHECKPOINT'"
        ).fetchone()
        assert audit["checkpoint_outcome"] == "COMMITTED"
        assert runtime.previous_features is not None and not runtime.previous_features.eligible
        dispatch = sender(runtime, clock, received)
        assert dispatch.flush() == {"DELIVERED": 1}
        assert received == [(payload.encode(), "DELAYED")]
        assert runtime.store.db.execute("SELECT payload FROM outbox").fetchone()[0] == payload
        feed(runtime, clock, 2200, 3000)
        assert runtime.generated == 1  # Uncertainty never rearms an active episode.


def test_interruption_after_commit_is_checked_again_immediately_before_send(local):
    clock, received = Clock(), []
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2200)
        clock.advance(125000)
        assert sender(runtime, clock, received).flush() == {"DELIVERED": 1}
        assert received[0][1] == "DELAYED"


def test_clock_rollback_after_commit_is_not_current(local):
    clock, received = Clock(), []
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2200)
        clock.advance(125000, wall_ms=0)
        assert sender(runtime, clock, received).flush() == {"DELIVERED": 1}
        assert received[0][1] == "CLOCK_UNCERTAIN"


def test_host_gap_breaks_timing_even_when_media_gap_is_small(local):
    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2000)
        clock.advance(1000)
        runtime.process(observation(2000, mode="LIVE"), acquired_ns=clock.ns)
        assert runtime.generated == 0
        assert runtime.engine.start == 2000


def test_commit_then_error_is_unknown_to_caller_and_payload_survives_restart(local):
    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2000)
        original = runtime.store.checkpoint

        def committed_then_failed(*args, **kwargs):
            original(*args, **kwargs)
            raise sqlite3.OperationalError("injected failure after successful commit")

        runtime.store.checkpoint = committed_then_failed
        with pytest.raises(EdgeError, match="persistir"):
            feed(runtime, clock, 2000, 2200)
        row = runtime.store.db.execute("SELECT * FROM outbox").fetchone()
        payload, event_id = row["payload"], row["event_id"]
        assert (
            runtime.store.db.execute(
                "SELECT checkpoint_outcome FROM timing_audit WHERE stage='CHECKPOINT'"
            ).fetchone()[0]
            == "UNKNOWN"
        )
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as resumed:
        assert resumed.engine.state == "ACTIVE"
        assert resumed.store.db.execute("SELECT payload FROM outbox").fetchone()[0] == payload
        timing = resumed.store.delivery_timing(event_id)
        state, reason, _ = delivery_freshness(
            json.loads(payload), timing, clock.time(), clock.ns, "new-process"
        )
        assert state == "CLOCK_UNCERTAIN" and "RESTART" in reason


def test_retry_keeps_bytes_and_original_ack_class_after_lost_ack(local):
    clock, sent = Clock(), []
    incident_id = str(uuid4())
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2200)

        def transport(request):
            sent.append((request.content, request.headers.get("x-radar-delivery-state")))
            if len(sent) == 1:
                raise httpx.ReadError("injected lost ACK", request=request)
            return httpx.Response(
                200,
                json={
                    "eventId": json.loads(request.content)["eventId"],
                    "incidentId": incident_id,
                    "receivedAt": datetime.fromtimestamp(clock.time(), UTC)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                    "duplicate": True,
                    "deliveryClass": "CURRENT",
                },
            )

        dispatch = Delivery(
            runtime.store,
            DeliveryConfig(enabled=True),
            client=httpx.Client(transport=httpx.MockTransport(transport)),
            clock=clock.time,
            freshness_clock=clock.time,
            jitter=lambda *_: 1,
            monotonic_clock=clock.monotonic_ns,
            clock_session=clock.session_id,
        )
        assert dispatch.flush() == {"PENDING": 1}
        clock.advance(125000)
        assert dispatch.flush() == {"DELIVERED": 1}
        assert sent[0][0] == sent[1][0] and sent[1][1] == "DELAYED"
        row = runtime.store.db.execute("SELECT ack FROM outbox").fetchone()
        assert json.loads(row[0])["deliveryClass"] == "CURRENT"


def test_additive_v2_migration_preserves_original_outbox(local):
    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2200)
        original = runtime.store.db.execute("SELECT payload FROM outbox").fetchone()[0]
        runtime.store.db.executescript(
            "DROP TABLE timing_audit; DROP TABLE delivery_timing; PRAGMA user_version=2;"
        )
    with Outbox(local.events.outboxPath, CAMERA) as store:
        assert store.db.execute("PRAGMA user_version").fetchone()[0] == 3
        assert store.db.execute("SELECT payload FROM outbox").fetchone()[0] == original
        assert store.db.execute("SELECT COUNT(*) FROM timing_audit").fetchone()[0] == 0


def test_continuity_break_does_not_remove_the_gap_from_coverage_denominator(local):
    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2000)
        clock.advance(1000)
        runtime.process(observation(2800, mode="LIVE"), acquired_ns=clock.ns)
        assert runtime.summary()["observedMediaMs"] == 2800
        assert runtime.summary()["eligibleMediaMs"] <= 1800


def test_retry_schedule_clock_does_not_age_a_fresh_event(local):
    clock, received = Clock(), []
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2200)
        dispatch = sender(runtime, clock, received)
        dispatch.clock = lambda: clock.time() + 10000
        assert dispatch.flush() == {"DELIVERED": 1}
        assert received[0][1] is None


def test_uncertain_delivery_hint_is_durable_and_does_not_upgrade_on_retry(local):
    clock = Clock()
    with EventRuntime(local, calibration(), "hash", GEOMETRY, clock=clock) as runtime:
        begin(runtime, clock)
        feed(runtime, clock, 0, 2200)
        event_id = runtime.store.db.execute("SELECT event_id FROM outbox").fetchone()[0]
        clock.advance(125000, wall_ms=0)

        def lost(request):
            raise httpx.ReadTimeout("lost", request=request)

        dispatch = Delivery(
            runtime.store,
            DeliveryConfig(enabled=True),
            client=httpx.Client(transport=httpx.MockTransport(lost)),
            clock=clock.time,
            freshness_clock=clock.time,
            monotonic_clock=clock.monotonic_ns,
            clock_session=clock.session_id,
        )
        assert dispatch.flush() == {"PENDING": 1}
        saved = runtime.store.delivery_timing(event_id)
        assert saved["deliveryHint"] == "CLOCK_UNCERTAIN"
        assert (
            runtime.store.db.execute(
                "SELECT reason FROM timing_audit WHERE stage='DELIVERY_PREFLIGHT'"
            ).fetchone()[0]
            == "WALL_MONOTONIC_DIVERGENCE"
        )
        clock.wall += 125
        state, _, _ = delivery_freshness(
            runtime.store.events(runtime.run["run_id"])[0],
            saved,
            clock.time(),
            clock.ns,
            clock.session_id,
        )
        assert state == "CLOCK_UNCERTAIN"
