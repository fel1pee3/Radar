"""V4 protects current evidence, supports and old policy behavior."""

from dataclasses import replace

import pytest
from test_posture_candidate import rtmo_observation
from test_posture_multiclass import classifier

from radar_edge.body_context import apply_body_context
from radar_edge.evidence_engine import create_engine
from radar_edge.features import extract_features
from radar_edge.observations import Pose
from radar_edge.policy import configured_policy
from radar_edge.posture_multiclass import usable_body


def result(model, o, cal, p):
    f = model.classify(o, extract_features(o, cal["floorPolygon"], p))
    return apply_body_context(model, o, f, usable_body(o.poses[0]))


def test_partial_side_current_evidence_without_inventing_joint(tmp_path, monkeypatch):
    model, cal, p = classifier(tmp_path, monkeypatch, 3)
    o = rtmo_observation(0)
    o = replace(
        o,
        poses=(
            replace(o.poses[0], landmarks=tuple(x for x in o.poses[0].landmarks if x.index != 28)),
        ),
    )
    assert result(model, o, cal, p).candidate
    assert len(o.poses[0].landmarks) == 7
    o = replace(
        o,
        poses=(
            replace(
                o.poses[0],
                landmarks=tuple(x for x in o.poses[0].landmarks if x.index not in (25, 27)),
            ),
        ),
    )
    assert not result(model, o, cal, p).candidate


@pytest.mark.parametrize("kind", ["CHAIR", "BED", "HAMMOCK", "AMBIGUOUS"])
def test_torso_support_wins_over_feet_on_floor(tmp_path, monkeypatch, kind):
    from radar_edge.config import SupportRegion

    model, cal, p = classifier(tmp_path, monkeypatch, 3)
    o = rtmo_observation(0)
    points = {x.index: x for x in o.poses[0].landmarks}
    q = points[11]
    model.settings.supportRegions = [
        SupportRegion(
            kind=kind,
            polygon=[
                (q.x - 0.03, q.y - 0.03),
                (q.x + 0.03, q.y - 0.03),
                (q.x + 0.03, q.y + 0.03),
                (q.x - 0.03, q.y + 0.03),
            ],
        )
    ]
    f = result(model, o, cal, p)
    assert not f.candidate and f.regionState == "EXCLUDED"


def test_no_floor_from_bbox_only_or_foot_only(tmp_path, monkeypatch):
    model, cal, p = classifier(tmp_path, monkeypatch, 3)
    o = rtmo_observation(0)
    q = {x.index: x for x in o.poses[0].landmarks}[27]
    model._floor = [
        (q.x - 0.01, q.y - 0.01),
        (q.x + 0.01, q.y - 0.01),
        (q.x + 0.01, q.y + 0.01),
        (q.x - 0.01, q.y + 0.01),
    ]
    f = result(model, o, cal, p)
    assert not f.candidate and f.regionState == "UNKNOWN"


def test_real_shoulder_support_can_confirm_without_falsifying_hip(tmp_path, monkeypatch):
    model, cal, p = classifier(tmp_path, monkeypatch, 3)
    o = rtmo_observation(0)
    # Test independently of original synthetic layout: hip pair above polygon;
    # real shoulder and two real distal joints inside. No virtual footprint.
    coords = {
        11: (0.3, 0.7),
        12: (0.35, 0.7),
        23: (0.5, 0.55),
        24: (0.55, 0.55),
        25: (0.7, 0.7),
        26: (0.75, 0.7),
        27: (0.85, 0.75),
        28: (0.9, 0.75),
    }
    o = replace(
        o,
        poses=(
            Pose(
                tuple(
                    replace(x, x=coords[x.index][0], y=coords[x.index][1])
                    for x in o.poses[0].landmarks
                ),
                "RTMO_KEYPOINT_SCORE",
            ),
        ),
    )
    model._floor = [(0, 0.65), (1, 0.65), (1, 1), (0, 1)]
    f = result(model, o, cal, p)
    assert f.candidate and f.hipInFloorZone is False
    assert f.floorContextCompatible and 11 in f.contextEvidenceIndices


