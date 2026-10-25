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
    transitionObserved: bool | None = None
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
    expectedPerson: bool = True
    targets: list[Target] = Field(default_factory=list, max_length=1000)
    excluded: list[Interval] = Field(default_factory=list, max_length=1000)
    origin: str | None = Field(default=None, max_length=1000)
    authorizationNote: str | None = Field(default=None, max_length=1000)
    confounders: list[Interval] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def check_ranges(self):
        if self.targets and not self.expectedPerson:
            raise ValueError("A target episode requires expected person presence")
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


def match_floor_acceptance(
    events,
    targets,
    excluded,
    eligible_ms,
    observed_ms,
    annotations_complete=True,
    max_latency_ms=5000,
    negative_expected_person=True,
    capture_eligible_ms=None,
):
    """New primary result: no target is removed for lack of pose or exclusions.

    Both event kinds can support persistent floor posture. Transition accuracy
    remains a separate question; this score never relabels an event as a fall.
    """
    matched = {}
    duplicates = unexpected = 0
    for event in sorted(events, key=lambda item: item["sourceOffsetMs"]):
        t = event["sourceOffsetMs"]
        candidates = [i for i, target in enumerate(targets) if target.startMs <= t <= target.endMs]
        available = [i for i in candidates if i not in matched]
        if available:
            index = available[0]
            matched[index] = t - targets[index].startMs
        elif candidates:
            duplicates += 1
        else:
            unexpected += 1
    coverage = ratio(eligible_ms, observed_ms)
    negative_coverage = (
        coverage
        if negative_expected_person
        else (ratio(capture_eligible_ms, observed_ms) if capture_eligible_ms is not None else None)
    )
    approval_coverage = coverage if targets else negative_coverage
    latencies = [matched[i] for i in sorted(matched)]
    unjustified_transitions = sum(
        event["kind"] == "POSSIBLE_FALL"
        and any(
            target.transitionObserved is False
            and target.startMs <= event["sourceOffsetMs"] <= target.endMs
            for target in targets
        )
        for event in events
    )
    return {
        "targets": len(targets),
        "matched": len(matched),
        "missed": len(targets) - len(matched),
        "withinDeadline": sum(latency <= max_latency_ms for latency in latencies),
        "late": sum(latency > max_latency_ms for latency in latencies),
        "maxLatencyMs": max_latency_ms,
        "latenciesMs": latencies,
        "duplicates": duplicates,
        "unmatchedAlerts": unexpected if annotations_complete else None,
        "unadjudicatedAlerts": unexpected if not annotations_complete else 0,
        "targetsOverlappingExclusions": sum(
            any(i.startMs < target.endMs and i.endMs > target.startMs for i in excluded)
            for target in targets
        ),
        "eligibleMs": eligible_ms,
        "observedMs": observed_ms,
        "eligibleFraction": coverage,
        "negativeResult": None
        if targets
        else (
            "FAIL"
            if events
            else "PASS"
            if annotations_complete
            and negative_coverage is not None
            and negative_coverage >= 0.8
            and observed_ms > 0
            else "INCONCLUSIVE"
        ),
        "approved": bool(
            annotations_complete
            and approval_coverage is not None
            and approval_coverage >= 0.8
            and len(matched) == len(targets)
            and not duplicates
            and not unexpected
            and not unjustified_transitions
            and all(latency <= max_latency_ms for latency in latencies)
        ),
        "eventKinds": [event["kind"] for event in events],
        "negativeExpectedPerson": negative_expected_person,
        "negativeObservationCoverage": negative_coverage if not targets else None,
        "unjustifiedTransitionAlerts": unjustified_transitions,
        "transitionAccuracyEvaluated": any(
            target.transitionObserved is not None for target in targets
        ),
    }


def guard_candidate_evaluation(entries):
    """Preflight every reserved clip before predictions; keep historical evaluations."""
    from radar_edge.calibration import load_calibration
    from radar_edge.model import get_model_spec
    from radar_edge.policy import configured_policy
    from radar_edge.posture import PostureClassifier

    final = []
    for entry in entries:
        config = load_config(entry.config)
        if config.posture.method == "BASELINE" or entry.role != "EVALUATION":
            continue
        classifier = PostureClassifier(
            config.posture,
            load_calibration(config.calibrationPath),
            get_model_spec(config.model.variant),
            configured_policy(config.events.policy),
        )
        protocol = classifier.artifact.training.get("protocol", {})
        consulted = [
            clip for clip in protocol.get("clips", []) if clip["partition"] != "FINAL_RESERVED"
        ]
        if not consulted:
            raise EdgeError("EVALUATION_PROVENANCE_REQUIRED", "Falta procedência do classificador.")
        session_split = protocol.get("splitStrategy", "PARTICIPANT") == "SESSION"
        if session_split and (
            not protocol.get("sessionIndependenceEstablished")
            or "unknown" in entry.sessionId.lower()
        ):
            raise EdgeError("EVALUATION_SESSION_REQUIRED", "Identifique a nova sessão de gravação.")
        if any(
            entry.sha256 == clip["sourceSha256"]
            or not session_split
            and entry.personPseudonym == clip["participantId"]
            or clip["sessionId"] is not None
            and entry.sessionId == clip["sessionId"]
            for clip in consulted
        ):
            raise EdgeError(
                "FINAL_EVALUATION_LEAKAGE",
                "Material/participante/sessão já consultado; use CALIBRATION para desenvolvimento.",
            )
        final.append(entry)
    if final and (
        sum(len(entry.targets) for entry in final) < 4
        or sum(not entry.targets for entry in final) < 8
    ):
        raise EdgeError(
            "FINAL_EVALUATION_INCOMPLETE",
            "Reserve pelo menos quatro episódios-alvo e oito vídeos negativos novos.",
        )


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
    guard_candidate_evaluation(manifest.videos)
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
                "matchingScope": "SECONDARY_LEGACY"
                if config.posture.method != "BASELINE"
                else "HISTORICAL_BASELINE",
                "pipelineReport": report["reportPath"],
                **(
                    {
                        "primaryFloorAcceptance": match_floor_acceptance(
                            temporal.get("events", []),
                            entry.targets,
                            entry.excluded,
                            eligible_ms,
                            temporal.get("observedMediaMs", 0),
                            entry.annotationsComplete and not result_code,
                            negative_expected_person=entry.expectedPerson,
                            capture_eligible_ms=temporal.get("captureEligibleMs"),
                        )
                    }
                    if config.posture.method != "BASELINE"
                    else {}
                ),
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
