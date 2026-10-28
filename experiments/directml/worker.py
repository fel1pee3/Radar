"""Explicit opt-in short LIVE runner. Every invocation has its own local session."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "edge" / "src"))

from stream import experimental_factory  # noqa: E402


def validate(config, *, require_new_outbox=True):
    if config.source.kind != "WEBCAM" or not config.source.authorized:
        raise ValueError("This prepared short test requires the authorized existing webcam")
    if (
        config.model.variant != "rtmo-s"
        or config.model.recovery != "RTMO_ADAPTIVE_V3"
        or config.model.runtimeProfile != "REFERENCE_4_SPIN"
    ):
        raise ValueError("Preserve the RTMO reference, recovery and session profile")
    if config.events.delivery.enabled or config.events.snapshotAuthorized:
        raise ValueError("Prepared cost test must keep HTTP and snapshots disabled")
    duration = config.processing.maxRunSeconds
    if duration is None or not 0 < duration <= 120:
        raise ValueError("The explicit physical test must be bounded to at most 120 seconds")
    if require_new_outbox and Path(config.events.outboxPath).exists():
        raise ValueError("Use the newly prepared outbox; never resume another episode")


def prepare_session(config, source_config):
    """Clone output paths; an existing session is never resumed, removed or overwritten."""
    import yaml
    from radar_edge.config import private_path

    validate(config, require_new_outbox=False)
    original_outbox = private_path(config.events.outboxPath)
    session_id = str(uuid4())
    directory = private_path(original_outbox.parent / "sessions" / session_id)
    current = config.model_copy(deep=True)
    current.events.outboxPath = str(directory / "outbox.sqlite")
    current.diagnostics.outputDirectory = str(directory / "results")
    validate(current)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "config.yaml").write_text(
        yaml.safe_dump(current.model_dump(), sort_keys=False), encoding="utf-8"
    )
    (directory / "session.json").write_text(
        json.dumps(
            {
                "sessionId": session_id,
                "sourceConfig": str(source_config),
                "sourceConfigSha256": hashlib.sha256(Path(source_config).read_bytes()).hexdigest(),
                "outboxPath": current.events.outboxPath,
                "resultsDirectory": current.diagnostics.outputDirectory,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return current, directory


def execute(path):
    from radar_edge.config import load_config
    from radar_edge.live import run_live

    config, directory = prepare_session(load_config(path), path)
    print(
        json.dumps(
            {
                "status": "starting",
                "sessionDirectory": str(directory),
                "message": "Nova sessao local; os testes anteriores permanecem preservados.",
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    sessions = []
    with experimental_factory("directml", sessions):
        report, code = run_live(config)
    report["experimentalExecutor"] = {
        "backend": "directml",
        "sessions": sessions,
        "sessionDirectory": str(directory),
        "sourceConfig": str(path),
        "scope": "EXPLICIT_SHORT_PHYSICAL_TEST_NOT_MVP_APPROVAL",
    }
    Path(report["reportPath"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"code": code, "reportPath": report["reportPath"]}))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    raise SystemExit(execute(parser.parse_args().config))
