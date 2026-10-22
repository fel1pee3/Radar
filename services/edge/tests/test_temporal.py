import math
from dataclasses import replace

import pytest
from temporal_support import POLYGON, observation

from radar_edge.engine import TemporalEngine
from radar_edge.features import QualityGate, extract_features
from radar_edge.observations import Pose
from radar_edge.policy import configured_policy


def feature(t, floor=True, **changes):
    return replace(extract_features(observation(t, floor), POLYGON), **changes)


def feed(engine, times, **kwargs):
    return [e for t in times if (e := engine.step(feature(t, **kwargs))) is not None]


def test_geometry_uses_pixels_and_floor_not_normalized_angle():
    o = observation(0)
    f = extract_features(o, POLYGON)
    assert f.eligible and f.candidate and f.hipInFloorZone
    assert f.torsoAngleDeg == pytest.approx(90)
    assert f.bboxAspectRatio == pytest.approx(0.04 * 360 / (0.72 * 640))
    points = list(o.poses[0].landmarks)
    for i in [12, 24]:
        points[i - 11] = replace(points[i - 11], y=points[i - 11].y + 0.2)
    f = extract_features(replace(o, poses=(Pose(tuple(points)),)), POLYGON)
    assert f.torsoAngleDeg == pytest.approx(90)
    assert not extract_features(observation(0, False), POLYGON).candidate
    assert not extract_features(o, [[0, 0], [1, 0], [1, 0.5], [0, 0.5]]).candidate
    points = list(o.poses[0].landmarks)
    points[0] = replace(points[0], y=0.5)
    points[1] = replace(points[1], y=0.54)
    corrected = extract_features(replace(o, poses=(Pose(tuple(points)),)), POLYGON)
    assert corrected.torsoAngleDeg == pytest.approx(math.degrees(math.atan2(0.3 * 640, 0.2 * 360)))
    assert corrected.candidate  # Normalized-only angle would be <60 degrees, incorrectly.


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"x": None}, "MISSING_ESSENTIAL_LANDMARK"),
        ({"x": -0.01}, "BODY_CROPPED"),
        ({"visibility": 0.1}, "LOW_LANDMARK_QUALITY"),
    ],
)
def test_missing_partial_or_low_are_ineligible(change, reason):
    o = observation(0)
    points = list(o.poses[0].landmarks)
    points[0] = replace(points[0], **change)
    f = extract_features(replace(o, poses=(Pose(tuple(points)),)), POLYGON)
    assert not f.eligible and reason in f.reasons and f.hipY is None


def test_no_pose_multiple_and_degenerate_geometry():
    o = observation(0)
    for poses in [(), o.poses * 2]:
        assert not extract_features(replace(o, poses=poses, poseCount=len(poses)), POLYGON).eligible
    points = tuple(replace(p, x=0.5, y=0.5) for p in o.poses[0].landmarks)
    assert (
        "DEGENERATE_BODY_GEOMETRY"
        in extract_features(replace(o, poses=(Pose(points),)), POLYGON).reasons
    )


@pytest.mark.parametrize("step", [100, 200, 250, 400, 500])
def test_floor_duration_independent_of_sampling_and_long_episode_single_event(step):
    engine = TemporalEngine()
    events = feed(engine, range(0, 20001, step))
    assert len(events) == 1 and events[0].detectedMs == 2000
    assert events[0].kind == "PERSON_ON_FLOOR" and events[0].validPoseFraction == 1
    assert events[0].analysisFps == pytest.approx(1000 / step)


def test_brief_candidate_and_descent_without_persistent_floor_never_emit():
    e = TemporalEngine()
    assert not feed(e, range(0, 1000, 200), floor=False)
    assert not feed(e, range(1000, 2000, 200))
    assert not feed(e, range(2000, 6000, 200), floor=False)


