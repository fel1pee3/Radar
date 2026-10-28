"""Sequential frozen FILE comparisons. No webcam, HTTP or changes to reference configs."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def execute(protocol_path):
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    root = Path(protocol["outputRoot"])
    micro = json.loads((root / "micro-comparison.json").read_text(encoding="utf-8"))
    if not micro["eligibleForStreamComparison"]:
        raise ValueError("The frozen small comparison did not authorize paced tests")
    for item in protocol["cases"]:
        for key, expected in item["preservedFiles"].items():
            if hashlib.sha256(Path(key).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Preserved input changed: {key}")
    for repetition, order in enumerate(protocol["orders"], start=1):
        cases = protocol["cases"] if repetition % 2 else list(reversed(protocol["cases"]))
        for backend in order:
            for item in cases:
                destination = root / f"stream-r{repetition}-{backend}-{item['id']}"
                if destination.exists():
                    raise ValueError(f"Refusing to overwrite {destination}")
                log_path = destination.with_suffix(".log")
                command = [
                    protocol["python"][backend],
                    "experiments/directml/stream.py",
                    "--config",
                    item["config"],
                    "--output",
                    str(destination),
                    "--backend",
                    backend,
                ]
                print(json.dumps({"starting": str(destination)}), flush=True)
                with log_path.open("w", encoding="utf-8") as log:
                    completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
                if completed.returncode:
                    raise RuntimeError(f"Stream failed; preserved log: {log_path}")
                summary = json.loads((destination / "summary.json").read_text(encoding="utf-8"))
                print(
                    json.dumps(
                        {
                            "completed": destination.name,
                            "complete": summary["complete"],
                            "decisions": summary["decisions"],
                            "coverage": summary["wallTimingAcceptance"]["decisionCoverage"],
                            "capture": summary["wallTimingAcceptance"]["captureCoverage"],
                            "calls": summary["modelCallsPerAnalysis"]["mean"],
                        }
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    execute(parser.parse_args().protocol)
