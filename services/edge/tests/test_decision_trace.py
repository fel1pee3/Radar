"""Decision diagnostics preserve genuine observations, storage and privacy boundaries."""

import json
import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from temporal_support import GEOMETRY, calibration, config, observation

from radar_edge.config import DiagnosticsConfig
from radar_edge.decision_trace import DecisionTrace, temporal_state
from radar_edge.engine import TemporalEngine
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime
from radar_edge.features import extract_features


def directory(root=Path(".local/results")):
    path = root / str(uuid4())
    path.mkdir(parents=True)
    return path


@pytest.mark.parametrize("mode", ["REPLAY", "LIVE"])
def test_trace_does_not_change_episode_payload_decisions_or_fingerprint(
    tmp_path, monkeypatch, mode
):
    monkeypatch.chdir(tmp_path)
    outcomes, identities = [], []
    for enabled in [False, True]:
        c = config()
        c.events.outboxPath = f".local/outbox-{enabled}.sqlite"
        c.diagnostics.exportDecisions = enabled
        trace = DecisionTrace(directory(), c.diagnostics)
        try:
            with EventRuntime(c, calibration(), "hash", GEOMETRY, decision_trace=trace) as runtime:
                identities.append(runtime.fingerprint)
                runtime.run["anchor"] = "2000-01-01T00:00:00.000Z"
                for t in range(0, 2800, 200):
                    runtime.process(replace(observation(t), mode=mode))
                events = runtime.store.events(runtime.run["run_id"])
                outcomes.append(
                    [
                        {
                            k: event[k]
                            for k in [
                                "kind",
                                "occurredAt",
                                "detectedAt",
                                "signals",
                                "pose",
                                "versions",
                            ]
                        }
                        for event in events
                    ]
                )
        finally:
            trace.close()
    assert identities[0] == identities[1]
    assert outcomes[0] == outcomes[1] and len(outcomes[0]) == 1
    records = [json.loads(line) for line in trace.path.read_text().splitlines()]
    assert records[0]["timestampMs"] == 0
    assert records[1]["temporalAfter"]["coveredWindowMs"] == 200
    emitted = [record for record in records if record["emission"]]
    assert len(emitted) == 1
    assert emitted[0]["emission"]["detectedMs"] == 2000
    assert records[-1]["decisionReasons"] == ["EXISTING_EPISODE_SUPPRESSES_NEW_EMISSION"]


def test_unknown_is_not_empty_scene_or_positive_evidence_and_none_redacts_points(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    c = config()
    c.diagnostics.exportDecisions = True
    trace = DecisionTrace(directory(), c.diagnostics, evidence_mode="none")
    try:
        with EventRuntime(c, calibration(), "hash", GEOMETRY, decision_trace=trace) as runtime:
            runtime.process(observation(0))
            runtime.process(
                replace(
                    observation(200),
                    poses=(),
                    poseCount=0,
                    inferenceState="NO_POSE",
                    qualityReasons=("NO_POSE",),
                )
            )
    finally:
        trace.close()
    records = [json.loads(line) for line in trace.path.read_text().splitlines()]
    assert records[1]["posture"] == "NO_PERSON_DETECTED"
    assert records[1]["quality"]["eligible"] is False
    assert records[1]["emission"] is None
    assert "UNCERTAIN_NO_POSITIVE_EVIDENCE" in records[1]["decisionReasons"]
    assert "hipY" not in records[0]["features"]
    assert not {"hipX", "shoulderX", "shoulderY", "bodyScale"} & records[0]["features"].keys()
    assert all("x" not in p and "score" not in p for p in records[0]["quality"]["essential"])


def test_retention_and_directory_budget_never_touch_other_diagnostics(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = Path(".local/results")
    old, current = directory(root), directory(root)
    expired = old / "decisions.jsonl"
    expired.write_text("old trace")
    source = old / "observations.jsonl"
    source.write_text("preserve previous observations")
    before = (datetime.now(UTC) - timedelta(days=8)).timestamp()
    os.utime(expired, (before, before))
    settings = DiagnosticsConfig(exportDecisions=True, maxDecisionDirectoryBytes=1024)
    trace = DecisionTrace(current, settings)
    try:
        for _ in range(100):
            trace.status("RUNNING", "SYNTHETIC")
    finally:
        trace.close()
    assert trace.summary()["expiredTracesRemoved"] == 1
    assert source.read_text() == "preserve previous observations"
    assert not expired.exists()
    assert trace.bytes <= 1024 and trace.truncated
    other = DecisionTrace(directory(root), settings)
    try:
        other.status("ENDED", "SYNTHETIC")
        assert trace.bytes + other.bytes <= 1024
    finally:
        other.close()


def test_root_lock_and_record_limit_are_explicit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = DiagnosticsConfig(exportDecisions=True, maxDecisionRecords=1)
    first = DecisionTrace(directory(), settings)
    with pytest.raises(EdgeError) as error:
        DecisionTrace(directory(), settings)
    assert error.value.code == "DECISION_TRACE_UNAVAILABLE"
    first.status("RUNNING", "SYNTHETIC")
    first.status("ENDED", "SYNTHETIC")
    assert first.count == 1 and first.summary()["limitReason"] == "RECORD_LIMIT"
    first.close()
    second = DecisionTrace(directory(), settings)
    second.close()


def test_trace_failure_after_commit_cannot_erase_or_duplicate_an_event(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = config()
    c.diagnostics.exportDecisions = True
    trace = DecisionTrace(directory(), c.diagnostics)
    try:
        with EventRuntime(c, calibration(), "hash", GEOMETRY, decision_trace=trace) as runtime:
            for t in range(0, 2000, 200):
                runtime.process(observation(t))
            trace.stream.close()

            class BrokenStream:
                def write(self, _):
                    raise OSError("synthetic-private-value")

                def close(self):
                    pass

            trace.stream = BrokenStream()
            with pytest.raises(EdgeError) as error:
                runtime.process(observation(2000))
            assert error.value.code == "DECISION_TRACE_WRITE_ERROR"
            assert "synthetic-private-value" not in str(error.value)
            assert runtime.store.summary() == {"PENDING": 1}
            trace.status("ERROR", "DECISION_TRACE_WRITE_ERROR")
            assert trace.summary()["writeFailed"]
        with EventRuntime(c, calibration(), "hash", GEOMETRY) as resumed:
            resumed.process(observation(2200))
            assert len(resumed.store.events(resumed.run["run_id"])) == 1
    finally:
        trace.close()


def test_window_diagnostics_include_zero_origin_without_mutating_engine():
    engine = TemporalEngine()
    for t in [0, 200, 400]:
        engine.step(extract_features(observation(t), calibration()["floorPolygon"]))
    state = temporal_state(engine, 400)
    assert state["coveredWindowMs"] == 400 and state["validObservations"] == 3
    assert engine.start == 0 and len(engine.samples) == 3


def test_close_failure_releases_quota_lock_and_remains_explicit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = config()
    c.diagnostics.exportDecisions = True
    trace = DecisionTrace(directory(), c.diagnostics)
    trace.stream.close()

    class BrokenClose:
        def close(self):
            raise OSError("synthetic-private-value")

    trace.stream = BrokenClose()
    trace.close()
    assert trace.summary()["writeFailed"] and trace.lock is None
    another = DecisionTrace(directory(), c.diagnostics)
    another.close()
