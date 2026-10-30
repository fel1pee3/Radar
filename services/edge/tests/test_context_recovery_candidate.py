"""Causal opt-ins: current arm grounding and unresolved non-floor subtype."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from test_posture_candidate import rtmo_observation

from radar_edge.body_context import apply_body_context
from radar_edge.features import extract_features
from radar_edge.policy import configured_policy
from radar_edge.posture_multiclass import usable_body

FLOOR = [(0, 0.65), (1, 0.65), (1, 1), (0, 1)]
COORDS = {
    11: (0.20, 0.50),
    12: (0.25, 0.53),
    23: (0.50, 0.50),
    24: (0.55, 0.52),
    25: (0.70, 0.50),
    26: (0.75, 0.52),
    27: (0.90, 0.50),
    28: (0.95, 0.52),
    13: (0.30, 0.75),
    15: (0.55, 0.80),
}


def setup(strategy="ARTICULATED_ARM_V1", grouping="KEEP_UNKNOWN", coords=None):
    o = rtmo_observation(0)
    proto = o.poses[0].landmarks[0]
    points = tuple(replace(proto, index=i, x=x, y=y) for i, (x, y) in (coords or COORDS).items())
    o = replace(o, poses=(replace(o.poses[0], landmarks=points),))
    model = SimpleNamespace(
        settings=SimpleNamespace(
            floorContextStrategy=strategy,
            postureAmbiguityStrategy=grouping,
            excludedRegions=[],
            supportRegions=[],
        ),
        artifact=SimpleNamespace(qualityThreshold=0.5),
        calibration_floor=FLOOR,
    )
    p = configured_policy(
        dict(
            version="floor-rtmo-score-posture-context-v4-test",
            qualitySource="RTMO_KEYPOINT_SCORE",
            temporalMode="EVIDENCE_V2",
        )
    )
    observed = {point.index: point for point in points}
    f = replace(
        extract_features(o, FLOOR, p),
        posture="LYING",
        postureEvidenceOrigin="RTMO_FULL_BODY",
        hipX=(observed[23].x + observed[24].x) / 2,
        hipY=(observed[23].y + observed[24].y) / 2,
    )
    return model, o, f


def apply(m, o, f):
    return apply_body_context(m, o, f, usable_body(o.poses[0]))


def test_current_complete_arm_can_ground_a_lying_body_without_faking_hip():
    m, o, f = setup()
    r = apply(m, o, f)
    assert r.candidate and r.floorContextCompatible and r.hipInFloorZone is False
    assert r.contextSupportMechanism == "OBSERVED_ARM_CHAIN_2D"
    m.settings.floorContextStrategy = "DISTRIBUTED_V4"
    assert not apply(m, o, f).candidate


@pytest.mark.parametrize("fault", ["missing-wrist", "low-score", "coincident", "missing-torso"])
def test_no_grounding_from_incomplete_or_degenerate_arm(fault):
    m, o, f = setup()
    points = o.poses[0].landmarks
    if fault == "missing-wrist":
        points = tuple(p for p in points if p.index != 15)
    elif fault == "missing-torso":
        points = tuple(p for p in points if p.index != 12)
    elif fault == "low-score":
        points = tuple(replace(p, confidence=0.49) if p.index == 15 else p for p in points)
    else:
        q = next(p for p in points if p.index == 13)
        points = tuple(replace(p, x=q.x, y=q.y) if p.index == 15 else p for p in points)
    o = replace(o, poses=(replace(o.poses[0], landmarks=points),))
    assert not apply(m, o, f).candidate


@pytest.mark.parametrize("support", ["CHAIR", "BED", "HAMMOCK", "AMBIGUOUS"])
def test_configured_torso_support_still_vetoes_arm_grounding(support):
    m, o, f = setup()
    m.settings.supportRegions = [
        SimpleNamespace(
            kind=support, polygon=[(0.45, 0.45), (0.60, 0.45), (0.60, 0.60), (0.45, 0.60)]
        )
    ]
    assert not apply(m, o, f).candidate


def test_non_floor_group_does_not_claim_a_subtype_or_normal_activity():
    coords = {
        11: (0.48, 0.2),
        12: (0.52, 0.2),
        23: (0.48, 0.5),
        24: (0.52, 0.5),
        25: (0.48, 0.7),
        26: (0.52, 0.7),
        27: (0.48, 0.9),
        28: (0.52, 0.9),
    }
    m, o, f = setup(grouping="NON_FLOOR_GROUP_V1", coords=coords)
    f = replace(f, posture="UNKNOWN", postureClassScores=(0.49, 0.49, 0.019, 0.001))
    r = apply(m, o, f)
    assert r.posture == "OTHER_POSTURE" and r.postureSubtypeUncertain
    assert r.postureClassScores == f.postureClassScores
    assert r.eligible and not r.candidate
    m.settings.postureAmbiguityStrategy = "KEEP_UNKNOWN"
    assert apply(m, o, f).posture == "UNKNOWN"
    m.settings.postureAmbiguityStrategy = "NON_FLOOR_GROUP_V1"
    assert apply(m, o, replace(f, postureClassScores=(0.3, 0.3, 0.3, 0.1))).posture == "UNKNOWN"
    bad = replace(
        o,
        poses=(
            replace(o.poses[0], landmarks=tuple(p for p in o.poses[0].landmarks if p.index != 24)),
        ),
    )
    assert apply(m, bad, f).posture == "UNKNOWN"


@pytest.mark.parametrize("posture", ["UNKNOWN", "SEATED"])
def test_arm_context_can_enable_only_the_existing_observed_raised_knee_branch(posture):
    coords = {**COORDS, 25: (0.70, 0.20), 26: (0.75, 0.22)}
    m, o, f = setup(coords=coords)
    f = replace(f, posture=posture, postureClassScores=(0.001, 0.70, 0.001, 0.298))
    r = apply(m, o, f)
    assert r.candidate and r.posture == "LYING"
    assert r.postureEvidenceOrigin == "OBSERVED_RECLINED_TORSO_RAISED_KNEES_V4"
    assert not apply_body_context(
        m, o, f, usable_body(o.poses[0]), geometry_fallback=False
    ).candidate
    m.settings.supportRegions = [
        SimpleNamespace(
            kind="CHAIR", polygon=[(0.45, 0.45), (0.60, 0.45), (0.60, 0.60), (0.45, 0.60)]
        )
    ]
    assert not apply(m, o, f).candidate


def test_real_non_floor_group_can_rearm_but_absent_body_cannot():
    from radar_edge.evidence_engine import create_engine

    policy = configured_policy(
        dict(
            version="floor-rtmo-score-posture-context-v4-recovery-test",
            qualitySource="RTMO_KEYPOINT_SCORE",
            temporalMode="EVIDENCE_V2",
            transitionEvidence="POSTURE_DYNAMICS_V3",
        )
    )
    e = create_engine(policy)
    m, o, f = setup()
    lying = apply(m, o, f)
    emitted = None
    for t in range(0, 2400, 200):
        emitted = e.step(replace(lying, timestampMs=t)) or emitted
    assert emitted and emitted.kind == "PERSON_ON_FLOOR"
    for t in range(2400, 6000, 200):
        e.step(
            replace(
                lying,
                timestampMs=t,
                posture="UNKNOWN",
                candidate=False,
                eligible=False,
                reasons=("NO_POSE",),
            )
        )
    assert e.state == "ACTIVE"
    coords = {
        11: (0.48, 0.2),
        12: (0.52, 0.2),
        23: (0.48, 0.5),
        24: (0.52, 0.5),
        25: (0.48, 0.7),
        26: (0.52, 0.7),
        27: (0.48, 0.9),
        28: (0.52, 0.9),
    }
    m, o, f = setup(grouping="NON_FLOOR_GROUP_V1", coords=coords)
    negative = apply(
        m, o, replace(f, posture="UNKNOWN", postureClassScores=(0.49, 0.49, 0.019, 0.001))
    )
    assert negative.postureSubtypeUncertain and negative.posture == "OTHER_POSTURE"
    for t in range(6000, 9200, 200):
        assert not e.step(replace(negative, timestampMs=t))
    assert e.state == "OBSERVING"
