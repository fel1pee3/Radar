"""Sequential CPU/DML functional regression, alternating backend order per FILE."""

import argparse
import json
import subprocess
from pathlib import Path


def execute(path):
    protocol = json.loads(path.read_text(encoding="utf-8"))
    root = Path(protocol["outputRoot"])
    for index, item in enumerate(protocol["cases"]):
        order = ["cpu-reference", "directml"] if index % 2 == 0 else ["directml", "cpu-reference"]
        for backend in order:
            log_path = root / f"functional-{backend}-{item['id']}.log"
            command = [
                protocol["python"][backend],
                "experiments/directml/functional.py",
                "--protocol",
                str(path),
                "--backend",
                backend,
                "--case",
                item["id"],
            ]
            with log_path.open("w", encoding="utf-8") as log:
                child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            if child.returncode:
                raise RuntimeError(f"Regression failed; inspect {log_path}")
            result = json.loads(
                (root / "functional" / backend / item["id"] / "evaluation.json").read_text(
                    encoding="utf-8"
                )
            )
            print(
                json.dumps(
                    {
                        "case": item["id"],
                        "backend": backend,
                        "approved": result["score"]["approved"],
                        "missed": result["score"]["missed"],
                        "negative": result["score"]["negativeResult"],
                        "events": result["score"]["eventKinds"],
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    execute(parser.parse_args().protocol)
