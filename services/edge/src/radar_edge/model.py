"""Pinned official model; download is explicit and never part of run/doctor."""

import hashlib
from pathlib import Path
from uuid import uuid4

import httpx

from radar_edge.config import private_path
from radar_edge.errors import EdgeError

MODEL_ID = "pose-landmarker-lite-float16-v1"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
MODEL_SHA256 = "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a"
MODEL_CARD = (
    "https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf"
)


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_model(filename: str | Path) -> Path:
    path = private_path(filename)
    if not path.is_file():
        raise EdgeError("MODEL_MISSING", "Obtenha o bundle com radar-edge model-fetch.")
    if file_hash(path) != MODEL_SHA256:
        raise EdgeError(
            "MODEL_HASH_MISMATCH", "O modelo difere do bundle fixado. Confira o SHA-256."
        )
    return path


def fetch_model(filename: str = ".local/models/pose_landmarker_lite.task") -> dict:
    path = private_path(filename)
    if path.exists():
        verify_model(path)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{uuid4()}.part")
        try:
            with httpx.stream("GET", MODEL_URL, timeout=40, follow_redirects=False) as response:
                response.raise_for_status()
                size = 0
                with temporary.open("xb") as stream:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 20 * 1024 * 1024:
                            raise EdgeError(
                                "MODEL_TOO_LARGE", "Download do modelo excedeu o limite."
                            )
                        stream.write(chunk)
            verify_model(temporary)
            # Refuse to overwrite a model another process created during the download.
            with temporary.open("rb") as source, path.open("xb") as target:
                target.write(source.read())
        except EdgeError:
            raise
        except (OSError, httpx.HTTPError):
            raise EdgeError(
                "MODEL_DOWNLOAD_FAILED", "Falha ao obter o bundle oficial via HTTPS."
            ) from None
        finally:
            temporary.unlink(missing_ok=True)
    return {
        "status": "ok",
        "modelId": MODEL_ID,
        "sha256": MODEL_SHA256,
        "bytes": path.stat().st_size,
    }
