"""Sequential real FILE regression in the isolated DirectML environment. No camera/HTTP."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def execute(path):
    protocol = json.loads(path.read_text(encoding="utf-8-sig"))
    root = Path(protocol["outputRoot"])
    if root.exists():
        raise ValueError("Use uma pasta nova; resultados anteriores preservados.")
    root.mkdir(parents=True)
    for item in protocol["cases"]:
        for filename, digest in item["preservedFiles"].items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != digest:
                raise ValueError("Entrada mudou: " + filename)
    for item in protocol["cases"]:
        log = root / (item["id"] + ".log")
        command = [
            sys.executable,
            "experiments/directml/functional.py",
            "--protocol",
            str(path),
            "--backend",
            "directml",
            "--case",
            item["id"],
            "--native-worker",
        ]
        with log.open("x", encoding="utf-8") as stream:
            result = subprocess.run(
                command, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        if result.returncode:
            raise RuntimeError("Falha; consulte " + str(log))
        result = json.loads(
            (root / "functional/directml" / item["id"] / "evaluation.json").read_text()
        )
        print(json.dumps({"id": item["id"], "score": result["score"]}), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protocol", required=True, type=Path)
    execute(ap.parse_args().protocol)
