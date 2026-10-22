"""Bounded diagnostics retention; never touches sources, models or calibrations."""

from datetime import UTC, datetime
from uuid import UUID

from radar_edge.config import private_path


def cleanup_diagnostics(directory, now=None, max_bytes=20 * 1024 * 1024):
    root = private_path(directory)
    now = now or datetime.now(UTC)
    files = []
    if not root.exists():
        return {"removed": 0, "bytes": 0}
    for folder in root.iterdir():
        if folder.is_symlink() or not folder.is_dir():
            continue
        try:
            UUID(folder.name)
        except ValueError:
            continue
        for name in ("report.json", "observations.jsonl"):
            path = folder / name
            if path.is_file() and not path.is_symlink():
                files.append(path)
    files.sort(key=lambda p: p.stat().st_mtime)
    size = sum(p.stat().st_size for p in files)
    removed = 0
    for path in files:
        stat = path.stat()
        if now.timestamp() - stat.st_mtime >= 7 * 86400 or size > max_bytes:
            path.unlink()
            size -= stat.st_size
            removed += 1
    return {"removed": removed, "bytes": size}
