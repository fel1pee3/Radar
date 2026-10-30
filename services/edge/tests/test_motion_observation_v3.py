"""Observed torso orientation is separate from uncertain posture and floor evidence."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from test_posture_candidate import rtmo_observation

from radar_edge.body_context import apply_body_context
from radar_edge.evidence_engine import create_engine
from radar_edge.features import Features, extract_features
from radar_edge.policy import configured_policy
from radar_edge.posture_multiclass import usable_body

CONTEXT = ("camera", "calibration", 1, "rtmo", 640, 480, 0)


def engine(version="POSTURE_DYNAMICS_V3"):
    return create_engine(
        configured_policy(
            {
                "version": "floor-rtmo-score-posture-context-v4-motion-test",
                "qualitySource": "RTMO_KEYPOINT_SCORE",
                "temporalMode": "EVIDENCE_V2",
                "transitionEvidence": version,
            }
        )
    )


def feature(
    t,
    *,
    posture="UNKNOWN",
    eligible=False,
    upright=True,
    angle=15,
    x=0.3,
    y=0.3,
    candidate=False,
    reasons=None,
):
    return Features(
        timestampMs=t,
        context=CONTEXT,
        eligible=eligible,
        reasons=tuple(
            reasons if reasons is not None else (() if eligible else ("POSTURE_UNCERTAIN",))
        ),
        candidate=candidate,
        torsoAngleDeg=angle,
        bboxAspectRatio=0.8,
        hipInFloorZone=True,
        hipX=x,
        hipY=y,
        shoulderX=x - 0.1,
        shoulderY=y - 0.1,
        bodyScale=0.5,
        posture=posture,
        observedUprightTorso=upright,
    )


def lying(t, **changes):
    return replace(
        feature(
            t, posture="LYING", eligible=True, upright=False, angle=80, x=0.5, y=0.6, candidate=True
        ),
        **changes,
    )


def hold_floor(e, start=600, end=3000):
    emissions = []
    for t in range(start, end, 200):
        value = e.step(lying(t))
        if value:
            emissions.append(value)
    return emissions


def test_unknown_class_keeps_uncertainty_but_current_torso_has_orientation():
    original = rtmo_observation(0)
    coords = {
        11: (0.45, 0.15),
        12: (0.55, 0.15),
        23: (0.45, 0.40),
        24: (0.55, 0.40),
        25: (0.46, 0.65),
        26: (0.54, 0.65),
        27: (0.46, 0.90),
        28: (0.54, 0.90),
    }
    points = tuple(
        replace(p, x=coords[p.index][0], y=coords[p.index][1]) for p in original.poses[0].landmarks
    )
    observation = replace(original, poses=(replace(original.poses[0], landmarks=points),))
    floor = [(0, 0), (1, 0), (1, 1), (0, 1)]
    classifier = SimpleNamespace(
        calibration_floor=floor,
        artifact=SimpleNamespace(qualityThreshold=0.5),
        settings=SimpleNamespace(
            excludedRegions=[],
            supportRegions=[],
            floorContextStrategy="DISTRIBUTED_V4",
            postureAmbiguityStrategy="KEEP_UNKNOWN",
        ),
    )
    base = replace(
        extract_features(observation, floor, engine().policy),
        posture="UNKNOWN",
        eligible=False,
        reasons=("POSTURE_UNCERTAIN",),
    )
    result = apply_body_context(classifier, observation, base, usable_body(observation.poses[0]))
    assert result.observedUprightTorso is True
    assert result.posture == "UNKNOWN" and not result.eligible and not result.candidate
    assert result.reasons == ("POSTURE_UNCERTAIN",)
    missing = replace(
        observation,
        poses=(replace(observation.poses[0], landmarks=tuple(p for p in points if p.index != 12)),),
    )
    partial = apply_body_context(classifier, missing, base, usable_body(missing.poses[0]))
    assert partial.observedUprightTorso is None
    assert partial.posture == "UNKNOWN" and not partial.eligible


@pytest.mark.parametrize(
    "mode,kind",
    [
        ("POSTURE_DYNAMICS_V2", "PERSON_ON_FLOOR"),
        ("POSTURE_DYNAMICS_V3", "POSSIBLE_FALL"),
    ],
)
def test_orientation_dwell_can_support_transition_without_relabeling_unknown(mode, kind):
    e = engine(mode)
    support = [feature(t) for t in (0, 200, 400)]
    for f in support:
        assert not e.step(f)
        assert f.posture == "UNKNOWN" and not f.eligible
    events = hold_floor(e)
    assert len(events) == 1 and events[0].kind == kind
    assert events[0].detectedMs == 2600
    assert events[0].floorDurationMs == 2000
    assert e.policy.maxObservationGapMs == 500
    assert e.policy.rearmHoldMs == 3000


@pytest.mark.parametrize(
    "middle",
    [
        feature(200, upright=None),
        feature(200, upright=None, posture="PERSON_POSE_INSUFFICIENT", reasons=("NO_POSE",)),
        feature(200, upright=True, reasons=("FRAME_TIMEOUT",)),
        feature(200, upright=False, angle=70),
    ],
)
def test_support_must_be_consecutive_real_torso_observations(middle):
    e = engine()
    for f in (feature(0), middle, feature(400)):
        assert not e.step(f)
    events = hold_floor(e)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


def test_long_gap_discards_prior_orientation_without_extending_tolerance():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    events = hold_floor(e, 1200, 3600)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"
    assert events[0].detectedMs == 3200


def test_short_dwell_is_not_support():
    e = engine()
    for t in (0, 200):
        e.step(feature(t))
    events = hold_floor(e, 400, 2800)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


def test_rotation_without_body_displacement_is_not_a_transition():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    events = []
    for t in range(600, 3000, 200):
        value = e.step(lying(t, hipX=0.3, hipY=0.3, shoulderX=0.2, shoulderY=0.2))
        if value:
            events.append(value)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


def test_no_fall_for_a_person_already_lying():
    events = hold_floor(engine(), 0, 2600)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


def test_motion_after_early_lying_label_is_still_observed():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    e.step(
        lying(
            600,
            torsoAngleDeg=30,
            hipX=0.32,
            hipY=0.32,
            shoulderX=0.22,
            shoulderY=0.22,
            observedUprightTorso=True,
        )
    )
    events = hold_floor(e, 800, 3000)
    assert len(events) == 1 and events[0].kind == "POSSIBLE_FALL"


def test_uncertain_upright_orientation_does_not_rearm_or_duplicate_episode():
    e = engine()
    events = hold_floor(e, 0, 2600)
    assert len(events) == 1
    for t in range(2600, 6600, 200):
        assert not e.step(feature(t))
    assert e.state == "ACTIVE" and not e.closed
    for t in range(6600, 10000, 200):
        assert not e.step(feature(t, posture="STANDING_OR_WALKING", eligible=True))
    assert e.state == "OBSERVING"
    assert len(hold_floor(e, 10000, 12400)) == 1


def test_motion_v3_requires_the_explicit_context_family():
    with pytest.raises(ValueError, match="Motion"):
        configured_policy(
            {
                "version": "floor-rtmo-score-posture-multiclass-v3-test",
                "qualitySource": "RTMO_KEYPOINT_SCORE",
                "temporalMode": "EVIDENCE_V2",
                "transitionEvidence": "POSTURE_DYNAMICS_V3",
            }
        )


def test_confident_lying_class_is_not_upright_support_even_when_image_axis_is_vertical():
    e = engine()
    for t in (0, 200, 400):
        assert not e.step(
            lying(
                t,
                observedUprightTorso=True,
                torsoAngleDeg=15,
                hipX=0.3,
                hipY=0.3,
                shoulderX=0.2,
                shoulderY=0.2,
            )
        )
    events = hold_floor(e)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


@pytest.mark.parametrize(
    "group_evidence,kind",
    [
        (False, "PERSON_ON_FLOOR"),
        (True, "POSSIBLE_FALL"),
    ],
)
def test_other_posture_needs_explicit_non_floor_group_evidence(group_evidence, kind):
    e = engine()
    for t in (0, 200, 400):
        assert not e.step(
            replace(
                feature(t, posture="OTHER_POSTURE", eligible=True),
                postureSubtypeUncertain=group_evidence,
            )
        )
    events = hold_floor(e)
    assert len(events) == 1 and events[0].kind == kind


def missing(t, reasons=("NO_POSE", "MISSING_ESSENTIAL_LANDMARK")):
    return replace(
        feature(t, upright=None, posture="PERSON_POSE_INSUFFICIENT", reasons=reasons),
        hipX=None,
        hipY=None,
        shoulderX=None,
        shoulderY=None,
        torsoAngleDeg=None,
        bodyScale=None,
    )


def test_missing_inside_motion_adds_no_pose_or_dwell_but_bounded_real_endpoints_can_match():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    absent = missing(600)
    assert not e.step(absent)
    assert e.motion_v3_history[-1] == (600, None)
    assert absent.hipX is None and absent.posture == "PERSON_POSE_INSUFFICIENT"
    events = hold_floor(e, 800, 3200)
    assert len(events) == 1 and events[0].kind == "POSSIBLE_FALL"
    assert events[0].startedMs == 800 and events[0].detectedMs == 2800


def test_repeated_missing_measurements_clear_support_after_real_gap_above_500():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    for t in (600, 800, 1000):
        assert not e.step(missing(t))
    assert not e.motion_v3_history
    events = hold_floor(e, 1200, 3600)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


def test_capture_failure_clears_completed_support_even_when_short():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    assert not e.step(missing(600, ("FRAME_TIMEOUT",)))
    assert not e.motion_v3_history
    events = hold_floor(e, 800, 3200)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"


def test_previously_completed_support_never_extends_the_1000ms_motion_window():
    e = engine()
    for t in (0, 200, 400):
        e.step(feature(t))
    for t in range(600, 1600, 200):
        assert not e.step(feature(t, upright=False, angle=45, x=0.32, y=0.32))
    events = hold_floor(e, 1600, 4000)
    assert len(events) == 1 and events[0].kind == "PERSON_ON_FLOOR"
