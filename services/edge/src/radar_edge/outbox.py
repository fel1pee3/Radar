"""Durable episodes, immutable event payloads and replay checkpoints in SQLite."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
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
            if self.db.execute("PRAGMA user_version").fetchone()[0] not in {0, 1}:
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
                CREATE TABLE IF NOT EXISTS resets (
                    id TEXT PRIMARY KEY, camera_id TEXT NOT NULL, run_id TEXT,
                    reason TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)
            self.db.execute("PRAGMA user_version=1")
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

    def execution(self, fingerprint):
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
        run_id, anchor = str(uuid4()), utc_now()
        with self.transaction():
            self.db.execute(
                "INSERT INTO executions(run_id,camera_id,fingerprint,anchor,created_at) "
                "VALUES(?,?,?,?,?)",
                (run_id, self.camera_id, fingerprint, anchor, anchor),
            )
        return dict(
            self.db.execute("SELECT * FROM executions WHERE run_id=?", (run_id,)).fetchone()
        ), False

    def checkpoint(self, run_id, observation, engine, event=None, closed=False):
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
