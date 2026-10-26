"""Explicit local training from pinned observations and preannotated private clips.

No automatic labeling, frame shuffling, model download or media export.
"""

import hashlib
import json
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from radar_edge.calibration import load_calibration
from radar_edge.config import StrictModel, load_config, private_path
from radar_edge.errors import EdgeError
from radar_edge.evaluation import Interval
from radar_edge.features import QualityGate, extract_features
from radar_edge.model import file_hash, get_model_spec
from radar_edge.observations import Landmark, Observation, Pose
from radar_edge.policy import configured_policy
from radar_edge.posture import BODY_DESCRIPTOR, DESCRIPTOR, LinearArtifact, body_descriptor


class TrainingClip(StrictModel):
    videoId: str
    configuration: str
    sourceSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: str
    observationsSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    partition: Literal["TRAIN", "SELECTION", "FINAL_RESERVED"]
    participantId: str
    sessionId: str | None
    environmentId: str
    permission: Literal["CC-BY-4.0", "OWNER_RECORDED_AUTHORIZED"]
    permissionEvidence: str = Field(min_length=10, max_length=2000)
    annotationsConfirmed: Literal[True]
    floorIntervals: list[Interval] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def ordered_annotations(self):
        ordered = sorted(self.floorIntervals, key=lambda interval: interval.startMs)
        if any(a.endMs > b.startMs for a, b in zip(ordered, ordered[1:], strict=False)):
            raise ValueError("Overlapping floor annotations")
        return self


class TrainingManifest(StrictModel):
    schemaVersion: Literal[1]
    trainingAuthorized: Literal[True]
    version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    installationId: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    sessionIndependenceEstablished: bool
    splitStrategy: Literal["PARTICIPANT", "SESSION"] = "PARTICIPANT"
    l2: float = Field(default=0.01, gt=0, le=10)
    descriptor: Literal["symmetric-body-context-35-v1", "symmetric-body-shape-29-v1"] = DESCRIPTOR
    clips: list[TrainingClip] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def split_without_leakage(self):
        if len({c.sourceSha256 for c in self.clips}) != len(self.clips):
            raise ValueError("Duplicate video bytes")
        if len({c.videoId for c in self.clips}) != len(self.clips):
            raise ValueError("Duplicate video identifiers")
        participants, sessions = {}, {}
        for clip in self.clips:
            participants.setdefault(clip.participantId, set()).add(clip.partition)
            if clip.sessionId is not None:
                sessions.setdefault(clip.sessionId, set()).add(clip.partition)
        groups = [*sessions.values()]
        if self.splitStrategy == "PARTICIPANT":
            groups.extend(participants.values())
        elif not self.sessionIndependenceEstablished or any(
            c.sessionId is None for c in self.clips
        ):
            raise ValueError("Session split requires known distinct recording sessions")
        if any(len(partitions) > 1 for partitions in groups):
            raise ValueError("Participant/session leakage between partitions")
        if len({c.environmentId for c in self.clips}) != 1:
            raise ValueError("This initial model is specific to one fixed camera/room")
        if self.sessionIndependenceEstablished and any(c.sessionId is None for c in self.clips):
            raise ValueError("Unknown sessions cannot establish session independence")
        return self


def read_observations(filename):
    path = private_path(filename)
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Observation input exceeds 64 MiB")
    previous = -1
    with path.open(encoding="utf-8-sig") as stream:
        for index, line in enumerate(stream):
            if index >= 100000 or len(line) > 65536:
                raise ValueError("Observation input limit")
            raw = json.loads(line)
            raw["poses"] = tuple(
                Pose(tuple(Landmark(**p) for p in pose["landmarks"]), pose["qualitySource"])
                for pose in raw["poses"]
            )
            raw["qualityReasons"] = tuple(raw["qualityReasons"])
            o = Observation(**raw)
            if o.timestampMs <= previous:
                raise ValueError("Non-monotonic observations")
            previous = o.timestampMs
            yield o


def fit_linear(vectors, labels, video_ids, l2):
    x, y = np.asarray(vectors), np.asarray(labels, dtype=float)
    if len(y) < 20 or set(y) != {0.0, 1.0} or not np.isfinite(x).all():
        raise ValueError("Need at least 20 valid observations and both labeled classes")
    mean, std = x.mean(axis=0), np.maximum(x.std(axis=0), 0.05)
    matrix = np.column_stack(((x - mean) / std, np.ones(len(x))))
    weights = np.zeros(len(y))
    for category in [0, 1]:
        groups = {group for group, label in zip(video_ids, y, strict=True) if label == category}
        for group in sorted(groups):
            selected = np.array([g == group for g in video_ids]) & (y == category)
            weights[selected] = 0.5 / len(groups) / selected.sum()
    coefficients = np.zeros(matrix.shape[1])
    for _ in range(3000):
        probabilities = 1 / (1 + np.exp(-np.clip(matrix @ coefficients, -40, 40)))
        penalty = l2 * coefficients
        penalty[-1] = 0
        coefficients -= 0.05 * (matrix.T @ ((probabilities - y) * weights) + penalty)
    return mean.tolist(), std.tolist(), coefficients.tolist()


