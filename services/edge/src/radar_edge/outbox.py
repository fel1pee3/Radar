"""Durable episodes, immutable event payloads and replay checkpoints in SQLite."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from radar_edge.config import private_path
from radar_edge.errors import EdgeError


def utc_now():
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class FileLock:
    def __init__(self, path):
        self.path, self.file = path, None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+b")
        self.file.seek(0, 2)
        if self.file.tell() == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            self.file = None
            raise EdgeError(
                "WORKER_LOCKED", "Outra execução usa esta câmera ou outbox; encerre-a primeiro."
            ) from None
        return self

    def __exit__(self, *_):
        if self.file is not None:
            self.file.close()  # OS releases the lock, also after process crash.


class Outbox:
    def __init__(self, path, camera_id):
        self.path = private_path(path)
        self.camera_id = camera_id
        self.db = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(self.path, timeout=2)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA secure_delete=ON")
            if self.db.execute("PRAGMA user_version").fetchone()[0] not in {0, 1, 2, 3}:
                raise EdgeError(
                    "OUTBOX_SCHEMA_UNSUPPORTED",
                    "Versão SQLite não suportada; preserve a outbox e confira a versão do worker.",
                )
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS executions (
                    run_id TEXT PRIMARY KEY, camera_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, anchor TEXT NOT NULL,
                    frame_index INTEGER NOT NULL DEFAULT -1,
                    timestamp_ms INTEGER NOT NULL DEFAULT -1,
                    engine TEXT NOT NULL DEFAULT '{}', completed INTEGER NOT NULL DEFAULT 0,
                    retired INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_execution ON executions(camera_id)
                    WHERE retired=0;
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES executions(run_id),
                    event_id TEXT NOT NULL UNIQUE, state TEXT NOT NULL, closed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    event_id TEXT PRIMARY KEY REFERENCES episodes(event_id), payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt REAL NOT NULL DEFAULT 0, error_code TEXT, ack TEXT,
                    created_at TEXT NOT NULL, delivered_at TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_episode ON episodes(run_id)
                    WHERE state='ACTIVE';
                CREATE TRIGGER IF NOT EXISTS immutable_payload BEFORE UPDATE OF payload ON outbox
                    BEGIN SELECT RAISE(ABORT, 'immutable payload'); END;
                CREATE TABLE IF NOT EXISTS snapshots (
                    event_id TEXT PRIMARY KEY REFERENCES episodes(event_id),
                    jpeg BLOB, hash TEXT, created_at TEXT NOT NULL, expires_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt REAL NOT NULL DEFAULT 0, error_code TEXT
                );
                CREATE TABLE IF NOT EXISTS delivery_timing (
                    event_id TEXT PRIMARY KEY REFERENCES outbox(event_id) ON DELETE CASCADE,
                    timing TEXT NOT NULL, delivery_hint TEXT
                );
                CREATE TABLE IF NOT EXISTS timing_audit (
                    id INTEGER PRIMARY KEY, run_id TEXT, event_id TEXT,
                    frame_index INTEGER NOT NULL, stage TEXT NOT NULL,
                    reason TEXT NOT NULL, age_ms REAL, checkpoint_outcome TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(event_id, frame_index, stage, reason)
                );
                CREATE TABLE IF NOT EXISTS resets (
                    id TEXT PRIMARY KEY, camera_id TEXT NOT NULL, run_id TEXT,
                    reason TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)
            self.db.execute("PRAGMA user_version=3")
            self.db.commit()
            cameras = {r[0] for r in self.db.execute("SELECT DISTINCT camera_id FROM executions")}
            if cameras and cameras != {self.camera_id}:
                raise EdgeError(
                    "OUTBOX_CAMERA_CONFLICT", "Use uma outbox dedicada à câmera configurada."
                )
        except Exception:
            if self.db is not None:
                self.db.close()
            raise
        return self

    def __exit__(self, *_):
        self.db.close()

    @contextmanager
    def transaction(self):
        try:
            self.db.execute("BEGIN IMMEDIATE")
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def check_capacity(self, max_items=10000, max_bytes=100 * 1024 * 1024, extra_bytes=0):
        count = self.db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
        size = sum(
            p.stat().st_size
            for p in [
                self.path,
                self.path.with_name(self.path.name + "-wal"),
                self.path.with_name(self.path.name + "-shm"),
            ]
            if p.exists()
        )
        if count >= max_items or size + extra_bytes >= max_bytes:
            raise EdgeError(
                "STORAGE_FULL",
                "Outbox no limite; novas inferências interrompidas. Pendentes preservados.",
            )
        return {"items": count, "bytes": size, "maxItems": max_items, "maxBytes": max_bytes}

    def prune_confirmed(self, retention_days=7, now=None):
        # The active episode restores from executions.engine, never the confirmed payload.
        now = now or datetime.now(UTC)
        cutoff = (
            (now - timedelta(days=retention_days))
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        current = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with self.transaction():
            self.db.execute(
                "UPDATE snapshots SET "
                "jpeg=NULL,status='EXPIRED',error_code='SNAPSHOT_EXPIRED' WHERE jpeg IS NOT "
                "NULL AND expires_at<=?",
                (current,),
            )
            self.db.execute(
                "DELETE FROM outbox WHERE status='DELIVERED' AND delivered_at<=?", (cutoff,)
            )
        # secure_delete + checkpoint also removes confirmed/expired data from WAL when possible.
        self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def snapshot_summary(self):
        return [
            dict(r)
            for r in self.db.execute(
                "SELECT event_id,status,attempts,error_code,LENGTH(jpeg) AS bytes FROM "
                "snapshots ORDER BY rowid DESC LIMIT 100"
            )
        ]

    def execution(self, fingerprint, *, anchor=None):
        row = self.db.execute(
            "SELECT * FROM executions WHERE camera_id=? AND retired=0", (self.camera_id,)
        ).fetchone()
        if row is not None:
            if row["fingerprint"] != fingerprint:
                raise EdgeError(
                    "SOURCE_CONFIG_CONFLICT",
                    "Fonte, calibração ou política mudou. Pare o worker e use reset-episode "
                    "com motivo; o histórico será preservado.",
                )
            return dict(row), True
        run_id, created = str(uuid4()), utc_now()
        anchor = anchor or created
        with self.transaction():
            self.db.execute(
                "INSERT INTO executions(run_id,camera_id,fingerprint,anchor,created_at) "
                "VALUES(?,?,?,?,?)",
                (run_id, self.camera_id, fingerprint, anchor, created),
            )
        return dict(
            self.db.execute("SELECT * FROM executions WHERE run_id=?", (run_id,)).fetchone()
        ), False

    def checkpoint(
        self,
        run_id,
        observation,
        engine,
        event=None,
        closed=False,
        snapshot=None,
        snapshot_error=None,
        timing=None,
    ):
        # Episode creation + event + checkpoint must commit together before any HTTP.
        with self.transaction():
            if event:
                self.db.execute(
                    "INSERT INTO episodes VALUES(?,?,?,?,NULL)",
                    (event["episodeId"], run_id, event["eventId"], "ACTIVE"),
                )
                self.db.execute(
                    "INSERT INTO outbox(event_id,payload,created_at) VALUES(?,?,?)",
                    (event["eventId"], encode(event), utc_now()),
                )
                if timing is not None:
                    self.db.execute(
                        "INSERT INTO delivery_timing(event_id,timing) VALUES(?,?)",
                        (event["eventId"], encode(timing)),
                    )
                if event.get("evidenceMode") == "snapshot":
                    count, size = self.db.execute(
                        "SELECT COUNT(jpeg),COALESCE(SUM(LENGTH(jpeg)),0) FROM snapshots"
                    ).fetchone()
                    if count >= 100 or size + len(snapshot or b"") > 20 * 1024 * 1024:
                        snapshot, snapshot_error = None, "SNAPSHOT_STORAGE_FULL"
                    import hashlib

                    created = datetime.now(UTC)
                    self.db.execute(
                        "INSERT INTO "
                        "snapshots(event_id,jpeg,hash,created_at,expires_at,status,error_code) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (
                            event["eventId"],
                            snapshot,
                            hashlib.sha256(snapshot).hexdigest() if snapshot else None,
                            created.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                            (created + timedelta(days=1))
                            .isoformat(timespec="milliseconds")
                            .replace("+00:00", "Z"),
                            "PENDING" if snapshot else "PERMANENT_ERROR",
                            snapshot_error,
                        ),
                    )
            if closed:
                self.db.execute(
                    "UPDATE episodes SET state='CLOSED',closed_at=? "
                    "WHERE run_id=? AND state='ACTIVE'",
                    (utc_now(), run_id),
                )
            self.db.execute(
                "UPDATE executions SET frame_index=?,timestamp_ms=?,engine=? WHERE run_id=?",
                (
                    observation.frameIndex,
                    observation.timestampMs,
                    encode(engine.snapshot()),
                    run_id,
                ),
            )

    def delivery_timing(self, event_id):
        row = self.db.execute(
            "SELECT timing,delivery_hint FROM delivery_timing WHERE event_id=?", (event_id,)
        ).fetchone()
        return (
            {"timing": json.loads(row["timing"]), "deliveryHint": row["delivery_hint"]}
            if row
            else None
        )

    def audit_timing(
        self,
        run_id,
        frame_index,
        stage,
        reason,
        age_ms=None,
        event_id=None,
        outcome=None,
        engine=None,
        delivery_hint=None,
    ):
        with self.transaction():
            if engine is not None:
                self.db.execute(
                    "UPDATE executions SET engine=? WHERE run_id=?",
                    (encode(engine.snapshot()), run_id),
                )
            self.db.execute(
                "INSERT OR IGNORE INTO timing_audit "
                "(run_id,event_id,frame_index,stage,reason,age_ms,checkpoint_outcome,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (run_id, event_id, frame_index, stage, reason, age_ms, outcome, utc_now()),
            )
            if event_id and stage == "DELIVERY_PREFLIGHT" and delivery_hint is not None:
                self.db.execute(
                    "UPDATE delivery_timing SET delivery_hint=? WHERE event_id=?",
                    (delivery_hint, event_id),
                )

    def finish(self, run_id):
        with self.transaction():
            self.db.execute("UPDATE executions SET completed=1 WHERE run_id=?", (run_id,))

    def reset(self, reason):
        with self.transaction():
            row = self.db.execute(
                "SELECT run_id FROM executions WHERE camera_id=? AND retired=0", (self.camera_id,)
            ).fetchone()
            run_id = row[0] if row else None
            self.db.execute(
                "INSERT INTO resets VALUES(?,?,?,?,?)",
                (str(uuid4()), self.camera_id, run_id, reason, utc_now()),
            )
            if run_id:
                self.db.execute(
                    "UPDATE episodes SET state='RESET',closed_at=? "
                    "WHERE run_id=? AND state='ACTIVE'",
                    (utc_now(), run_id),
                )
                self.db.execute("UPDATE executions SET retired=1 WHERE run_id=?", (run_id,))

    def summary(self):
        return {
            r[0]: r[1]
            for r in self.db.execute("SELECT status,COUNT(*) FROM outbox GROUP BY status")
        }

    def delivery_errors(self):
        return {
            r[0]: r[1]
            for r in self.db.execute(
                "SELECT error_code,COUNT(*) FROM outbox WHERE error_code IS NOT NULL "
                "AND status!='DELIVERED' GROUP BY error_code"
            )
        }

    def items(self):
        return [
            {
                "eventId": r["event_id"],
                "status": r["status"],
                "attempts": r["attempts"],
                "errorCode": r["error_code"],
                "nextAttemptEpochSeconds": r["next_attempt"],
                "confirmation": json.loads(r["ack"]) if r["ack"] else None,
            }
            for r in self.db.execute("SELECT * FROM outbox ORDER BY rowid DESC LIMIT 100")
        ]

    def events(self, run_id):
        return [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT payload FROM outbox JOIN episodes USING(event_id) "
                "WHERE run_id=? ORDER BY outbox.rowid LIMIT 1001",
                (run_id,),
            )
        ]

    def update_delivery(self, event_id, status, attempts, next_attempt, error=None, ack=None):
        with self.transaction():
            self.db.execute(
                "UPDATE outbox SET status=?,attempts=?,next_attempt=?,error_code=?,ack=?,"
                "delivered_at=? WHERE event_id=?",
                (
                    status,
                    attempts,
                    next_attempt,
                    error,
                    encode(ack) if ack else None,
                    utc_now() if status == "DELIVERED" else None,
                    event_id,
                ),
            )
