"""Private FILE/WEBCAM configuration, relative to the repository working directory."""

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


class WebcamConfig(StrictModel):
    kind: Literal["WEBCAM"]
    index: int = Field(ge=0, le=15)
    backend: Literal["DSHOW", "MSMF"] = "DSHOW"
    authorized: bool = False
    width: int = Field(default=640, ge=160, le=1920)
    height: int = Field(default=480, ge=120, le=1080)
    fps: float = Field(default=30.0, gt=0, le=120)
    rotation: Literal[0, 90, 180, 270] = 0
    frameTimeoutSeconds: float = Field(default=2.0, ge=0.5, le=10)
    openTimeoutSeconds: float = Field(default=10.0, ge=1, le=30)
    reconnectAttempts: int = Field(default=3, ge=0, le=10)
    reconnectDelaySeconds: float = Field(default=1.0, ge=0.1, le=10)


class ModelConfig(StrictModel):
    variant: Literal["lite", "full", "rtmo-s"] = "lite"
    path: str = ".local/models/pose_landmarker_lite.task"
    recovery: Literal[
        "NONE",
        "RTMO_ADAPTIVE_V1",
        "RTMO_ADAPTIVE_V2",
        "RTMO_ADAPTIVE_V3",
        "RTMO_PREFERRED_V1",
        "RTMO_PREFERRED_V2",
    ] = "NONE"
    runtimeProfile: Literal["REFERENCE_4_SPIN", "CPU_2_SPIN", "CPU_4_SLEEP", "CPU_2_SLEEP"] = (
        "REFERENCE_4_SPIN"
    )

    @model_validator(mode="after")
    def full_path_is_explicit(self):
        if self.runtimeProfile != "REFERENCE_4_SPIN" and self.variant != "rtmo-s":
            raise ValueError("CPU runtime profiles require RTMO.")
        if self.recovery != "NONE" and self.variant != "rtmo-s":
            raise ValueError("Recuperacao adaptativa exige RTMO explicito.")
        if self.variant != "lite" and "path" not in self.model_fields_set:
            raise ValueError("Informe model.path explicitamente ao selecionar outro modelo.")
        return self


class ProcessingConfig(StrictModel):
    maxWidth: int = Field(default=640, ge=64, le=640)
    targetAnalysisFps: float = Field(default=5.0, gt=0, le=30)
    minLandmarkVisibility: float = Field(default=0.5, ge=0, le=1)
    minKeypointScore: float = Field(default=0.5, gt=0, le=1)
    replaySpeed: float = Field(default=0.0, ge=0, le=10)
    preview: bool = False
    previewStartPaused: bool = False
    previewStabilization: bool = False
    maxObservations: int | None = Field(default=None, ge=1, le=1000000)
    maxRunSeconds: float | None = Field(default=None, gt=0, le=86400)