def train_posture(filename, output):
    try:
        path = private_path(filename)
        if path.stat().st_size > 1024 * 1024:
            raise ValueError()
        if json.loads(path.read_bytes()).get("schemaVersion") == 2:
            from radar_edge.posture_multiclass_training import train_multiclass

            return train_multiclass(filename, output)
        manifest = TrainingManifest.model_validate_json(path.read_bytes())
        destination = private_path(output)
        if destination.exists():
            raise EdgeError(
                "POSTURE_OUTPUT_EXISTS", "Use um novo destino; preserve o modelo anterior."
            )
        vectors, labels, video_ids = [], [], []
        for clip in manifest.clips:
            # Reserved/selection observations are not opened or fitted.
            if clip.partition != "TRAIN":
                continue
            config = load_config(clip.configuration)
            if config.source.kind != "FILE" or config.model.variant != "rtmo-s":
                raise ValueError()
            if file_hash(Path(config.source.path)) != clip.sourceSha256:
                raise ValueError()
            obs_path = private_path(clip.observations)
            if file_hash(obs_path) != clip.observationsSha256:
                raise ValueError()
            calibration = load_calibration(config.calibrationPath)
            policy = configured_policy(config.events.policy)
            gate = QualityGate(policy)
            for o in read_observations(obs_path):
                if (o.cameraId, o.calibrationId, o.calibrationVersion, o.modelId) != (
                    config.cameraId,
                    calibration["calibrationId"],
                    calibration["version"],
                    get_model_spec("rtmo-s").model_id,
                ):
                    raise ValueError()
                if (o.width, o.height, o.rotation) != tuple(
                    calibration["geometry"][key] for key in ("width", "height", "rotation")
                ):
                    raise ValueError("Observation geometry differs from confirmed installation")
                f = gate.apply(o, extract_features(o, calibration["floorPolygon"], policy))
                label = 0
                for target in clip.floorIntervals:
                    if target.startMs + 500 <= o.timestampMs < target.endMs - 500:
                        label = 1
                        break
                    if target.startMs - 1000 <= o.timestampMs <= target.endMs:
                        label = None
                        break
                if f.eligible and label is not None:
                    vector = body_descriptor(o, manifest.descriptor)
                    if vector is not None:
                        if len(labels) >= 20000:
                            raise ValueError("Training exceeds 20000 eligible observations")
                        vectors.append(vector)
                        labels.append(label)
                        video_ids.append(clip.videoId)
        mean, std, coefficients = fit_linear(vectors, labels, video_ids, manifest.l2)
        protocol = manifest.model_dump()
        if manifest.splitStrategy == "PARTICIPANT":
            # Preserve the first frozen artifact; absent field means PARTICIPANT.
            protocol.pop("splitStrategy")
        if manifest.descriptor == DESCRIPTOR:
            protocol.pop("descriptor")
        artifact = LinearArtifact(
            schemaVersion=1,
            descriptor=manifest.descriptor,
            version=manifest.version,
            poseModelSha256=get_model_spec("rtmo-s").sha256,
            installationIds=[manifest.installationId],
            mean=mean,
            std=std,
            coefficients=coefficients,
            contextMode="OPERATOR_CONFIRMED_FIXED_CAMERA"
            if manifest.descriptor == BODY_DESCRIPTOR
            else "TRAINED_INSTALLATION",
            training={
                "manifestSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "observations": len(labels),
                "positiveObservations": sum(labels),
                "protocol": protocol,
                "algorithm": "numpy-logistic; 3000 steps; lr=0.05; class/video-balanced",
                "annotationGuardMs": 500,
                "preOnsetGuardMs": 1000,
                "independentAccuracyClaim": False,
            },
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        serialized = (
            artifact.model_dump_json(
                indent=2, exclude={"contextMode"} if manifest.descriptor == DESCRIPTOR else None
            )
            + "\n"
        )
        if len(serialized.encode()) > 256 * 1024:
            raise ValueError("Model artifact exceeds runtime size limit")
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
        return {
            "status": "ok",
            "command": "posture-train",
            "artifactPath": str(destination),
            "sha256": file_hash(destination),
            "trainingObservations": len(labels),
            "cameraOpened": False,
            "approved": False,
        }
    except EdgeError:
        raise
    except (OSError, ValueError, TypeError, KeyError):
        raise EdgeError(
            "POSTURE_TRAINING_INVALID",
            "Confira manifesto, permissões, divisões, hashes e observações; "
            "nenhum segredo exibido.",
        ) from None
