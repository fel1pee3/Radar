"""Explicit grouped local training; no automatic labels, downloads or fitting on run."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from radar_edge.calibration import load_calibration
from radar_edge.config import StrictModel, load_config, private_path
from radar_edge.errors import EdgeError
from radar_edge.evaluation import Interval
from radar_edge.model import file_hash, get_model_spec
from radar_edge.observations import Landmark, Pose
from radar_edge.posture_multiclass import (
    CLASSES,
    DESCRIPTOR,
    FEATURE_DIM,
    MulticlassArtifact,
    signed_descriptor,
)


class ClassInterval(Interval):
    posture: Literal["STANDING_OR_WALKING", "SEATED", "KNEELING_OR_CROUCHING", "LYING", "UNKNOWN"]


class MulticlassClip(StrictModel):
    videoId: str
    configuration: str
    sourceSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: str
    observationsSha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    format: Literal["OBSERVATIONS", "DECISION_TRACE_ESSENTIAL"]
    partition: Literal["TRAIN", "SELECTION", "FINAL_RESERVED"]
    groupId: str = Field(min_length=1, max_length=120)
    participantId: str
    sessionId: str | None
    environmentId: str
    permission: Literal["CC-BY-4.0", "OWNER_RECORDED_AUTHORIZED"]
    permissionEvidence: str = Field(min_length=10, max_length=2000)
    annotationsConfirmed: Literal[True]
    classIntervals: list[ClassInterval] = Field(max_length=1000)

    @model_validator(mode="after")
    def no_overlap(self):
        intervals = sorted(self.classIntervals, key=lambda i: i.startMs)
        if any(a.endMs > b.startMs for a, b in zip(intervals, intervals[1:], strict=False)):
            raise ValueError("Overlapping posture labels")
        return self


class MulticlassTrainingManifest(StrictModel):
    schemaVersion: Literal[2]
    trainingAuthorized: Literal[True]
    version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    descriptor: Literal["signed-body-quality-84-v1"] = DESCRIPTOR
    seed: int = Field(default=1729, ge=0, le=2**32 - 1)
    steps: int = Field(default=1800, ge=100, le=5000)
    learningRate: float = Field(default=0.01, gt=0, le=0.1)
    l2: float = Field(default=0.001, gt=0, le=1)
    splitProtocol: Literal["RECORDING_GROUPS_POSSIBLE_SHARED_PARTICIPANTS"]
    clips: list[MulticlassClip] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def separate_recordings(self):
        groups, sessions = {}, {}
        if len({c.sourceSha256 for c in self.clips}) != len(self.clips) or len(
            {c.videoId for c in self.clips}
        ) != len(self.clips):
            raise ValueError("Duplicate material")
        for c in self.clips:
            groups.setdefault(c.groupId, set()).add(c.partition)
            if c.sessionId is not None:
                sessions.setdefault(c.sessionId, set()).add(c.partition)
        if any(len(values) > 1 for values in [*groups.values(), *sessions.values()]):
            raise ValueError("Recording group/session leakage")
        return self


def labeled_poses(clip):
    path = private_path(clip.observations)
    if path.stat().st_size > 64 * 1024 * 1024 or file_hash(path) != clip.observationsSha256:
        raise ValueError("Observation integrity/size mismatch")
    previous = -1
    with path.open(encoding="utf-8-sig") as stream:
        for index, line in enumerate(stream):
            if index >= 100000 or len(line) > 65536:
                raise ValueError("Observation limits")
            record = json.loads(line)
            if clip.format == "DECISION_TRACE_ESSENTIAL":
                if record.get("recordType") != "DECISION":
                    continue
            timestamp = record["timestampMs"]
            if timestamp <= previous:
                raise ValueError("Nonmonotonic training input")
            previous = timestamp
            if clip.format == "DECISION_TRACE_ESSENTIAL":
                if record["inferenceState"] in {"NO_POSE", "MULTIPLE_POSES"}:
                    continue
                points = [
                    Landmark(p["index"], p["x"], p["y"], None, None, None, p["score"])
                    for p in record["quality"]["essential"]
                    if p["present"]
                ]
                pose = Pose(tuple(points), record["quality"]["source"])
            else:
                if len(record["poses"]) != 1:
                    continue
                p = record["poses"][0]
                pose = Pose(
                    tuple(Landmark(**point) for point in p["landmarks"]), p["qualitySource"]
                )
            intervals = [i for i in clip.classIntervals if i.startMs <= timestamp < i.endMs]
            if intervals and intervals[0].posture in CLASSES:
                yield timestamp, pose, CLASSES.index(intervals[0].posture)


def fit_mlp(vectors, labels, groups, seed=1729, steps=1800, learning_rate=0.01, l2=0.001):
    x, y = np.asarray(vectors, dtype=float), np.asarray(labels, dtype=int)
    if (
        x.ndim != 2
        or x.shape[1] != FEATURE_DIM
        or len(y) < 40
        or set(y) != set(range(len(CLASSES)))
        or not np.isfinite(x).all()
    ):
        raise ValueError("Need all four classes and valid features")
    mean, std = x.mean(axis=0), np.maximum(x.std(axis=0), 0.05)
    x = (x - mean) / std
    weights = np.zeros(len(y))
    for label in range(len(CLASSES)):
        class_groups = sorted({g for g, k in zip(groups, y, strict=True) if k == label})
        for group in class_groups:
            mask = np.array([g == group for g in groups]) & (y == label)
            weights[mask] = 1 / len(CLASSES) / len(class_groups) / mask.sum()
    rng = np.random.default_rng(seed)
    parameters = [
        rng.normal(0, 0.1, (FEATURE_DIM, 32)),
        np.zeros(32),
        rng.normal(0, 0.1, (32, len(CLASSES))),
        np.zeros(len(CLASSES)),
    ]
    moments = [np.zeros_like(p) for p in parameters]
    squares = [np.zeros_like(p) for p in parameters]
    targets = np.eye(len(CLASSES))[y]
    for step in range(1, steps + 1):
        w1, b1, w2, b2 = parameters
        hidden = np.tanh(x @ w1 + b1)
        logits = hidden @ w2 + b2
        exp = np.exp(logits - logits.max(axis=1, keepdims=True))
        scores = exp / exp.sum(axis=1, keepdims=True)
        error = (scores - targets) * weights[:, None]
        back = (error @ w2.T) * (1 - hidden**2)
        gradients = [
            x.T @ back + l2 * w1,
            back.sum(axis=0),
            hidden.T @ error + l2 * w2,
            error.sum(axis=0),
        ]
        for p, g, m, v in zip(parameters, gradients, moments, squares, strict=True):
            m *= 0.9
            m += 0.1 * g
            v *= 0.999
            v += 0.001 * g * g
            p -= learning_rate * (m / (1 - 0.9**step)) / (np.sqrt(v / (1 - 0.999**step)) + 1e-8)
    return {
        "mean": mean.tolist(),
        "std": std.tolist(),
        **dict(
            zip(
                ["weights1", "bias1", "weights2", "bias2"],
                [p.tolist() for p in parameters],
                strict=True,
            )
        ),
    }


def train_multiclass(filename, output):
    try:
        path, destination = private_path(filename), private_path(output)
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("Manifest size")
        manifest = MulticlassTrainingManifest.model_validate_json(path.read_bytes())
        if destination.exists():
            raise EdgeError(
                "POSTURE_OUTPUT_EXISTS", "Use um novo destino; preserve o modelo anterior."
            )
        vectors, labels, groups = [], [], []
        counts = {}
        rng = np.random.default_rng(manifest.seed)
        for clip in manifest.clips:
            if clip.partition != "TRAIN":
                continue
            config = load_config(clip.configuration)
            if (
                config.source.kind != "FILE"
                or config.model.variant != "rtmo-s"
                or file_hash(Path(config.source.path)) != clip.sourceSha256
            ):
                raise ValueError("Training source/model mismatch")
            geometry = load_calibration(config.calibrationPath)["geometry"]
            count = 0
            for _, pose, label in labeled_poses(clip):
                mirrored = Pose(
                    tuple(
                        replace(p, x=1 - p.x if p.x is not None else None) for p in pose.landmarks
                    ),
                    pose.qualitySource,
                )
                missing_index = int(rng.choice([11, 12, 23, 24, 25, 26, 27, 28]))
                masked = Pose(
                    tuple(p for p in pose.landmarks if p.index != missing_index), pose.qualitySource
                )
                for sample in (pose, mirrored, masked):
                    vector = signed_descriptor(sample, geometry["width"], geometry["height"])
                    if vector is not None:
                        vectors.append(vector)
                        labels.append(label)
                        groups.append(clip.groupId)
                        count += 1
                if len(vectors) > 20000:
                    raise ValueError("Training sample limit")
            counts[clip.videoId] = count
        fitted = fit_mlp(
            vectors,
            labels,
            groups,
            manifest.seed,
            manifest.steps,
            manifest.learningRate,
            manifest.l2,
        )
        artifact = MulticlassArtifact(
            schemaVersion=2,
            descriptor=DESCRIPTOR,
            version=manifest.version,
            poseModelSha256=get_model_spec("rtmo-s").sha256,
            classes=CLASSES,
            contextMode="OPERATOR_CONFIRMED_FIXED_CAMERA",
            **fitted,
            training={
                "manifestSha256": file_hash(path),
                "protocol": manifest.model_dump(),
                "algorithm": "numpy-mlp-tanh32-adam; class/recording-group-balanced",
                "augmentation": (
                    "training only: horizontal mirror and one missing-joint mask; "
                    "native observations unchanged"
                ),
                "observationsIncludingAugmentation": len(labels),
                "samplesPerClip": counts,
                "independentAccuracyClaim": False,
            },
        )
        serialized = artifact.model_dump_json(indent=2) + "\n"
        if len(serialized.encode()) > 256 * 1024:
            raise ValueError("Artifact size")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
        return {
            "status": "ok",
            "command": "posture-train",
            "artifactPath": str(destination),
            "sha256": file_hash(destination),
            "trainingObservations": len(labels),
            "classCounts": {name: labels.count(i) for i, name in enumerate(CLASSES)},
            "cameraOpened": False,
            "approved": False,
        }
    except EdgeError:
        raise
    except (OSError, ValueError, TypeError, KeyError):
        raise EdgeError(
            "POSTURE_TRAINING_INVALID",
            "Confira manifesto multiclasse, rótulos, permissões, grupos e hashes.",
        ) from None