class DiagnosticsConfig(StrictModel):
    profileProcessing: bool = False
    outputDirectory: str = ".local/results/edge"
    exportObservations: bool = False
    maxExportObservations: int = Field(default=1000, ge=1, le=10000)
    maxExportBytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)
    exportDecisions: bool = False
    maxDecisionRecords: int = Field(default=10000, ge=1, le=10000)
    maxDecisionBytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)
    maxDecisionDirectoryBytes: int = Field(default=50 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    decisionRetentionDays: int = Field(default=7, ge=1, le=7)


class DeliveryConfig(StrictModel):
    enabled: bool = False
    credentialFile: str | None = None
    timeoutSeconds: float = Field(default=5.0, gt=0, le=15)
    maxItems: int = Field(default=10000, ge=1, le=10000)
    maxBytes: int = Field(default=100 * 1024 * 1024, ge=65536, le=100 * 1024 * 1024)
    confirmedRetentionDays: int = Field(default=7, ge=1, le=90)


class EventsConfig(StrictModel):
    enabled: bool = False
    outboxPath: str = ".local/edge/outbox.sqlite"
    evidenceMode: Literal["none", "skeleton", "snapshot"] = "skeleton"
    snapshotAuthorized: bool = False
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


class SupportRegion(StrictModel):
    kind: Literal["CHAIR", "BED", "HAMMOCK", "AMBIGUOUS"]
    polygon: list[tuple[float, float]]

    @field_validator("polygon", mode="before")
    @classmethod
    def valid_polygon(cls, value):
        from radar_edge.calibration import validate_polygon

        return validate_polygon(value)


class PostureConfig(StrictModel):
    method: Literal["BASELINE", "LINEAR_CONTEXT_V1", "LINEAR_BODY_V2", "MULTICLASS_BODY_V3"] = (
        "BASELINE"
    )
    artifactPath: str | None = None
    artifactSha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    installationId: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    calibrationSha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    operatorConfirmed: bool = False
    excludedRegions: list[list[tuple[float, float]]] = Field(default_factory=list, max_length=16)
    supportRegions: list[SupportRegion] = Field(default_factory=list, max_length=16)

    @field_validator("excludedRegions", mode="before")
    @classmethod
    def valid_regions(cls, value):
        from radar_edge.calibration import validate_polygon

        return [validate_polygon(region) for region in value]

    @model_validator(mode="after")
    def explicit_context(self):
        if self.method != "BASELINE" and not (
            self.artifactPath
            and self.artifactSha256
            and self.installationId
            and self.calibrationSha256
            and self.operatorConfirmed
        ):
            raise ValueError("Classifier requires a pinned artifact and confirmed installation.")
        if self.method == "BASELINE" and self != PostureConfig.model_construct():
            raise ValueError("Context/exclusions require the explicit new classifier method.")
        return self


class EdgeConfig(StrictModel):
    schemaVersion: Literal[1] = 1
    purpose: Literal["RADAR_FILE_POSE", "RADAR_LIVE_POSE"] = "RADAR_FILE_POSE"
    cameraId: str
    source: SourceConfig | WebcamConfig = Field(discriminator="kind")
    model: ModelConfig = Field(default_factory=ModelConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    posture: PostureConfig = Field(default_factory=PostureConfig)
    calibrationPath: str = ".local/calibration.json"
    diagnostics: DiagnosticsConfig = Field(default_factory=DiagnosticsConfig)
    events: EventsConfig = Field(default_factory=EventsConfig)

    @field_validator("source", mode="before")
    @classmethod
    def preserve_file_default(cls, value):
        if isinstance(value, dict) and "kind" not in value:
            return {"kind": "FILE", **value}
        return value

    @field_validator("cameraId")
    @classmethod
    def uuid_camera(cls, value: str) -> str:
        UUID(value)
        return value

    @model_validator(mode="after")
    def live_model_is_explicit(self):
        if self.source.kind == "WEBCAM" and self.model.variant not in {"full", "rtmo-s"}:
            raise ValueError("A webcam exige Full ou seleção explícita do RTMO experimental.")
        if self.events.enabled:
            from radar_edge.policy import configured_policy

            expected = "RTMO_KEYPOINT_SCORE" if self.model.variant == "rtmo-s" else "MEDIAPIPE"
            if configured_policy(self.events.policy).qualitySource != expected:
                raise ValueError(
                    "O modelo exige política explícita com a mesma origem de qualidade."
                )
        return self


def quality_threshold(config: EdgeConfig) -> float:
    return (
        config.processing.minKeypointScore
        if config.model.variant == "rtmo-s"
        else config.processing.minLandmarkVisibility
    )


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
        if config.posture.artifactPath is not None:
            private_path(config.posture.artifactPath)
        if not config.source.authorized:
            raise EdgeError(
                "CAMERA_AUTHORIZATION_REQUIRED"
                if config.source.kind == "WEBCAM"
                else "VIDEO_AUTHORIZATION_REQUIRED",
                "Confirme source.authorized para a fonte local antes de abri-la.",
            )
        return config
    except EdgeError:
        raise
    except (OSError, ValueError, yaml.YAMLError, ValidationError):
        raise EdgeError(
            "INVALID_CONFIG", "Confira o arquivo privado e os campos do exemplo edge.example.yaml."
        ) from None