def test_observed_descent_only_changes_label_after_floor_persistence():
    e = TemporalEngine()
    feed(e, range(0, 1000, 200), floor=False)
    events = feed(e, range(1000, 4000, 200))
    assert len(events) == 1 and events[0].kind == "POSSIBLE_FALL"
    assert events[0].detectedMs == 3000 and events[0].rapidDescentObserved


def test_invalid_breaks_descent_continuity():
    e = TemporalEngine()
    e.step(feature(0, False))
    e.step(feature(200, eligible=False, candidate=False))
    events = feed(e, range(400, 3000, 200))
    assert events[0].kind == "PERSON_ON_FLOOR"


def test_weighted_coverage_and_gap_reset_not_frame_count():
    e = TemporalEngine()
    events = []
    for t in range(0, 2200, 200):
        event = e.step(feature(t, eligible=t != 1000, candidate=t != 1000))
        if event:
            events.append(event)
    assert len(events) == 1 and events[0].validPoseFraction == pytest.approx(0.8)
    e = TemporalEngine()
    assert not feed(e, [0, 400, 800, 1200, 1800, 2000])  # 600 ms hole resets.
    assert not feed(e, range(2200, 3800, 200))
    assert feed(e, [3800])[0].startedMs == 1800
    e = TemporalEngine()
    for t in range(0, 4000, 200):
        assert (
            e.step(feature(t, eligible=(t // 200) % 2 == 0, candidate=(t // 200) % 2 == 0)) is None
        )


def test_contrary_posture_resets_suspected_and_rearm_requires_valid_continuity():
    e = TemporalEngine()
    feed(e, range(0, 1800, 200))
    e.step(feature(1800, False))
    assert not feed(e, range(2000, 4000, 200))
    assert len(feed(e, [4000])) == 1
    feed(e, range(4200, 6200, 200), floor=False)
    e.step(feature(6200, eligible=False, candidate=False))
    assert e.state == "ACTIVE"
    feed(e, range(6400, 9400, 200), floor=False)
    assert e.state == "REARMING"
    e.step(feature(9400, False))
    assert e.closed and e.state == "OBSERVING"
    assert len(feed(e, range(9600, 12000, 200))) == 1


def test_restore_active_and_rearm_reset_and_context_time_guards():
    e = TemporalEngine()
    e.restore({"state": "REARMING"})
    assert not feed(e, range(10000, 20000, 200))
    assert e.state == "ACTIVE"
    with pytest.raises(ValueError, match="NON_MONOTONIC"):
        e.step(feature(1000))
    with pytest.raises(ValueError, match="CONTEXT"):
        e.step(feature(22000, context=("different",)))


def test_quality_dark_frozen_fps_and_frame_timeout_are_media_time_gates():
    gate = QualityGate()
    for t in range(0, 2200, 200):
        o = observation(t, meanLuminance=10.0)
        f = gate.apply(o, extract_features(o, POLYGON))
    assert not f.eligible and "LOW_LIGHT" in f.reasons
    o = observation(2200)
    assert gate.apply(o, extract_features(o, POLYGON)).eligible
    gate = QualityGate()
    for t in range(0, 10200, 200):
        o = observation(t, frameFingerprint="identical")
        f = gate.apply(o, extract_features(o, POLYGON))
    assert "POSSIBLE_FROZEN" in f.reasons
    gate = QualityGate()
    for t in range(0, 6000, 1000):
        o = observation(t)
        f = gate.apply(o, extract_features(o, POLYGON))
    assert "LOW_FPS" in f.reasons
    o = observation(9000)
    assert "FRAME_TIMEOUT" in gate.apply(o, extract_features(o, POLYGON)).reasons


def test_policy_change_requires_new_version_and_no_nan_or_unknowns():
    with pytest.raises(ValueError):
        configured_policy({"floorHoldMs": 1000})
    with pytest.raises(ValueError):
        configured_policy({"minTorsoAngleDeg": math.nan})
    with pytest.raises(TypeError):
        configured_policy({"unknown": 1})
    assert (
        configured_policy({"version": "floor-experiment-1", "floorHoldMs": 2400}).floorHoldMs
        == 2400
    )
