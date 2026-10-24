"""Local episode matching, explicit exclusions and reproducible evaluation runs."""

import json
from pathlib import Path
from uuid import uuid4

from pydantic import Field, model_validator

from radar_edge.config import ProcessingConfig, StrictModel, load_config, private_path
from radar_edge.errors import EdgeError
from radar_edge.model import file_hash
from radar_edge.pipeline import run_pipeline


class Interval(StrictModel):
    startMs: int = Field(ge=0)
    endMs: int = Field(gt=0)
    reason: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def ordered(self):
        if self.endMs <= self.startMs:
            raise ValueError("Invalid interval")
        return self


class Target(Interval):
    kind: str = Field(pattern=r"^(PERSON_ON_FLOOR|POSSIBLE_FALL)$")
    assistanceNeeded: bool | None = None
    confounder: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def enough_time(self):
        if self.endMs - self.startMs < 2000:
            raise ValueError("Target is shorter than the baseline persistence window")
        return self


class VideoEntry(StrictModel):
    videoId: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
    config: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    authorized: bool
    retention: str = Field(min_length=1, max_length=120)
    personPseudonym: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    sessionId: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    environmentId: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    role: str = Field(pattern=r"^(CALIBRATION|EVALUATION)$")
    material: str = Field(pattern=r"^(REAL_VIDEO|SYNTHETIC)$")
    durationMs: int = Field(gt=0)
    fps: float = Field(gt=0, le=1000)
    annotationsComplete: bool = False
    targets: list[Target] = Field(default_factory=list, max_length=1000)
    excluded: list[Interval] = Field(default_factory=list, max_length=1000)
    origin: str | None = Field(default=None, max_length=1000)
    authorizationNote: str | None = Field(default=None, max_length=1000)
    confounders: list[Interval] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def check_ranges(self):
        for group in (self.targets, self.excluded, self.confounders):
            ordered = sorted(group, key=lambda x: x.startMs)
            for index, item in enumerate(ordered):
                if item.endMs > self.durationMs or (
                    index and item.startMs < ordered[index - 1].endMs
                ):
                    raise ValueError("Intervals overlap or exceed video")
        return self


class Manifest(StrictModel):
    schemaVersion: int = Field(default=1, ge=1, le=1)
    matchingToleranceMs: int = Field(default=2000, ge=2000, le=2000)
    videos: list[VideoEntry] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def no_repeated_or_leaked_sessions(self):
        if len({v.videoId for v in self.videos}) != len(self.videos) or len(
            {v.sha256 for v in self.videos}
        ) != len(self.videos):
            raise ValueError("Repeated file or identifier is not an independent sample")
        sessions = {}
        for video in self.videos:
            sessions.setdefault(video.sessionId, set()).add(video.role)
        if any(len(roles) > 1 for roles in sessions.values()):
            raise ValueError("Calibration and evaluation cannot share a session")
        return self


def excluded_at(t, excluded):
    return any(i.startMs <= t < i.endMs for i in excluded)


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def match_episodes(events, targets, excluded, eligible_ms, annotations_complete=True):
    results = {}
    for kind in ("PERSON_ON_FLOOR", "POSSIBLE_FALL"):
        annotated = [t for t in targets if t.kind == kind]
        expected = [
            t
            for t in targets
            if t.kind == kind
            and not any(i.startMs < t.endMs and i.endMs > t.startMs for i in excluded)
        ]
        unknown_targets = [t for t in annotated if t not in expected]
        matched, duplicate, false_positive, inconclusive, latencies = set(), 0, 0, 0, []
        alerts = sorted((e for e in events if e["kind"] == kind), key=lambda e: e["sourceOffsetMs"])
        for event in alerts:
            time = event["sourceOffsetMs"]
            if (
                excluded_at(time, excluded)
                or not annotations_complete
                or any(t.startMs <= time <= t.endMs + 2000 for t in unknown_targets)
            ):
                inconclusive += 1
                continue
            candidates = [
                index
                for index, target in enumerate(expected)
                if target.startMs <= time <= target.endMs + 2000
            ]
            unmatched = [index for index in candidates if index not in matched]
            if unmatched:
                index = unmatched[0]
                matched.add(index)
                latencies.append(time - expected[index].startMs)
            elif candidates:
                duplicate += 1
            else:
                false_positive += 1
        evaluable = len(alerts) - inconclusive
        results[kind] = {
            "targetsAnnotated": len(annotated),
            "targetsExcluded": len(annotated) - len(expected),
            "targets": len(expected),
            "alerts": len(alerts),
            "matched": len(matched),
            "missed": len(expected) - len(matched) if annotations_complete else None,
            "duplicates": duplicate,
            "unmatchedAlerts": false_positive,
            "inconclusiveAlerts": inconclusive,
            "recall": ratio(len(matched), len(expected)) if annotations_complete else None,
            "precision": ratio(len(matched), evaluable) if annotations_complete else None,
            "falseAlertsPerHour": ratio(false_positive, eligible_ms / 3600000)
            if annotations_complete
            else None,
            "detectorLatencyMs": latencies,
        }
    return results


