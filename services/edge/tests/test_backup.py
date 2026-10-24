import sqlite3
from uuid import uuid4

import pytest
from temporal_support import CAMERA, config, observation

from radar_edge.backup import backup_outbox, copy_outbox
from radar_edge.engine import TemporalEngine
from radar_edge.errors import EdgeError
from radar_edge.outbox import FileLock, Outbox


def test_backup_restore_preserves_pending_episode_and_excludes_media(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = config()
    with Outbox(c.events.outboxPath, CAMERA) as store:
        run, _ = store.execution("fingerprint")
        engine = TemporalEngine()
        # Actual persisted event and checkpoint, using deterministic synthetic observations.
        from temporal_support import POLYGON

        from radar_edge.features import extract_features

        event = None
        for t in range(0, 2200, 200):
            o = observation(t)
            decision = engine.step(extract_features(o, POLYGON))
            if decision:
                event = {
                    "eventId": str(uuid4()),
                    "episodeId": str(uuid4()),
                    "evidenceMode": "snapshot",
                    "kind": decision.kind,
                }
            store.checkpoint(
                run["run_id"],
                o,
                engine,
                event=event if decision else None,
                snapshot=b"SYNTHETIC-JPEG-PRIVATE" if decision else None,
            )
        assert event is not None
    result = backup_outbox(c, ".local/copy.sqlite")
    assert not result["mediaIncluded"] and not result["httpDeliveryExecuted"]
    copy_outbox(".local/copy.sqlite", ".local/restored.sqlite")
    with Outbox(".local/restored.sqlite", CAMERA) as restored:
        assert restored.summary() == {"PENDING": 1}
        assert restored.events(run["run_id"]) == [event]
        assert restored.db.execute("SELECT state FROM episodes").fetchone()[0] == "ACTIVE"
        assert restored.db.execute("SELECT jpeg FROM snapshots").fetchone()[0] is None
        restored_run, resumed = restored.execution("fingerprint")
        assert resumed and restored_run["engine"] == store_engine_snapshot(engine)
    assert b"SYNTHETIC-JPEG-PRIVATE" not in (tmp_path / ".local/copy.sqlite").read_bytes()
    with sqlite3.connect(c.events.outboxPath) as original:
        assert (
            original.execute("SELECT jpeg FROM snapshots").fetchone()[0]
            == b"SYNTHETIC-JPEG-PRIVATE"
        )


def store_engine_snapshot(engine):
    from radar_edge.outbox import encode

    return encode(engine.snapshot())


def test_backup_refuses_live_lock_and_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = config()
    with Outbox(c.events.outboxPath, CAMERA):
        pass
    with FileLock(tmp_path / f".local/edge-locks/{CAMERA}.lock"):
        with pytest.raises(EdgeError, match="Outra execução"):
            backup_outbox(c, ".local/refused.sqlite")
    backup_outbox(c, ".local/copied.sqlite")
    with pytest.raises(EdgeError):
        backup_outbox(c, ".local/copied.sqlite")
