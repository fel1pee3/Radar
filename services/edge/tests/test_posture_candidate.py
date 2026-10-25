"""Synthetic contract/lifecycle checks, never a measurement of real pose accuracy."""

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from temporal_support import GEOMETRY, calibration, config, observation

from radar_edge.config import PostureConfig
from radar_edge.errors import EdgeError
from radar_edge.evaluation import guard_candidate_evaluation
from radar_edge.event_runtime import EventRuntime
from radar_edge.features import extract_features
from radar_edge.health import LiveHealth
from radar_edge.model import get_model_spec
from radar_edge.observations import ESSENTIAL, Pose
from radar_edge.policy import configured_policy
from radar_edge.posture import PostureClassifier, body_descriptor, calibration_digest


def candidate(tmp_path, monkeypatch, bias=10.0):
    monkeypatch.chdir(tmp_path)
    path = Path(".local/posture.json")
    path.parent.mkdir(exist_ok=True)
    artifact = {
        "schemaVersion": 1,
        "descriptor": "symmetric-body-context-35-v1",
        "version": "synthetic-contract-v1",
        "poseModelSha256": get_model_spec("rtmo-s").sha256,
        "installationIds": ["synthetic-room"],
        "mean": [0.0] * 35,
        "std": [1.0] * 35,
        "coefficients": [0.0] * 35 + [bias],
        "training": {"material": "SYNTHETIC_CONTRACT_FIXTURE"},
    }
    path.write_text(json.dumps(artifact))
    cal = {**calibration(), "geometry": asdict(GEOMETRY)}
    c = config()
    c.model.variant = "rtmo-s"
    c.model.path = ".local/not-opened.onnx"
    c.events.policy = {
        "version": "floor-rtmo-score-posture-synthetic-v1",
        "qualitySource": "RTMO_KEYPOINT_SCORE",
        "temporalMode": "EVIDENCE_V2",
    }
    c.posture = PostureConfig(
        method="LINEAR_CONTEXT_V1",
        artifactPath=str(path),
        artifactSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        installationId="synthetic-room",
        calibrationSha256=calibration_digest(cal),
        operatorConfirmed=True,
    )
    return c, cal


def rtmo_observation(t, floor=True):
    o = observation(t, floor)
    points = tuple(
        replace(p, visibility=None, presence=None, confidence=0.99)
        for p in o.poses[0].landmarks
        if p.index in ESSENTIAL
    )
    return replace(
        o, poses=(Pose(points, "RTMO_KEYPOINT_SCORE"),), modelId=get_model_spec("rtmo-s").model_id
    )


def test_artifact_tampering_context_and_pose_quality_cannot_create_positive(tmp_path, monkeypatch):
    c, cal = candidate(tmp_path, monkeypatch)
    policy = configured_policy(c.events.policy)
    classifier = PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)
    o = rtmo_observation(0)
    f = classifier.classify(o, extract_features(o, cal["floorPolygon"], policy))
    assert f.posture == "LYING" and f.candidate and len(f.postureAttributes) == 35
    absent = replace(o, poses=(), poseCount=0, inferenceState="NO_POSE")
    f = classifier.classify(absent, extract_features(absent, cal["floorPolygon"], policy))
    assert not f.candidate and not f.eligible and f.posture == "NO_PERSON_DETECTED"
    resized = replace(o, width=o.width // 2)
    f = classifier.classify(resized, extract_features(resized, cal["floorPolygon"], policy))
    assert not f.eligible and "POSTURE_GEOMETRY_UNSUPPORTED" in f.reasons
    with pytest.raises(EdgeError, match="Instalação"):
        PostureClassifier(c.posture, {**cal, "version": 2}, get_model_spec("rtmo-s"), policy)
    Path(c.posture.artifactPath).write_text('{"private": "must never appear in error"}')
    with pytest.raises(EdgeError) as failure:
        PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)
    assert failure.value.code == "POSTURE_ARTIFACT_INVALID"
    assert "private" not in failure.value.message


