"""Sequential paired FILE streams in the active isolated runtime. Never a camera."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def execute(candidate_root, reference_root, output):
    output.mkdir(parents=True, exist_ok=False)
    cases = (
        "floor03",
        "floor05",
        "floor07",
        "controlled-lying",
        "cauca-03",
        "cauca-04",
        "cauca-10",
        "chair08-01",
        "intake16-03",
        "intake16-15",
    )
    plan = []
    for repeat in (1, 2):
        for index, case in enumerate(cases):
            order = (
                ("reference", "candidate")
                if (repeat + index) % 2
                else ("candidate", "reference")
            )
            for variant in order:
                config = (
                    reference_root / "functional/directml" / case / "config.yaml"
                    if variant == "reference"
                    else candidate_root / "configs" / (case + ".yaml")
                )
                # Historical functional configs were written before the experimental
                # runtime factory override. Never infer executor from their folder name.
                settings = yaml.safe_load(config.read_text(encoding="utf-8"))
                settings["model"]["executor"] = "DIRECTML"
                config_dir = output / "effective-inputs"
                config_dir.mkdir(exist_ok=True)
                effective = config_dir / f"{case}-{variant}.yaml"
                if not effective.exists():
                    effective.write_text(
                        yaml.safe_dump(settings, sort_keys=False), encoding="utf-8"
                    )
                config = effective
                target = output / f"{case}-{repeat}-{variant}"
                plan.append(
                    {
                        "case": case,
                        "repeat": repeat,
                        "variant": variant,
                        "config": str(config),
                        "output": str(target),
                    }
                )
    (output / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(Path("services/edge/src").resolve()))
    for item in plan:
        with (output / (Path(item["output"]).name + ".log")).open(
            "x", encoding="utf-8"
        ) as log:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validation/benchmark-stream.py",
                    "--config",
                    item["config"],
                    "--output",
                    item["output"],
                ],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if result.returncode:
            raise RuntimeError("Falha: " + item["output"])
        summary = json.loads(
            (Path(item["output"]) / "summary.json").read_text(encoding="utf-8")
        )
        report = json.loads(Path(summary["reportPath"]).read_text(encoding="utf-8"))
        execution = report["model"]["executor"]
        if not (
            execution.get("initialized")
            and execution.get("requested") == "DIRECTML"
            and "DmlExecutionProvider" in execution.get("providers", [])
        ):
            raise RuntimeError(
                "Executor divergiu; comparacao invalida: " + item["output"]
            )
        print(json.dumps(item), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate-root", type=Path, required=True)
    ap.add_argument("--reference-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    execute(args.candidate_root, args.reference_root, args.output)
