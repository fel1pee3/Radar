"""Pinned official model; download is explicit and never part of run/doctor."""

import hashlib
import shutil
import zipfile
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
ModelVariant = Literal["lite", "full", "rtmo-s"]


@dataclass(frozen=True)
class ModelSpec:
    variant: ModelVariant
    model_id: str
    url: str
    sha256: str
    default_path: str
    backend: str = "MEDIAPIPE"
    archive_sha256: str | None = None
    max_bytes: int = MAX_MODEL_BYTES


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
        "rtmo-s": ModelSpec(
            variant="rtmo-s",
            model_id="rtmo-s-body7-640x640-20231211-onnx-v1",
            url=(
                "https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
                "rtmo-s_8xb32-600e_body7-640x640-dac2bf74_20231211.zip"
            ),
            sha256="d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8",
            default_path=".local/models/rtmo_s_body7_640.onnx",
            backend="ONNX_RUNTIME",
            archive_sha256="3da7ad88b209f9da8be87ba5c325610639af04de3b5c8a96649b98cd9e2848a2",
            max_bytes=64 * 1024 * 1024,
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
        raise EdgeError(
            "INVALID_MODEL_VARIANT", "Selecione lite, full ou rtmo-s experimental."
        ) from None


def model_metadata(spec: ModelSpec) -> dict:
    return {
        "id": spec.model_id,
        "sha256": spec.sha256,
        "backend": spec.backend,
        "delegate": "CPU",
        "runningMode": "FRAME" if spec.backend == "ONNX_RUNTIME" else "VIDEO",
        "numPoses": None if spec.backend == "ONNX_RUNTIME" else 2,
        "segmentationMasks": False,
        "experimental": spec.backend == "ONNX_RUNTIME",
        "qualitySource": "RTMO_KEYPOINT_SCORE" if spec.backend == "ONNX_RUNTIME" else "MEDIAPIPE",
    }


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
        extracted = temporary.with_suffix(".onnx.part")
        try:
            with httpx.stream("GET", spec.url, timeout=40, follow_redirects=False) as response:
                response.raise_for_status()
                size = 0
                with temporary.open("xb") as stream:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > spec.max_bytes:
                            raise EdgeError(
                                "MODEL_TOO_LARGE", "Download do modelo excedeu o limite."
                            )
                        stream.write(chunk)
            candidate = temporary
            if spec.archive_sha256 is not None:
                if file_hash(temporary) != spec.archive_sha256:
                    raise EdgeError("MODEL_HASH_MISMATCH", "O ZIP oficial difere do hash fixado.")
                with zipfile.ZipFile(temporary) as archive:
                    entries = [i for i in archive.infolist() if i.filename.endswith(".onnx")]
                    if len(entries) != 1 or not 0 < entries[0].file_size <= spec.max_bytes:
                        raise EdgeError("MODEL_ARCHIVE_INVALID", "Conteúdo ONNX inesperado no ZIP.")
                    # Never extract filenames supplied by the archive onto the filesystem.
                    with archive.open(entries[0]) as source, extracted.open("xb") as target:
                        shutil.copyfileobj(source, target)
                candidate = extracted
            verify_model(candidate, variant)
            # Refuse to overwrite a model another process created during the download.
            with candidate.open("rb") as source, path.open("xb") as target:
                target.write(source.read())
        except EdgeError:
            raise
        except (OSError, httpx.HTTPError, zipfile.BadZipFile):
            raise EdgeError(
                "MODEL_DOWNLOAD_FAILED", "Falha ao obter o bundle oficial via HTTPS."
            ) from None
        finally:
            temporary.unlink(missing_ok=True)
            extracted.unlink(missing_ok=True)
    return {
        "status": "ok",
        "modelId": spec.model_id,
        "sha256": spec.sha256,
        "bytes": path.stat().st_size,
    }
