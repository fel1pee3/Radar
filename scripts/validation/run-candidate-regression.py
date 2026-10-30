"""Sequential real FILE regression in the isolated DirectML environment. No camera/HTTP."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def execute(path, native_only=False):
    protocol = json.loads(path.read_text(encoding="utf-8-sig"))
    identities = [item["id"] for item in protocol["cases"]]
    if any(
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", identity)
        for identity in identities
    ):
        raise ValueError("Use simple case identities, never filesystem paths")
    if len(identities) != len(set(identities)):
        raise ValueError("Case identities must be unique")
    root = Path(protocol["outputRoot"])
    if not root.resolve().is_relative_to((Path.cwd() / ".local").resolve()):
        raise ValueError("Use uma pasta privada nova dentro de .local")
    if root.exists():
        raise ValueError("Use uma pasta nova; resultados anteriores preservados.")
    for item in protocol["cases"]:
        for filename, digest in item["preservedFiles"].items():
            if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != digest:
                raise ValueError("Entrada mudou: " + filename)
    root.mkdir(parents=True)
    for item in protocol["cases"]:
        log = root / (item["id"] + ".log")
        command = (
            [
                sys.executable,
                "scripts/validation/evaluate-native-case.py",
                "--protocol",
                str(path),
                "--case",
                item["id"],
            ]
            if native_only
            else [
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
        )
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
    ap.add_argument("--native-only", action="store_true")
    args = ap.parse_args()
    execute(args.protocol, args.native_only)
