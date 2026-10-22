"""Pinned official model; download is explicit and never part of run/doctor."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal
from uuid import uuid4

import httpx

from radar_edge.config import private_path
from radar_edge.errors import EdgeError

MODEL_CARD = (
    "https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf"
)
MAX_MODEL_BYTES = 20 * 1024 * 1024
ModelVariant = Literal["lite", "full"]


@dataclass(frozen=True)
class ModelSpec:
    variant: ModelVariant
    model_id: str
    url: str
    sha256: str
    default_path: str


MODEL_SPECS = MappingProxyType(
    {
        "lite": ModelSpec(
            variant="lite",
            model_id="pose-landmarker-lite-float16-v1",
            url=(
                "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
            ),
            sha256="59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a",
            default_path=".local/models/pose_landmarker_lite.task",
        ),
        "full": ModelSpec(
            variant="full",
            model_id="pose-landmarker-full-float16-v1",
            url=(
                "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                "pose_landmarker_full/float16/1/pose_landmarker_full.task"
            ),
            sha256="5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1",
            default_path=".local/models/pose_landmarker_full.task",
        ),
    }
)
# Existing callers and configurations continue to select Lite by default.
MODEL_ID = MODEL_SPECS["lite"].model_id
MODEL_URL = MODEL_SPECS["lite"].url
MODEL_SHA256 = MODEL_SPECS["lite"].sha256


def get_model_spec(variant: ModelVariant = "lite") -> ModelSpec:
    try:
        return MODEL_SPECS[variant]
    except (KeyError, TypeError):
        raise EdgeError("INVALID_MODEL_VARIANT", "Selecione o modelo lite ou full.") from None


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_model(filename: str | Path, variant: ModelVariant = "lite") -> Path:
    spec = get_model_spec(variant)
    path = private_path(filename)
    if not path.is_file():
        raise EdgeError(
            "MODEL_MISSING", f"Obtenha o bundle com radar-edge model-fetch --variant {variant}."
        )
    if file_hash(path) != spec.sha256:
        raise EdgeError(
            "MODEL_HASH_MISMATCH",
            "O modelo difere do bundle fixado para a variante selecionada. Confira o SHA-256.",
        )
    return path


def fetch_model(filename: str | Path | None = None, variant: ModelVariant = "lite") -> dict:
    spec = get_model_spec(variant)
    path = private_path(spec.default_path if filename is None else filename)
    if path.exists():
        verify_model(path, variant)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{uuid4()}.part")
        try:
            with httpx.stream("GET", spec.url, timeout=40, follow_redirects=False) as response:
                response.raise_for_status()
                size = 0
                with temporary.open("xb") as stream:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_MODEL_BYTES:
                            raise EdgeError(
                                "MODEL_TOO_LARGE", "Download do modelo excedeu o limite."
                            )
                        stream.write(chunk)
            verify_model(temporary, variant)
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
        "modelId": spec.model_id,
        "sha256": spec.sha256,
        "bytes": path.stat().st_size,
    }
