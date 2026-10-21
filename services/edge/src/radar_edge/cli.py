"""Diagnóstico de imports reais sem abrir câmera, rede ou modelo."""

import argparse
import json
import platform
import sys
from importlib.metadata import distributions, version


def inspect_environment() -> dict[str, object]:
    providers = sorted(
        package.metadata["Name"]
        for package in distributions()
        if package.metadata["Name"].lower().startswith("opencv-")
    )
    if providers != ["opencv-contrib-python"]:
        raise RuntimeError(
            "Instale somente opencv-contrib-python; há fornecedores cv2 incompatíveis."
        )

    import cv2
    import mediapipe
    from mediapipe.tasks.python import vision

    if not hasattr(vision, "PoseLandmarker"):
        raise RuntimeError("MediaPipe Tasks PoseLandmarker indisponível nesta instalação.")
    build = cv2.getBuildInformation()
    backends = [
        line.strip()
        for line in build.splitlines()
        if any(key in line for key in ("GUI:", "FFMPEG:", "Media Foundation:", "DirectShow:"))
    ]
    return {
        "status": "ok",
        "command": "env",
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "packages": {
            name: version(name)
            for name in ("mediapipe", "opencv-contrib-python", "pydantic", "httpx")
        },
        "mediapipe_import": mediapipe.__version__,
        "opencv_import": cv2.__version__,
        "opencv_providers": providers,
        "opencv_build": backends,
        "pose_landmarker_import": "ok",
        "model_loaded": False,
        "camera_opened": False,
        "inference_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Radar Edge — diagnóstico do ambiente local.")
    parser.add_argument("command", choices=["env"], help="Importa bibliotecas e informa versões.")
    parser.parse_args()
    try:
        result = inspect_environment()
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": type(error).__name__,
                    "message": (
                        "Falha no ambiente de visão. Execute uv sync --project services/edge "
                        "--frozen e verifique os wheels/DLLs para Python 3.12 e seu sistema."
                    ),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False, indent=2))
