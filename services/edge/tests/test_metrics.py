"""Bounded per-joint failure counts using synthetic observations only."""

from dataclasses import replace

from temporal_support import observation

from radar_edge.metrics import Metrics
from radar_edge.observations import ESSENTIAL, Pose


def test_per_joint_failures_separate_presence_visibility_and_unavailable_coordinates():
    metrics = Metrics(visibility=0.7)
    o = observation(0)
    changes = {
        11: {"visibility": 0.6, "presence": 0.8},
        12: {"visibility": 0.8, "presence": 0.6},
        23: {"x": float("nan"), "presence": float("inf")},
        24: {"x": -0.1},
        25: {"x": None, "visibility": 0.1},
    }
    points = tuple(
        replace(point, **changes.get(point.index, {}))
        for point in o.poses[0].landmarks
        if point.index != 28
    )
    metrics.add(replace(o, poses=(Pose(points),)))
    metrics.add(observation(200))
    diagnostics = metrics.summary()["landmarkDiagnostics"]
    assert diagnostics["minLandmarkVisibility"] == 0.7
    counts = diagnostics["essentialLandmarkFailures"]
    assert set(counts) == {str(index) for index in ESSENTIAL}
    assert counts["11"]["lowVisibility"] == 1
    assert counts["11"]["lowPresence"] == 0
    assert counts["12"]["lowPresence"] == 1
    assert counts["12"]["lowVisibility"] == 0
    assert counts["23"]["nonfinite"] == 1  # Once per point, not once per bad value.
    assert counts["23"]["missing"] == 0
    assert counts["24"]["outOfFrame"] == 1
    assert counts["25"]["missing"] == 1
    assert counts["25"]["lowVisibility"] == 1  # Reasons can coexist.
    assert counts["28"]["missing"] == 1
    assert not any(counts["27"].values())
    assert diagnostics["poseObservations"] == {"none": 0, "one": 2, "multiple": 0}


def test_no_pose_multiple_or_mismatched_counts_do_not_invent_joint_failures():
    metrics = Metrics()
    o = observation(0)
    # Neither detected pose has enough points, but there is no stable person identity to aggregate.
    sparse = Pose(tuple(point for point in o.poses[0].landmarks if point.index == 11))
    metrics.add(replace(o, poses=(), poseCount=0, inferenceState="NO_POSE"))
    metrics.add(replace(o, poses=(sparse, sparse), poseCount=2, inferenceState="MULTIPLE_POSES"))
    metrics.add(replace(o, poses=(sparse,), poseCount=2))
    diagnostics = metrics.summary()["landmarkDiagnostics"]
    assert diagnostics["scope"] == "SINGLE_POSE_ONLY"
    assert diagnostics["poseObservations"] == {"none": 1, "one": 1, "multiple": 1}
    assert diagnostics["poseCountMismatchObservations"] == 1
    assert all(
        not any(counts.values()) for counts in diagnostics["essentialLandmarkFailures"].values()
    )


def test_diagnostic_size_stays_constant_with_repeated_failures_and_never_keeps_coordinates():
    metrics = Metrics()
    o = observation(0)
    points = tuple(replace(point, presence=0.2) for point in o.poses[0].landmarks)
    for index in range(100):
        metrics.add(replace(o, timestampMs=index * 200, poses=(Pose(points),)))
    diagnostics = metrics.summary()["landmarkDiagnostics"]
    assert len(diagnostics["essentialLandmarkFailures"]) == 8
    for counts in diagnostics["essentialLandmarkFailures"].values():
        assert counts == {
            "missing": 0,
            "nonfinite": 0,
            "outOfFrame": 0,
            "lowVisibility": 0,
            "lowPresence": 100,
        }
    assert not hasattr(metrics, "observations")
