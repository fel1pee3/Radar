"""Contract, missingness and recording isolation; no claim of recognition accuracy."""

import hashlib
import json
from dataclasses import replace

import numpy as np
import pytest
from test_posture_candidate import candidate, rtmo_observation

from radar_edge.features import extract_features
from radar_edge.model import get_model_spec
from radar_edge.observations import Pose
from radar_edge.policy import configured_policy
from radar_edge.posture_multiclass import (
    CLASSES,
    DESCRIPTOR,
    FEATURE_DIM,
    MulticlassArtifact,
    MulticlassClassifier,
    signed_descriptor,
)
from radar_edge.posture_multiclass_training import fit_mlp


def classifier(tmp_path, monkeypatch, winner):
    c, cal = candidate(tmp_path, monkeypatch)
    artifact = MulticlassArtifact(
        schemaVersion=2,
        descriptor=DESCRIPTOR,
        version="synthetic-v3",
        poseModelSha256=get_model_spec("rtmo-s").sha256,
        classes=CLASSES,
        mean=[0.0] * FEATURE_DIM,
        std=[1.0] * FEATURE_DIM,
        weights1=np.zeros((FEATURE_DIM, 32)).tolist(),
        bias1=[0.0] * 32,
        weights2=np.zeros((32, 4)).tolist(),
        bias2=[10.0 if i == winner else 0.0 for i in range(4)],
        contextMode="OPERATOR_CONFIRMED_FIXED_CAMERA",
        training={"synthetic": True},
    )
    from pathlib import Path

    path = Path(c.posture.artifactPath)
    path.write_text(artifact.model_dump_json())
    c.posture.artifactSha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    c.posture.method = "MULTICLASS_BODY_V3"
    c.events.policy["version"] = "floor-rtmo-score-posture-multiclass-v3-synthetic"
    p = configured_policy(c.events.policy)
    return MulticlassClassifier(c.posture, cal, get_model_spec("rtmo-s"), p), cal, p


def test_descriptor_preserves_up_down_orientation_and_missingness():
    o = rtmo_observation(0)
    pose = o.poses[0]
    a = signed_descriptor(pose, o.width, o.height)
    inverted = Pose(tuple(replace(p, y=1 - p.y) for p in pose.landmarks), pose.qualitySource)
    b = signed_descriptor(inverted, o.width, o.height)
    assert a.shape == (84,) and not np.allclose(a, b)
    partial = replace(pose, landmarks=tuple(p for p in pose.landmarks if p.index != 28))
    c = signed_descriptor(partial, o.width, o.height)
    assert c is not None and c[7 * 6 + 3 : 7 * 6 + 6].tolist() == [0, 0, 0]
    assert signed_descriptor(replace(pose, qualitySource="MEDIAPIPE"), o.width, o.height) is None


@pytest.mark.parametrize("winner", range(4))
def test_partial_pose_can_reject_floor_but_cannot_confirm_floor(tmp_path, monkeypatch, winner):
    model, cal, policy = classifier(tmp_path, monkeypatch, winner)
    o = rtmo_observation(0)
    o = replace(o, poses=(replace(o.poses[0], landmarks=o.poses[0].landmarks[:-1]),))
    f = model.classify(o, extract_features(o, cal["floorPolygon"], policy))
    assert f.posture == CLASSES[winner] and not f.candidate
    assert f.eligible == (winner != 3)
    assert f.postureQualityReasons and f.postureEvidenceOrigin == "RTMO_PARTIAL_BODY"
    assert len(o.poses[0].landmarks) == 7


@pytest.mark.parametrize(
    "reason", ["LOW_LIGHT", "FRAME_TIMEOUT", "POSSIBLE_FROZEN", "QUALITY_POLICY_MISMATCH"]
)
def test_classification_never_overrides_capture_or_quality_origin(tmp_path, monkeypatch, reason):
    model, cal, policy = classifier(tmp_path, monkeypatch, 0)
    o = rtmo_observation(0)
    base = extract_features(o, cal["floorPolygon"], policy)
    f = model.classify(o, replace(base, eligible=False, reasons=(reason,)))
    assert not f.eligible and not f.candidate and reason in f.reasons


def test_fitting_is_seeded_and_rejects_missing_classes():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(48, FEATURE_DIM))
    labels = np.tile(np.arange(4), 12)
    groups = ["recording-a"] * 24 + ["recording-b"] * 24
    a = fit_mlp(x, labels, groups, steps=100)
    b = fit_mlp(x, labels, groups, steps=100)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    with pytest.raises(ValueError):
        fit_mlp(x, np.zeros(48), groups, steps=100)