def motion_feature(t, posture, angle, x, y, candidate=False):
    from radar_edge.features import Features

    return Features(
        t,
        ("camera", "cal", 1, "rtmo", 640, 480, 0),
        True,
        (),
        candidate=candidate,
        posture=posture,
        hipX=x,
        hipY=y,
        shoulderX=x - 0.1,
        shoulderY=y - 0.1,
        bodyScale=0.5,
        torsoAngleDeg=angle,
        bboxAspectRatio=0.8,
        hipInFloorZone=True,
    )


def engine():
    return create_engine(
        configured_policy(
            dict(
                version="floor-rtmo-score-posture-context-v4-test",
                qualitySource="RTMO_KEYPOINT_SCORE",
                temporalMode="EVIDENCE_V2",
                transitionEvidence="POSTURE_DYNAMICS_V2",
            )
        )
    )


def test_motion_after_first_lying_and_single_episode_rearm():
    e = engine()
    for t in (0, 200, 400, 600):
        assert not e.step(motion_feature(t, "STANDING_OR_WALKING", 5, 0.3, 0.3))
    assert not e.step(motion_feature(800, "LYING", 25, 0.32, 0.32, True))
    event = None
    for t in range(1000, 3000, 200):
        event = e.step(motion_feature(t, "LYING", 80, 0.5, 0.6, True)) or event
    assert event and event.kind == "POSSIBLE_FALL"
    for t in range(3000, 6000, 200):
        assert not e.step(motion_feature(t, "LYING", 80, 0.5, 0.6, True))
    for t in range(6000, 9200, 200):
        assert not e.step(motion_feature(t, "STANDING_OR_WALKING", 5, 0.3, 0.3))
    assert e.state == "OBSERVING"


def test_missing_pose_and_long_gap_cannot_supply_motion():
    e = engine()
    for t in (0, 200, 400):
        e.step(motion_feature(t, "STANDING_OR_WALKING", 5, 0.3, 0.3))
    event = None
    for t in range(1200, 3400, 200):
        event = e.step(motion_feature(t, "LYING", 80, 0.5, 0.6, True)) or event
    assert event and event.kind == "PERSON_ON_FLOOR"


def test_already_lying_never_fall():
    e = engine()
    event = None
    for t in range(0, 2400, 200):
        event = e.step(motion_feature(t, "LYING", 80, 0.5, 0.6, True)) or event
    assert event.kind == "PERSON_ON_FLOOR"


def test_missing_hip_never_confirms_floor(tmp_path, monkeypatch):
    model, cal, p = classifier(tmp_path, monkeypatch, 3)
    o = rtmo_observation(0)
    o = replace(
        o,
        poses=(
            replace(o.poses[0], landmarks=tuple(x for x in o.poses[0].landmarks if x.index != 24)),
        ),
    )
    f = result(model, o, cal, p)
    assert not f.candidate and not f.bodyEvidenceSufficient


def test_uniform_image_scaling_preserves_observed_context(tmp_path, monkeypatch):
    model, cal, p = classifier(tmp_path, monkeypatch, 3)
    original = rtmo_observation(0)
    a = result(model, original, cal, p)
    model.geometry = {**model.geometry, "width": original.width * 2, "height": original.height * 2}
    b = result(
        model, replace(original, width=original.width * 2, height=original.height * 2), cal, p
    )
    assert (a.candidate, a.posture, a.contextEvidenceIndices) == (
        b.candidate,
        b.posture,
        b.contextEvidenceIndices,
    )
    assert a.torsoAngleDeg == pytest.approx(b.torsoAngleDeg)
    assert a.bodyScale == pytest.approx(b.bodyScale)


def test_ineligible_capture_never_supplies_transition_or_rearm():
    e = engine()
    for t in range(0, 800, 200):
        e.step(motion_feature(t, "STANDING_OR_WALKING", 5, 0.3, 0.3))
    for t in range(800, 1800, 200):
        e.step(
            replace(
                motion_feature(t, "LYING", 80, 0.5, 0.6, True),
                eligible=False,
                reasons=("FRAME_STALE",),
            )
        )
    emitted = None
    for t in range(1800, 4200, 200):
        emitted = e.step(motion_feature(t, "LYING", 80, 0.5, 0.6, True)) or emitted
    assert emitted.kind == "PERSON_ON_FLOOR"
    for t in range(4200, 8000, 200):
        e.step(
            replace(
                motion_feature(t, "STANDING_OR_WALKING", 5, 0.3, 0.3),
                eligible=False,
                reasons=("FRAME_STALE",),
            )
        )
    assert e.state == "ACTIVE"
