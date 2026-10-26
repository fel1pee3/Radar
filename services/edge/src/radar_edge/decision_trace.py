"""Opt-in, bounded private diagnostics. Never frames, credentials or interpolated poses."""

import json
import math
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from radar_edge.errors import EdgeError
from radar_edge.observations import ESSENTIAL, point_confidence, point_usable
from radar_edge.outbox import FileLock


def temporal_state(engine, timestamp):
    start = engine.start if engine.start is not None else timestamp
    cutoff = max(start, timestamp - engine.policy.floorHoldMs)
    samples = list(engine.samples)
    covered = sum(
        b[0] - max(a[0], cutoff)
        for a, b in zip(samples, samples[1:], strict=False)
        if a[1] and b[1] and b[0] > cutoff and b[0] - a[0] <= engine.policy.maxObservationGapMs
    )
    return {
        "state": engine.state,
        "startedMs": engine.start,
        "lastCandidateMs": engine.last_candidate,
        "previousTimestampMs": engine.last.timestampMs if engine.last else None,
        "coveredWindowMs": covered,
        "requiredWindowMs": engine.policy.floorHoldMs,
        "validObservations": sum(valid for ts, valid in samples if ts >= cutoff),
        "rapidDescentObserved": engine.rapid,
        "transitionMotionAtMs": getattr(engine, "motion_at", None),
        "recoveryEvidenceMs": engine.rearm_ms,
        "negativeEvidenceMs": getattr(engine, "negative_ms", None),
        "mode": engine.policy.temporalMode,
        "episodeClosed": engine.closed,
    }


def _number(value):
    return value if value is not None and math.isfinite(value) else None


