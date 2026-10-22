"""Private FILE-only configuration. Paths are relative to the repository working directory."""

from pathlib import Path
from typing import Literal
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from radar_edge.errors import EdgeError


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class SourceConfig(StrictModel):
    kind: Literal["FILE"] = "FILE"
    path: str
    videoId: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")
    authorized: bool = False
    rotation: Literal["AUTO", 0, 90, 180, 270] = "AUTO"
    allowTimestampFallback: bool = True

    @field_validator("path")
    @classmethod
    def local_path(cls, value: str) -> str:
        if not value.strip() or "://" in value or value.startswith(("\\\\", "//")):
            raise ValueError("Only explicitly configured local files are supported")
        return value

    @field_validator("rotation", mode="before")
    @classmethod
    def rotation_not_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("Rotation cannot be boolean")
        return value


class ModelConfig(StrictModel):
    variant: Literal["lite", "full"] = "lite"
    path: str = ".local/models/pose_landmarker_lite.task"

    @model_validator(mode="after")
    def full_path_is_explicit(self):
        if self.variant == "full" and "path" not in self.model_fields_set:
            raise ValueError("Informe model.path explicitamente ao selecionar o modelo full.")
        return self


class ProcessingConfig(StrictModel):
    maxWidth: int = Field(default=640, ge=64, le=640)
    targetAnalysisFps: float = Field(default=5.0, gt=0, le=30)
    minLandmarkVisibility: float = Field(default=0.5, ge=0, le=1)
    replaySpeed: float = Field(default=0.0, ge=0, le=10)
    preview: bool = False
    previewStartPaused: bool = False
    maxObservations: int | None = Field(default=None, ge=1, le=1000000)


class DiagnosticsConfig(StrictModel):
    outputDirectory: str = ".local/results/edge"
    exportObservations: bool = False
    maxExportObservations: int = Field(default=1000, ge=1, le=10000)
    maxExportBytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)


class DeliveryConfig(StrictModel):
    enabled: bool = False
    credentialFile: str | None = None
    timeoutSeconds: float = Field(default=2.0, gt=0, le=15)


class EventsConfig(StrictModel):
    enabled: bool = False
    outboxPath: str = ".local/edge/outbox.sqlite"
    evidenceMode: Literal["none", "skeleton"] = "skeleton"
    policy: dict = Field(default_factory=dict)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)

    @field_validator("policy")
    @classmethod
    def valid_policy(cls, value):
        from radar_edge.policy import configured_policy

        try:
            configured_policy(value)
        except (ValueError, TypeError):
            raise ValueError(
                "Confira os parâmetros; alterá-los exige outra policy version."
            ) from None
        return value


class EdgeConfig(StrictModel):
    schemaVersion: Literal[1] = 1
    purpose: Literal["RADAR_FILE_POSE"] = "RADAR_FILE_POSE"
    cameraId: str
    source: SourceConfig
    model: ModelConfig = Field(default_factory=ModelConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    calibrationPath: str = ".local/calibration.json"
    diagnostics: DiagnosticsConfig = Field(default_factory=DiagnosticsConfig)
    events: EventsConfig = Field(default_factory=EventsConfig)

    @field_validator("cameraId")
    @classmethod
    def uuid_camera(cls, value: str) -> str:
        UUID(value)
        return value


def private_path(value: str | Path) -> Path:
    path = Path(value).resolve()
    if path == Path(".local").resolve() or not path.is_relative_to(Path(".local").resolve()):
        raise EdgeError("PRIVATE_PATH_REQUIRED", "Use um arquivo ou subdiretório dentro de .local.")
    return path


def load_config(filename: str | Path) -> EdgeConfig:
    try:
        path = private_path(filename)
        if path.stat().st_size > 65536:
            raise EdgeError("INVALID_CONFIG", "A configuração excede 64 KiB.")
        config = EdgeConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8-sig")))
        for value in (
            config.model.path,
            config.calibrationPath,
            config.diagnostics.outputDirectory,
            config.events.outboxPath,
        ):
            private_path(value)
        if config.events.delivery.credentialFile is not None:
            private_path(config.events.delivery.credentialFile)
        if not config.source.authorized:
            raise EdgeError(
                "VIDEO_AUTHORIZATION_REQUIRED",
                "Autorize o vídeo local em source.authorized antes de abri-lo.",
            )
        return config
    except EdgeError:
        raise
    except (OSError, ValueError, yaml.YAMLError, ValidationError):
        raise EdgeError(
            "INVALID_CONFIG", "Confira o arquivo privado e os campos do exemplo edge.example.yaml."
        ) from None
