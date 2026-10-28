"""Explicit opt-in short LIVE runner. Preparation/tests never open a camera."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "edge" / "src"))

from stream import experimental_factory  # noqa: E402


def validate(config):
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
    if Path(config.events.outboxPath).exists():
        raise ValueError("Use the newly prepared outbox; never resume another episode")


def execute(path):
    from radar_edge.config import load_config
    from radar_edge.live import run_live

    config = load_config(path)
    validate(config)
    sessions = []
    with experimental_factory("directml", sessions):
        report, code = run_live(config)
    report["experimentalExecutor"] = {
        "backend": "directml",
        "sessions": sessions,
        "scope": "EXPLICIT_SHORT_PHYSICAL_TEST_NOT_MVP_APPROVAL",
    }
    Path(report["reportPath"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"code": code, "reportPath": report["reportPath"]}))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    raise SystemExit(execute(parser.parse_args().config))