def test_excluded_support_or_outside_region_is_uncertainty_not_recovery(tmp_path, monkeypatch):
    c, cal = candidate(tmp_path, monkeypatch)
    c.posture.excludedRegions = [[(0.1, 0.65), (0.9, 0.65), (0.9, 0.9), (0.1, 0.9)]]
    policy = configured_policy(c.events.policy)
    classifier = PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)
    o = rtmo_observation(0)
    f = classifier.classify(o, extract_features(o, cal["floorPolygon"], policy))
    assert f.posture == "LYING" and not f.eligible and not f.candidate
    assert f.regionState == "EXCLUDED" and f.reasons == ("CONTEXT_EXCLUDED_REGION",)
    c.posture.excludedRegions = []
    outside = rtmo_observation(0, False)
    f = classifier.classify(outside, extract_features(outside, cal["floorPolygon"], policy))
    assert f.regionState == "OUTSIDE" and not f.eligible
    assert "LYING_OUTSIDE_OBSERVED_REGION" in f.reasons


def test_pause_and_restart_keep_episode_dedup_but_not_old_positive_timing(tmp_path, monkeypatch):
    c, cal = candidate(tmp_path, monkeypatch)
    with EventRuntime(c, cal, "synthetic", GEOMETRY) as runtime:
        for t in range(0, 1800, 200):
            runtime.process(rtmo_observation(t))
        assert runtime.generated == 0 and runtime.engine.start == 0
        runtime.break_observation()
        for t in range(1800, 3801, 200):
            runtime.process(rtmo_observation(t))
        assert runtime.generated == 1
        assert runtime.store.events(runtime.run["run_id"])[0]["sourceOffsetMs"] == 3800
        identity = runtime.fingerprint
    with EventRuntime(c, cal, "synthetic", GEOMETRY) as resumed:
        assert resumed.fingerprint == identity and resumed.resumed
        for t in range(4000, 6800, 200):
            resumed.process(rtmo_observation(t))
        assert resumed.generated == 0
        assert len(resumed.store.events(resumed.run["run_id"])) == 1


def test_uncertain_score_does_not_count_as_negative_or_positive(tmp_path, monkeypatch):
    c, cal = candidate(tmp_path, monkeypatch, bias=0.0)
    policy = configured_policy(c.events.policy)
    classifier = PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)
    o = rtmo_observation(0)
    f = classifier.classify(o, extract_features(o, cal["floorPolygon"], policy))
    assert f.posture == "UNKNOWN" and f.postureScore == 0.5
    assert not f.eligible and not f.candidate and f.reasons == ("POSTURE_UNCERTAIN",)
    assert body_descriptor(o).shape == (35,)
    health = LiveHealth(c, o.runId, cal)
    health.observation(o, f)
    assert health.snapshot()["qualityFlags"] == ["POSTURE_UNCERTAIN"]


def test_reserved_evaluation_rejects_consulted_participant_before_any_source_is_opened(
    tmp_path, monkeypatch
):
    c, cal = candidate(tmp_path, monkeypatch)
    path = Path(c.posture.artifactPath)
    artifact = json.loads(path.read_text())
    artifact["training"] = {
        "protocol": {
            "clips": [
                {
                    "partition": "SELECTION",
                    "sourceSha256": "a" * 64,
                    "participantId": "already-consulted",
                    "sessionId": None,
                }
            ]
        }
    }
    path.write_text(json.dumps(artifact))
    c.posture.artifactSha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr("radar_edge.evaluation.load_config", lambda _: c)
    monkeypatch.setattr("radar_edge.calibration.load_calibration", lambda _: cal)
    entry = SimpleNamespace(
        config="not-opened",
        role="EVALUATION",
        sha256="b" * 64,
        personPseudonym="already-consulted",
        sessionId="unknown",
    )
    with pytest.raises(EdgeError) as failure:
        guard_candidate_evaluation([entry])
    assert failure.value.code == "FINAL_EVALUATION_LEAKAGE"


