"""FILE-only opt-in session factory over the existing paced transmission executor."""

import argparse
import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter, process_time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "edge" / "src"))

from runtime import BACKENDS, create_session, process_memory  # noqa: E402


@contextmanager
def experimental_factory(backend, sessions):
    import radar_edge.rtmo as rtmo

    original = rtmo.RtmoEstimator

    class ExperimentalEstimator(original):
        def __enter__(self):
            if self.runtime_profile != "REFERENCE_4_SPIN" or self.recovery != "RTMO_ADAPTIVE_V3":
                raise ValueError("The isolated executor requires the unchanged reference")
            self.session, info = create_session(self.model_path, backend)
            self.executor_metadata = {
                **info,
                "requested": backend,
                "runtime": "onnxruntime-directml" if backend != "cpu-reference" else "onnxruntime",
                "version": info.get("ortVersion"),
                "providers": info.get("actualProviders", []),
                "adapter": info.get("adapter"),
            }
            sessions.append(info)
            return self

    rtmo.RtmoEstimator = ExperimentalEstimator
    try:
        yield
    finally:
        rtmo.RtmoEstimator = original


def measure(config_path, output, backend):
    from radar_edge.config import load_config

    config = load_config(config_path)
    if config.source.kind != "FILE" or not config.source.authorized:
        raise ValueError("Only an authorized FILE is allowed; no camera can be opened")
    if config.model.variant != "rtmo-s":
        raise ValueError("This experiment only accepts the preserved RTMO weights")
    if os.environ.get("EVIDENCE_MODE", "skeleton") != "skeleton":
        raise ValueError("Snapshots are forbidden in this experiment")
    spec = importlib.util.spec_from_file_location(
        "radar_paced_stream", ROOT / "scripts" / "validation" / "benchmark-stream.py"
    )
    executor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(executor)
    sessions = []
    cpu_started, wall_started = process_time(), perf_counter()
    memory_before = process_memory()
    with experimental_factory(backend, sessions):
        result = executor.measure(
            config_path, output, "REFERENCE_4_SPIN", False, "RTMO_ADAPTIVE_V3"
        )
    cpu_seconds, wall_seconds = process_time() - cpu_started, perf_counter() - wall_started
    result["experimentalExecutor"] = {
        "backend": backend,
        "sessions": sessions,
        "processCpuSeconds": cpu_seconds,
        "processWallSeconds": wall_seconds,
        "machineNormalizedCpuPercent": 100 * cpu_seconds / wall_seconds / (os.cpu_count() or 1),
        "memoryBefore": memory_before,
        "memoryAfter": process_memory(),
        "limitations": (
            "Process CPU includes initialization, warmup, decode, logging and hashing; "
            "memory excludes complete GPU/driver use. No power, clocks or temperature measured."
        ),
        "unchangedPrePostRecoveryClassifierTemporalLogic": True,
        "outputsReady": (
            "Synchronous session.run returns CPU numpy outputs; "
            "original RTMO decode consumes them before decision."
        ),
    }
    (Path(output) / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "backend": backend,
                "output": str(output),
                "complete": result["complete"],
                "decisions": result["decisions"],
                "processing": result["stages"].get("processingMs"),
                "calls": result["modelCallsPerAnalysis"],
                "timing": result["wallTimingAcceptance"],
            }
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=BACKENDS, required=True)
    args = parser.parse_args()
    raise SystemExit(measure(args.config, args.output, args.backend)["code"])
