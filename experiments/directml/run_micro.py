"""Reproduce the frozen small gate in a NEW private directory, sequentially."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def execute(protocol_path, output, reference_python):
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=False)
    (output / "micro-protocol.frozen.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )
    python = {
        "cpu-reference": str(reference_python),
        "cpu-matched": sys.executable,
        "directml": sys.executable,
    }
    for repetition, order in enumerate(protocol["order"], start=1):
        for backend in order:
            destination = output / f"micro-r{repetition}-{backend}"
            command = [
                python[backend],
                "experiments/directml/probe.py",
                "--protocol",
                str(protocol_path),
                "--backend",
                backend,
                "--output",
                str(destination),
                "--repetition",
                str(repetition),
            ]
            with destination.with_suffix(".log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f"Failed; inspect {destination}.log")
            print(json.dumps({"completed": destination.name}), flush=True)
    destination = output / "profile-only"
    command = [
        sys.executable,
        "experiments/directml/probe.py",
        "--protocol",
        str(protocol_path),
        "--backend",
        "directml",
        "--output",
        str(destination),
        "--profile",
    ]
    with destination.with_suffix(".log").open("w", encoding="utf-8") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Profiling failed; inspect {destination}.log")
    profile = json.loads((destination / "result.json").read_text(encoding="utf-8"))["profile"]
    (output / "placement-proof.json").write_text(
        json.dumps({"profilePath": profile["path"]}, indent=2), encoding="utf-8"
    )
    from analyze import analyze

    return analyze(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--reference-python",
        type=Path,
        default=Path(".local/pose-env-965d2e5d/.venv/Scripts/python.exe"),
    )
    args = parser.parse_args()
    execute(args.protocol, args.output, args.reference_python)
