"""Explicit stopped-worker backup/restore; no HTTP, camera, media or credentials."""

import sqlite3
from contextlib import ExitStack, closing
from pathlib import Path

from radar_edge.config import private_path
from radar_edge.errors import EdgeError
from radar_edge.outbox import FileLock


def copy_outbox(source, destination):
    source, destination = private_path(source), private_path(destination)
    if not source.is_file() or destination.exists():
        raise EdgeError("BACKUP_PATH_INVALID", "Origem ausente ou destino já existente.")
    if source.is_symlink() or destination.parent.is_symlink():
        raise EdgeError("BACKUP_PATH_INVALID", "Links não são aceitos no backup.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as original:
        with closing(sqlite3.connect(destination)) as target:
            version = original.execute("PRAGMA user_version").fetchone()[0]
            if version not in {1, 2, 3}:
                raise EdgeError("OUTBOX_SCHEMA_UNSUPPORTED", "Confira a versão da outbox.")
            original.backup(target)
            target.execute("PRAGMA secure_delete=ON")
            if version >= 2:
                target.execute(
                    "UPDATE snapshots SET jpeg=NULL,status='EXPIRED',error_code='BACKUP_NO_MEDIA'"
                )
            target.commit()
            target.execute("VACUUM")
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise EdgeError("BACKUP_INTEGRITY_FAILED", "Falha na integridade SQLite.")
            if target.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise EdgeError("BACKUP_INTEGRITY_FAILED", "Falha nas relações SQLite.")
            target.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    return {
        "status": "ok",
        "path": str(destination.relative_to(Path.cwd())),
        "mediaIncluded": False,
        "httpDeliveryExecuted": False,
        "cameraOpened": False,
    }


def backup_outbox(config, output):
    with ExitStack() as locks:
        locks.enter_context(FileLock(private_path(f".local/edge-locks/{config.cameraId}.lock")))
        locks.enter_context(FileLock(private_path(config.events.outboxPath + ".lock")))
        return copy_outbox(config.events.outboxPath, output)