def test_body_descriptor_does_not_use_absolute_image_position_or_body_size():
    o = rtmo_observation(0)
    moved = replace(
        o,
        poses=(
            Pose(
                tuple(
                    replace(p, x=p.x * 0.75 + 0.04, y=p.y * 0.75 + 0.03)
                    for p in o.poses[0].landmarks
                ),
                "RTMO_KEYPOINT_SCORE",
            ),
        ),
    )
    body = "symmetric-body-shape-29-v1"
    assert body_descriptor(o, body).shape == (29,)
    assert np.allclose(body_descriptor(o, body), body_descriptor(moved, body), atol=1e-12)
    assert not np.allclose(body_descriptor(o), body_descriptor(moved))


def test_body_model_requires_its_descriptor_policy_and_confirmed_current_calibration(
    tmp_path, monkeypatch
):
    c, cal = candidate(tmp_path, monkeypatch)
    path = Path(c.posture.artifactPath)
    artifact = json.loads(path.read_text())
    artifact.update(
        descriptor="symmetric-body-shape-29-v1",
        contextMode="OPERATOR_CONFIRMED_FIXED_CAMERA",
        mean=[0.0] * 29,
        std=[1.0] * 29,
        coefficients=[0.0] * 29 + [10.0],
    )
    path.write_text(json.dumps(artifact))
    c.posture.artifactSha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    c.posture.method = "LINEAR_BODY_V2"
    c.posture.installationId = "new-manually-confirmed-test-installation"
    c.events.policy["version"] = "floor-rtmo-score-posture-body-v2-synthetic"
    policy = configured_policy(c.events.policy)
    classifier = PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)
    o = rtmo_observation(0)
    f = classifier.classify(o, extract_features(o, cal["floorPolygon"], policy))
    assert f.candidate and f.postureMethod == "LINEAR_BODY_V2"
    assert len(f.postureAttributes) == 29
    with EventRuntime(c, cal, "synthetic", GEOMETRY) as runtime:
        for t in range(0, 2200, 200):
            runtime.process(rtmo_observation(t))
        event = runtime.store.events(runtime.run["run_id"])[0]
        assert event["versions"]["worker"] == "edge-posture-v2"
        assert event["kind"] == "PERSON_ON_FLOOR"
    with pytest.raises(EdgeError):
        PostureClassifier(c.posture, {**cal, "version": 2}, get_model_spec("rtmo-s"), policy)
    c.posture.method = "LINEAR_CONTEXT_V1"
    with pytest.raises(EdgeError):
        PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)


@pytest.mark.parametrize(
    "method,eligible", [("LINEAR_CONTEXT_V1", False), ("LINEAR_BODY_V2", True)]
)
def test_support_negative_evidence_is_versioned_without_changing_frozen_v1(
    tmp_path, monkeypatch, method, eligible
):
    c, cal = candidate(tmp_path, monkeypatch, bias=-10.0)
    if method == "LINEAR_BODY_V2":
        path = Path(c.posture.artifactPath)
        artifact = json.loads(path.read_text())
        artifact.update(
            descriptor="symmetric-body-shape-29-v1",
            contextMode="OPERATOR_CONFIRMED_FIXED_CAMERA",
            mean=[0.0] * 29,
            std=[1.0] * 29,
            coefficients=[0.0] * 29 + [-10.0],
        )
        path.write_text(json.dumps(artifact))
        c.posture.artifactSha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        c.posture.method = method
        c.events.policy["version"] = "floor-rtmo-score-posture-body-v2-synthetic"
    c.posture.excludedRegions = [[(0.1, 0.1), (0.9, 0.1), (0.9, 0.99), (0.1, 0.99)]]
    policy = configured_policy(c.events.policy)
    classifier = PostureClassifier(c.posture, cal, get_model_spec("rtmo-s"), policy)
    o = rtmo_observation(0, floor=False)
    f = classifier.classify(o, extract_features(o, cal["floorPolygon"], policy))
    assert f.eligible is eligible
    assert not f.candidate and f.posture == "STANDING_OR_WALKING"
    assert f.regionState == "EXCLUDED"
