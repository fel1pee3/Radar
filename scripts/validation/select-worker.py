"""Select a frozen worker environment by validated configuration; never opens a source."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/edge/src"))
from radar_edge.config import load_config


def arguments(config_path, runtime="PYTHON312"):
    config = load_config(config_path)
    project = (
        "experiments/directml"
        if config.model.executor == "DIRECTML"
        else "services/edge"
    )
    if runtime == "PYTHON313_SIGNED":
        project = (
            "experiments/python313-directml"
            if config.model.executor == "DIRECTML"
            else "experiments/python313-cpu"
        )
    elif runtime != "PYTHON312":
        raise ValueError("Runtime explicito desconhecido")
    return {
        "pythonRuntime": runtime,
        "cameraId": config.cameraId,
        "executor": config.model.executor,
        "project": project,
        "sourceOpened": False,
        "arguments": [
            "run",
            "--project",
            project,
            "--frozen",
            "--no-python-downloads",
            "python",
            "scripts/run-edge.py",
            "run",
            "--config",
            str(config_path),
            "--preview",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--runtime", choices=("PYTHON312", "PYTHON313_SIGNED"), default="PYTHON312")
    args = parser.parse_args()
    print(json.dumps(arguments(args.config, args.runtime)))
