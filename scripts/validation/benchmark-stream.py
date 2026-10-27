"""Real inference on a 1x FILE stream through LIVE scheduling; never a webcam."""

import argparse
import hashlib
import json
import os
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np
import yaml
from radar_edge.config import load_config, private_path
from radar_edge.live import run_live
from radar_edge.stream_acceptance import assess_stream_timing

PROFILES = ("REFERENCE_4_SPIN", "CPU_2_SPIN", "CPU_4_SLEEP", "CPU_2_SLEEP")


def statistics(values):
    values = [v for v in values if v is not None]
    return {
        "samples": len(values),
        "mean": float(np.mean(values)) if values else None,
        "p95": float(np.percentile(values, 95)) if values else None,
        "max": max(values) if values else None,
    }


def measure(
    config_path, output, profile="REFERENCE_4_SPIN", preview=False, recovery=None
):
    config = load_config(config_path)
    output = private_path(output)
    if (
        config.source.kind != "FILE"
        or os.environ.get("EVIDENCE_MODE", "skeleton") != "skeleton"
    ):
        raise ValueError("Use FILE autorizado, sem snapshot e EVIDENCE_MODE=skeleton")
    output.mkdir(parents=True, exist_ok=False)
    original_hash = hashlib.sha256(Path(config.source.path).read_bytes()).hexdigest()
    config.events.delivery.enabled = False
    config.events.delivery.credentialFile = None
    config.events.snapshotAuthorized = False
    config.events.evidenceMode = "skeleton"
    config.events.outboxPath = str(output / "outbox.sqlite")
    config.diagnostics.outputDirectory = str(output / "results")
    config.diagnostics.exportDecisions = True
    config.diagnostics.profileProcessing = True
    config.model.runtimeProfile = profile
    if recovery is not None:
        config.model.recovery = recovery
    if config.model.recovery in {"RTMO_PREFERRED_V1", "RTMO_PREFERRED_V2"}:
        suffix = "-preferred-" + config.model.recovery.rsplit("_", 1)[1].lower()
        if not config.events.policy["version"].endswith(suffix):
            config.events.policy["version"] += suffix
    config.processing.preview = preview
    config.processing.previewStartPaused = False
    config.processing.replaySpeed = 1
    config.processing.maxRunSeconds = None
    config.processing.maxObservations = None
    (output / "config.yaml").write_text(
        yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8"
    )
    report, code = run_live(config, technical_stream=True)
    trace_path = report["decisionExport"].get("path")
    records = (
        [json.loads(x) for x in Path(trace_path).read_text().splitlines()]
        if trace_path
        else []
    )
    decisions = [r for r in records if r["recordType"] == "DECISION"]
    processing = [r for r in records if r["recordType"] == "PROCESSING_PROFILE"]
    assert report["mode"] == "REPLAY"
    assert report["executionKind"] == "TECHNICAL_PACED_FILE_NOT_WEBCAM"
    assert (
        hashlib.sha256(Path(config.source.path).read_bytes()).hexdigest()
        == original_hash
    )
    stages, passes = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for row in processing:
        for key, value in row.items():
            if (
                key.endswith("Ms")
                and key != "timestampMs"
                and isinstance(value, (int, float))
            ):
                stages[key].append(value)
        for key, value in row.get("eventRuntimeStages", {}).items():
            stages["runtime." + key].append(value)
        for attempt in row["attempts"]:
            for key in (
                "inferenceMs",
                "prepareMs",
                "sessionRunMs",
                "decodeMs",
                "restoreMs",
            ):
                if key in attempt:
                    passes[attempt["pass"]][key].append(attempt[key])
    timestamps = [r["timestampMs"] for r in decisions]
    # Frame identity is asserted from diagnostics, never inferred from FPS.
    indices = [r["frameIndex"] for r in decisions]
    assert len(indices) == len(set(indices))
    assert all(r["mode"] == "REPLAY" for r in decisions)
    gaps = [b - a for a, b in pairwise(timestamps)]
    host = [r["monotonicStartNs"] for r in processing]
    host_gaps = [(b - a) / 1e6 for a, b in pairwise(host)]
    ages = [r.get("timing", {}) for r in decisions]
    result = {
        "executionKind": report["executionKind"],
        "cameraOpened": False,
        "httpEnabled": False,
        "code": code,
        "error": report.get("error"),
        "configPath": str(output / "config.yaml"),
        "videoSha256": original_hash,
        "runtimeProfile": profile,
        "recovery": config.model.recovery,
        "perceptionStrategy": report.get("perceptionStrategy"),
        "modelCallsPerAnalysis": statistics(
            [
                sum(
                    not attempt.get("skippedReason")
                    for attempt in r["perception"]["attempts"]
                )
                for r in decisions
            ]
        ),
        "previewEnabled": preview,
        "warmupSyntheticExcludedMs": report["warmupSyntheticExcludedMs"],
        "reportPath": report["reportPath"],
        "complete": code == 0
        and report["source"].get("fullPlaybackCompleted", False)
        and not report["decisionExport"].get("truncated"),
        "decisions": len(decisions),
        "effectiveSamplesPerSecond": (len(timestamps) - 1)
        * 1000
        / (timestamps[-1] - timestamps[0])
        if len(timestamps) > 1
        else None,
        "sourceGapsMs": {**statistics(gaps), "above500": sum(g > 500 for g in gaps)},
        "monotonicGapsMs": {
            **statistics(host_gaps),
            "above500": sum(g > 500 for g in host_gaps),
        },
        "frameAgesMs": {
            key: statistics([r.get(key) for r in ages])
            for key in (
                "frameAgeAtAnalysisStartMs",
                "frameAgeAfterInferenceMs",
                "capturedFrameAgeAtDecisionMs",
            )
        },
        "stages": {k: statistics(v) for k, v in stages.items()},
        "passes": {
            p: {k: {**statistics(v), "total": sum(v)} for k, v in fields.items()}
            for p, fields in passes.items()
        },
        "source": report["source"],
        "metrics": report["metrics"],
        "temporal": report["temporal"],
        "profileWrite": report["processingProfile"],
        "wallTimingAcceptance": assess_stream_timing(
            records,
            report["source"]["durationMsEstimate"],
            report["source"]["hostMonotonicOriginNs"],
        ),
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--runtime-profile", choices=PROFILES, default=PROFILES[0])
    parser.add_argument("--preview", action="store_true")
    parser.add_argument(
        "--recovery",
        choices=("RTMO_ADAPTIVE_V3", "RTMO_PREFERRED_V1", "RTMO_PREFERRED_V2"),
    )
    args = parser.parse_args()
    result = measure(
        args.config, args.output, args.runtime_profile, args.preview, args.recovery
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "runtimeProfile",
                    "recovery",
                    "code",
                    "error",
                    "complete",
                    "decisions",
                    "effectiveSamplesPerSecond",
                    "sourceGapsMs",
                    "reportPath",
                )
            }
        )
    )
    raise SystemExit(result["code"])