def evaluate_manifest(filename, replay_speed=0.0):
    ProcessingConfig(replaySpeed=replay_speed)
    try:
        path = private_path(filename)
        if path.stat().st_size > 1024 * 1024:
            raise ValueError()
        manifest = Manifest.model_validate(json.loads(path.read_text(encoding="utf-8-sig")))
    except (ValueError, OSError):
        raise EdgeError(
            "INVALID_MANIFEST", "Confira o manifesto privado e os intervalos anotados."
        ) from None
    output = private_path(".local/evaluation") / str(uuid4())
    output.mkdir(parents=True)
    results, code = [], 0
    for entry in manifest.videos:
        if not entry.authorized:
            raise EdgeError(
                "VIDEO_AUTHORIZATION_REQUIRED", "O manifesto exige autorização local explícita."
            )
        config = load_config(entry.config)
        if (
            config.source.videoId != entry.videoId
            or file_hash(Path(config.source.path)) != entry.sha256
        ):
            raise EdgeError(
                "EVALUATION_SOURCE_MISMATCH", "Identificador ou hash não corresponde ao manifesto."
            )
        config.events.enabled = True
        config.events.delivery.enabled = False
        config.events.outboxPath = str(output / f"{entry.videoId}-{uuid4()}.sqlite")
        config.processing.preview = False
        config.processing.previewStartPaused = False
        config.processing.maxObservations = None
        config.processing.replaySpeed = replay_speed
        config.diagnostics.exportObservations = False
        report, result_code = run_pipeline(config, [(i.startMs, i.endMs) for i in entry.excluded])
        code = max(code, result_code)
        temporal = report["temporal"]
        if temporal.get("eventsTruncated"):
            raise EdgeError(
                "EVALUATION_LIMIT", "Mais de 1000 eventos; divida a avaliação e preserve a outbox."
            )
        if not result_code:
            fps = report["source"]["fpsMetadata"]
            duration = report["source"]["durationMsEstimate"]
            if abs(fps - entry.fps) > 0.005 * fps or abs(duration - entry.durationMs) > 1000 / fps:
                raise EdgeError(
                    "EVALUATION_METADATA_MISMATCH",
                    "FPS ou duração do manifesto diverge da fonte real.",
                )
        excluded_ms = sum(i.endMs - i.startMs for i in entry.excluded)
        eligible_ms = temporal.get("eligibleMediaMs", 0)
        results.append(
            {
                "videoId": entry.videoId,
                "sha256": entry.sha256,
                "material": entry.material,
                "personPseudonym": entry.personPseudonym,
                "sessionId": entry.sessionId,
                "environmentId": entry.environmentId,
                "role": entry.role,
                "annotationsComplete": entry.annotationsComplete,
                "origin": entry.origin,
                "authorizationNote": entry.authorizationNote,
                "confounders": [i.model_dump() for i in entry.confounders],
                "excluded": [i.model_dump() for i in entry.excluded],
                "configuration": entry.config,
                "model": report.get("model"),
                "calibration": report.get("calibration"),
                "targets": [t.model_dump() for t in entry.targets],
                "assistanceNeedEvaluation": (
                    "not estimated; posture targets and assistanceNeeded annotations are separate"
                ),
                "status": report["status"],
                "captureState": report["captureState"],
                "eligibleMediaMs": eligible_ms,
                "excludedAnnotatedMs": excluded_ms,
                "observedMediaMs": temporal.get("observedMediaMs", 0),
                "unobservedTailMs": max(0, entry.durationMs - temporal.get("observedMediaMs", 0)),
                "matching": match_episodes(
                    temporal.get("events", []),
                    entry.targets,
                    entry.excluded,
                    eligible_ms,
                    entry.annotationsComplete and not result_code,
                ),
                "pipelineReport": report["reportPath"],
                "policy": temporal.get("policy"),
                "events": temporal.get("events", []),
                "ineligibleReasons": temporal.get("ineligibleReasons", {}),
                "performance": report["metrics"],
            }
        )
    result = {
        "schemaVersion": 1,
        "command": "evaluate",
        "status": "ok" if not code else "error",
        "manifestSha256": file_hash(path),
        "matchingRule": "same kind; emission in target or <=2000ms after end; one match per target",
        "zeroDenominator": "null = não estimável",
        "httpDeliveryEnabled": False,
        "replaySpeed": replay_speed,
        "results": results,
    }
    report_path = output / "evaluation.json"
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    return {**result, "reportPath": str(report_path.relative_to(Path.cwd()))}, code
