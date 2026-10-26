"""Time, recovery, uncertainty and transition risks for the opt-in evidence engine."""

from dataclasses import replace

import pytest

from radar_edge.evidence_engine import EvidenceEngine
from radar_edge.features import Features
from radar_edge.policy import configured_policy

POLICY = configured_policy(
    {
        "version": "floor-rtmo-score-posture-synthetic-v1",
        "qualitySource": "RTMO_KEYPOINT_SCORE",
        "temporalMode": "EVIDENCE_V2",
    }
)


def feature(t, posture="LYING", hip=0.8):
    return Features(
        t,
        ("room",),
        posture != "UNKNOWN",
        (),
        candidate=posture == "LYING",
        hipY=hip,
        posture=posture,
    )


@pytest.mark.parametrize("oscillation", ["UNKNOWN", "OTHER_POSTURE"])
def test_single_short_oscillation_keeps_suspicion_but_never_adds_positive_time(oscillation):
    engine = EvidenceEngine(POLICY)
    emissions = []
    for t in range(0, 2200, 200):
        event = engine.step(feature(t, oscillation if t == 800 else "LYING"))
        if event:
            emissions.append(event)
    assert len(emissions) == 1 and emissions[0].detectedMs == 2000
    assert emissions[0].validPoseFraction == 0.8


def test_larger_gap_resets_suspicion_and_unknown_never_rearms_active():
    engine = EvidenceEngine(POLICY)
    for t in range(0, 1800, 200):
        engine.step(feature(t))
    assert engine.step(feature(2200)) is None and engine.start == 2200
    for t in range(2400, 4201, 200):
        engine.step(feature(t))
    assert engine.state == "ACTIVE"
    for t in range(4400, 10000, 200):
        assert engine.step(feature(t, "UNKNOWN")) is None
    assert engine.state == "ACTIVE" and not engine.closed
    for t in range(10000, 13001, 200):
        engine.step(feature(t, "STANDING_OR_WALKING"))
    assert engine.closed and engine.state == "OBSERVING"


def test_possible_fall_requires_observed_upright_sequence_not_only_hip_delta():
    kinds = []
    for preceding in ["OTHER_POSTURE", "STANDING_OR_WALKING"]:
        engine = EvidenceEngine(POLICY)
        for t in range(0, 800, 200):
            engine.step(feature(t, preceding, hip=0.4))
        for t in range(800, 2801, 200):
            event = engine.step(feature(t))
            if event:
                kinds.append(event.kind)
    assert kinds == ["PERSON_ON_FLOOR", "POSSIBLE_FALL"]
    with pytest.raises(ValueError, match="CONTEXT_CHANGED"):
        engine.step(replace(feature(3000), context=("another-room",)))


def test_dynamics_requires_orientation_and_real_body_motion_before_floor():
    policy = configured_policy(
        {
            "version": "floor-rtmo-score-posture-multiclass-v3-synthetic",
            "qualitySource": "RTMO_KEYPOINT_SCORE",
            "temporalMode": "EVIDENCE_V2",
            "transitionEvidence": "POSTURE_DYNAMICS_V1",
        }
    )

    def f(t, posture, angle, y):
        return replace(
            feature(t, posture, y),
            context=("room", "cal", 1, "rtmo", 640, 360, 0),
            hipX=0.5,
            bodyScale=0.5,
            torsoAngleDeg=angle,
            shoulderX=0.5,
            shoulderY=y - 0.2,
        )

    kinds = []
    for angle, y in [(0, 0.7), (70, 0.4), (70, 0.7)]:
        engine = EvidenceEngine(policy)
        for t in range(0, 800, 200):
            engine.step(f(t, "STANDING_OR_WALKING", 0, 0.4))
        for t in range(800, 2801, 200):
            event = engine.step(f(t, "LYING", angle, y))
            if event:
                kinds.append(event.kind)
    assert kinds == ["PERSON_ON_FLOOR", "PERSON_ON_FLOOR", "POSSIBLE_FALL"]


def test_dynamics_does_not_infer_transition_from_already_lying_start():
    policy = configured_policy(
        {
            "version": "floor-rtmo-score-posture-multiclass-v3-synthetic",
            "qualitySource": "RTMO_KEYPOINT_SCORE",
            "temporalMode": "EVIDENCE_V2",
            "transitionEvidence": "POSTURE_DYNAMICS_V1",
        }
    )
    engine = EvidenceEngine(policy)
    events = [e for t in range(0, 2400, 200) if (e := engine.step(feature(t)))]
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"