class DecisionTrace:
    def __init__(self, directory: Path, settings, evidence_mode="skeleton"):
        self.settings = settings
        self.path = directory / "decisions.jsonl"
        self.evidence_mode = evidence_mode
        self.stream = self.lock = None
        self.count = self.bytes = self.removed_expired = 0
        self.truncated = False
        self.write_failed = False
        self.limit_reason = None
        self.available_bytes = settings.maxDecisionBytes
        if not settings.exportDecisions:
            return
        # A single active writer per diagnostics root serializes quota and retention.
        try:
            self.lock = FileLock(directory.parent / ".decision-export.lock")
            self.lock.__enter__()
            existing_bytes = 0
            now = datetime.now(UTC).timestamp()
            for folder in directory.parent.iterdir():
                if folder.is_symlink() or not folder.is_dir():
                    continue
                try:
                    UUID(folder.name)
                except ValueError:
                    continue
                path = folder / "decisions.jsonl"
                if path.is_symlink() or not path.is_file():
                    continue
                stat = path.stat()
                if now - stat.st_mtime >= settings.decisionRetentionDays * 86400:
                    path.unlink()
                    self.removed_expired += 1
                else:
                    existing_bytes += stat.st_size
            self.available_bytes = min(
                settings.maxDecisionBytes,
                max(0, settings.maxDecisionDirectoryBytes - existing_bytes),
            )
            self.stream = self.path.open("xb")
        except Exception:
            self.close()
            raise EdgeError(
                "DECISION_TRACE_UNAVAILABLE",
                "Diagnóstico de decisões indisponível; "
                "confira acesso, espaço e outro exportador ativo.",
            ) from None

    @property
    def enabled(self):
        return self.settings.exportDecisions

    def write(self, value):
        if not self.enabled or self.truncated or self.write_failed:
            return
        data = (json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
        if self.count >= self.settings.maxDecisionRecords:
            self.limit_reason = "RECORD_LIMIT"
        elif self.bytes + len(data) > self.available_bytes:
            self.limit_reason = "BYTE_OR_DIRECTORY_LIMIT"
        if self.limit_reason:
            self.truncated = True
            return
        try:
            self.stream.write(data)
            self.stream.flush()
        except OSError:
            self.write_failed = True
            raise EdgeError(
                "DECISION_TRACE_WRITE_ERROR", "Falha ao gravar diagnóstico privado de decisões."
            ) from None
        self.count += 1
        self.bytes += len(data)

    def observation(self, o, features, policy, before, after, emission=None):
        if not self.enabled:
            return
        points = {p.index: p for p in o.poses[0].landmarks} if len(o.poses) == 1 else {}
        threshold = (
            policy.minKeypointScore
            if policy.qualitySource == "RTMO_KEYPOINT_SCORE"
            else policy.minLandmarkVisibility
        )
        quality = []
        for index in sorted(ESSENTIAL):
            point = points.get(index)
            item = {"index": index, "present": point is not None, "usable": False}
            if point is not None:
                item["usable"] = point_usable(point, threshold, policy.qualitySource)
                if self.evidence_mode != "none":
                    item.update(
                        x=_number(point.x),
                        y=_number(point.y),
                        score=point_confidence(point, policy.qualitySource),
                    )
            quality.append(item)
        posture = features.posture or (
            "NO_PERSON_DETECTED"
            if not o.poses
            else "PERSON_POSE_INSUFFICIENT"
            if not features.eligible
            else "PERSON_ON_FLOOR"
            if features.candidate
            else "UNKNOWN"
        )
        reasons = []
        if before is None:
            reasons.append("TEMPORAL_ENGINE_DISABLED")
        else:
            previous = before["previousTimestampMs"]
            if previous is not None and o.timestampMs - previous > policy.maxObservationGapMs:
                reasons.append("OBSERVATION_GAP_RESET")
            if not features.eligible:
                reasons.append("UNCERTAIN_NO_POSITIVE_EVIDENCE")
            if before["state"] in {"ACTIVE", "REARMING"}:
                reasons.append("EXISTING_EPISODE_SUPPRESSES_NEW_EMISSION")
            if before["state"] == "SUSPECTED" and after["state"] == "OBSERVING":
                reasons.append("SUSPICION_RESET")
            if after["episodeClosed"]:
                reasons.append("CONSISTENT_RECOVERY")
            if emission:
                reasons.append("PERSISTENCE_SATISFIED")
            elif features.candidate and after["state"] == "SUSPECTED":
                reasons.append("INSUFFICIENT_PERSISTENT_EVIDENCE")
        feature_values = asdict(features)
        if self.evidence_mode == "none":
            for name in (
                "hipY",
                "hipX",
                "shoulderX",
                "shoulderY",
                "bodyScale",
                "postureAttributes",
            ):
                feature_values.pop(name, None)
        self.write(
            {
                "schemaVersion": 1,
                "recordType": "DECISION",
                "timestampMs": o.timestampMs,
                "timestampSource": o.timestampSource,
                "frameIndex": o.frameIndex,
                "mode": o.mode,
                "runId": o.runId,
                "cameraId": o.cameraId,
                "modelId": o.modelId,
                "calibrationId": o.calibrationId,
                "calibrationVersion": o.calibrationVersion,
                "policyVersion": policy.version,
                "capture": "FRAME_AVAILABLE",
                "inferenceState": o.inferenceState,
                "perception": {
                    "personLocated": bool(o.personDetections) or bool(o.poses),
                    "poseAvailable": bool(o.poses),
                    "acceptedPersonScores": [box[4] for box in o.personDetections],
                    "topProposalScore": o.personProposalScore,
                    "passes": o.perceptionPasses,
                    "absenceDoesNotConfirmEmptyScene": True,
                },
                "posture": posture,
                "quality": {
                    "eligible": features.eligible,
                    "reasons": features.reasons,
                    "source": policy.qualitySource,
                    "threshold": threshold,
                    "essential": quality,
                    "coordinatesRedacted": self.evidence_mode == "none",
                },
                "features": feature_values,
                "criteria": {
                    "method": features.postureMethod or "BASELINE",
                    "candidate": features.candidate,
                    "regionState": features.regionState,
                    "hipInsideImageRegion": features.hipInFloorZone,
                    "torsoAnglePass": None
                    if features.postureModel or features.torsoAngleDeg is None
                    else features.torsoAngleDeg >= policy.minTorsoAngleDeg,
                    "aspectPass": None
                    if features.postureModel or features.bboxAspectRatio is None
                    else features.bboxAspectRatio <= policy.maxBboxAspectRatio,
                    "regionSemantics": "IMAGE_REGION_ONLY_NOT_PHYSICAL_FLOOR_CONTACT",
                },
                "temporalBefore": before,
                "temporalAfter": after,
                "decisionReasons": reasons,
                "emission": asdict(emission) if emission else None,
                "observationOrigin": "MODEL_MEASUREMENT_NO_PREVIEW_INTERPOLATION",
            }
        )

    def status(self, capture, reason):
        self.write(
            {
                "schemaVersion": 1,
                "recordType": "CAPTURE_STATUS",
                "recordedAt": datetime.now(UTC).isoformat(),
                "capture": capture,
                "reason": reason,
                "timestampMs": None,
                "timestampSource": "NOT_AN_OBSERVATION",
            }
        )

    def summary(self):
        return {
            "enabled": self.enabled,
            "records": self.count,
            "bytes": self.bytes,
            "truncated": self.truncated,
            "writeFailed": self.write_failed,
            "limitReason": self.limit_reason,
            "retentionDays": self.settings.decisionRetentionDays,
            "expiredTracesRemoved": self.removed_expired,
            "path": str(self.path) if self.enabled else None,
        }

    def close(self):
        if self.stream is not None:
            try:
                self.stream.close()
            except OSError:
                self.write_failed = True
            finally:
                self.stream = None
        if self.lock is not None:
            self.lock.__exit__(None, None, None)
            self.lock = None
