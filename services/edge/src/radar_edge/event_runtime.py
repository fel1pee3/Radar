"""Connect pure analysis to atomic storage and optional HTTP transport."""

import hashlib
import json
import os
import re
import sqlite3
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from radar_edge.config import private_path
from radar_edge.contracts import validate_contract
from radar_edge.delivery import Delivery
from radar_edge.engine import TemporalEngine
from radar_edge.errors import EdgeError
from radar_edge.features import QualityGate, extract_features
from radar_edge.model import get_model_spec
from radar_edge.outbox import FileLock, Outbox, encode
from radar_edge.policy import configured_policy

WORKER_VERSION = "edge-temporal-v1"
SCHEMAS = Path(__file__).resolve().parents[4] / "packages/contracts/src/schemas"


def event_payload(observation, features, emission, run, policy, evidence_mode):
    anchor = datetime.fromisoformat(run["anchor"].replace("Z", "+00:00"))

    def instant(ms):
        return (
            (anchor + timedelta(milliseconds=ms))
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    points = []
    if evidence_mode == "skeleton":
        points = [
            {"index": p.index, "x": p.x, "y": p.y, "visibility": p.visibility}
            for p in observation.poses[0].landmarks
            if 11 <= p.index <= 32
            and all(v is not None for v in (p.x, p.y, p.visibility))
            and 0 <= p.visibility <= 1
        ]
    value = {
        "schemaVersion": 1,
        "eventType": "INCIDENT_CANDIDATE",
        "eventId": str(uuid4()),
        "episodeId": str(uuid4()),
        "cameraId": observation.cameraId,
        "runId": run["run_id"],
        "mode": observation.mode,
        "kind": emission.kind,
        "occurredAt": instant(emission.startedMs),
        "detectedAt": instant(emission.detectedMs),
        "sourceOffsetMs": emission.detectedMs if observation.mode == "REPLAY" else None,
        "signals": {
            "floorDurationMs": emission.floorDurationMs,
            "torsoAngleDeg": features.torsoAngleDeg,
            "bboxAspectRatio": features.bboxAspectRatio,
            "hipInFloorZone": features.hipInFloorZone,
            "rapidDescentObserved": emission.rapidDescentObserved,
            "validPoseFraction": emission.validPoseFraction,
            "analysisFps": emission.analysisFps,
        },
        "pose": points,
        "versions": {
            "worker": WORKER_VERSION,
            "model": observation.modelId,
            "policy": policy.version,
            "calibration": f"{observation.calibrationId}-v{observation.calibrationVersion}",
        },
    }
    if not validate_contract("event-v1", value, SCHEMAS):
        raise EdgeError(
            "EVENT_CONTRACT_ERROR",
            "Evento não satisfaz o contrato compartilhado; processamento interrompido.",
        )
    return value


class EventRuntime:
    def __init__(
        self, config, calibration, video_hash, geometry, excluded=None, async_delivery=False
    ):
        self.config, self.calibration = config, calibration
        self.async_delivery = async_delivery
        self.model_spec = get_model_spec(config.model.variant)
        self.policy = configured_policy(config.events.policy)
        self.evidence_mode = os.environ.get("EVIDENCE_MODE", config.events.evidenceMode)
        if self.evidence_mode not in {"none", "skeleton"}:
            raise EdgeError(
                "INVALID_EVIDENCE_MODE",
                "Use EVIDENCE_MODE none ou skeleton; snapshot não faz parte desta etapa.",
            )
        if config.processing.minLandmarkVisibility != self.policy.minLandmarkVisibility:
            raise EdgeError(
                "POLICY_QUALITY_CONFLICT", "Visibilidade de processing e policy deve coincidir."
            )
        self.engine = TemporalEngine(self.policy)
        self.gate = QualityGate(self.policy)
        self.resources = ExitStack()
        self.delivery = None
        self.generated = self.processed = 0
        self.reasons = Counter()
        self.posture_exclusions = Counter()
        self.candidate_observations = 0
        self.eligible_ms = self.total_ms = 0
        self.previous_features = None
        self.excluded = excluded or []
        self.fingerprint = hashlib.sha256(
            encode(
                {
                    "video": video_hash,
                    "videoId": getattr(config.source, "videoId", None),
                    **(
                        {"device": config.source.model_dump()}
                        if config.source.kind == "WEBCAM"
                        else {}
                    ),
                    "calibration": calibration,
                    "policy": self.policy.to_dict(),
                    "geometry": geometry.to_dict()
                    if hasattr(geometry, "to_dict")
                    else vars(geometry),
                    "model": self.model_spec.sha256,
                    "worker": WORKER_VERSION,
                    "processing": {
                        k: v
                        for k, v in config.processing.model_dump().items()
                        if k in {"maxWidth", "targetAnalysisFps", "minLandmarkVisibility"}
                    },
                    "evidenceMode": self.evidence_mode,
                }
            ).encode()
        ).hexdigest()

    def __enter__(self):
        try:
            self.resources.enter_context(
                FileLock(private_path(f".local/edge-locks/{self.config.cameraId}.lock"))
            )
            self.resources.enter_context(
                FileLock(private_path(self.config.events.outboxPath + ".lock"))
            )
            self.store = self.resources.enter_context(
                Outbox(self.config.events.outboxPath, self.config.cameraId)
            )
            self.run, self.resumed = self.store.execution(self.fingerprint)
            # Session identity is never resumed after ENDED. The SQLite execution
            # retains checkpoints/episodes; already stored envelopes stay immutable.
            self.capture_run_id = str(uuid4())
            self.engine.restore(json.loads(self.run["engine"]))
            if self.config.events.delivery.enabled and not self.async_delivery:
                self.delivery = Delivery(self.store, self.config.events.delivery)
                self.resources.callback(self.delivery.close)
                self.delivery.flush()
            return self
        except BaseException:
            self.resources.close()
            raise

    def __exit__(self, *_):
        self.resources.close()

    def process(self, observation):
        settings = self.config.events.delivery
        self.store.check_capacity(settings.maxItems, settings.maxBytes, extra_bytes=65536)
        f = self.gate.apply(
            observation,
            extract_features(observation, self.calibration["floorPolygon"], self.policy),
        )
        emission = self.engine.step(f)
        value = (
            event_payload(
                observation,
                f,
                emission,
                {**self.run, "run_id": self.capture_run_id},
                self.policy,
                self.evidence_mode,
            )
            if emission
            else None
        )
        try:
            self.store.checkpoint(
                self.run["run_id"], observation, self.engine, value, self.engine.closed
            )
        except sqlite3.Error:
            raise EdgeError(
                "STORAGE_ERROR",
                "Falha ao persistir episódio/checkpoint/outbox; "
                "execução interrompida sem envio HTTP.",
            ) from None
        self.generated += bool(value)
        self.processed += 1
        self.reasons.update(f.reasons)
        self.candidate_observations += bool(f.candidate)
        if f.eligible and not f.candidate:
            if not f.hipInFloorZone:
                self.posture_exclusions["HIP_OUTSIDE_FLOOR"] += 1
            if f.torsoAngleDeg < self.policy.minTorsoAngleDeg:
                self.posture_exclusions["TORSO_NOT_HORIZONTAL"] += 1
            if f.bboxAspectRatio > self.policy.maxBboxAspectRatio:
                self.posture_exclusions["BBOX_NOT_HORIZONTAL"] += 1
        if self.previous_features is not None:
            dt = f.timestampMs - self.previous_features.timestampMs
            self.total_ms += dt
            if (
                f.eligible
                and self.previous_features.eligible
                and dt <= self.policy.maxObservationGapMs
            ):
                excluded_ms = sum(
                    max(0, min(f.timestampMs, end) - max(self.previous_features.timestampMs, start))
                    for start, end in self.excluded
                )
                self.eligible_ms += dt - excluded_ms
        self.previous_features = f
        if self.delivery:
            self.delivery.flush()
        return f

    def finish(self):
        self.store.finish(self.run["run_id"])
        if self.delivery:
            self.delivery.flush()

    def summary(self):
        events = self.store.events(self.run["run_id"])
        checkpoint = self.store.db.execute(
            "SELECT frame_index,timestamp_ms FROM executions WHERE run_id=?",
            (self.run["run_id"],),
        ).fetchone()
        return {
            "enabled": True,
            "runId": self.run["run_id"],
            "resumed": self.resumed,
            "initialCheckpointFrame": self.run["frame_index"],
            "lastPersistedCheckpointFrame": checkpoint["frame_index"],
            "lastPersistedCheckpointTimestampMs": checkpoint["timestamp_ms"],
            "alreadyCompleted": bool(self.run["completed"]),
            "state": self.engine.state,
            "generatedEvents": self.generated,
            "processedObservations": self.processed,
            "ineligibleReasons": dict(self.reasons),
            "postureExclusions": dict(self.posture_exclusions),
            "candidateObservations": self.candidate_observations,
            "eligibleMediaMs": self.eligible_ms,
            "observedMediaMs": self.total_ms,
            "policy": self.policy.to_dict(),
            "outbox": self.store.summary(),
            "deliveryErrors": self.store.delivery_errors(),
            "eventsTruncated": len(events) > 1000,
            "events": [
                {
                    "eventId": e["eventId"],
                    "episodeId": e["episodeId"],
                    "kind": e["kind"],
                    "sourceOffsetMs": e["sourceOffsetMs"],
                }
                for e in events[:1000]
            ],
        }


def manage_outbox(config, command, reason=None, resume_auth=False):
    if not config.events.enabled:
        raise EdgeError("EVENTS_DISABLED", "Habilite events na configuração privada da etapa 05.")
    with ExitStack() as resources:
        resources.enter_context(FileLock(private_path(f".local/edge-locks/{config.cameraId}.lock")))
        resources.enter_context(FileLock(private_path(config.events.outboxPath + ".lock")))
        store = resources.enter_context(Outbox(config.events.outboxPath, config.cameraId))
        if command == "reset-episode":
            if not reason or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,119}", reason):
                raise EdgeError(
                    "RESET_REASON_REQUIRED",
                    "Informe --reason com motivo técnico de 3–120 caracteres, sem dados pessoais.",
                )
            store.reset(reason)
        elif command == "deliver":
            delivery = Delivery(store, config.events.delivery)
            resources.callback(delivery.close)
            delivery.flush(resume_auth)
        return {
            "status": "ok",
            "command": command,
            "outbox": store.summary(),
            "deliveryErrors": store.delivery_errors(),
            "items": store.items(),
        }
