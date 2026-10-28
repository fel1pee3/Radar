"""Sequential CPU/DML functional regression, alternating backend order per FILE."""

import argparse
import json
import subprocess
from pathlib import Path


def execute(path, *, native_worker=False):
    protocol = json.loads(path.read_text(encoding="utf-8-sig"))
    root = Path(protocol["outputRoot"])
    if (root / "functional").exists() or any(root.glob("functional-*.log")):
        raise ValueError("Use nova pasta de regressão; resultados anteriores preservados.")
    root.mkdir(parents=True, exist_ok=True)
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
            if native_worker:
                command.append("--native-worker")
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
    parser.add_argument("--native-worker", action="store_true")
    args = parser.parse_args()
    execute(args.protocol, native_worker=args.native_worker)
