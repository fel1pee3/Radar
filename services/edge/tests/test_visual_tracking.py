"""Known image motion and missing-pose boundaries; no model, camera, HTTP or GPU."""

import json
from dataclasses import asdict, replace

import cv2
import numpy as np
import pytest
from temporal_support import observation

from radar_edge.observations import Landmark, Pose
from radar_edge.source import Frame, Geometry
from radar_edge.visual_tracking import VisualTracker

GEOMETRY = Geometry(320, 240, 320, 240, 320, 240, 0)


def texture():
    return np.random.default_rng(731).integers(0, 256, (240, 320, 3), dtype=np.uint8)


def sample(image, index, timestamp):
    return Frame(index, timestamp, "MEDIA_PTS", image, GEOMETRY)


def anchor(frame, x=130.0, y=100.0, confidence=0.9):
    point = Landmark(11, x / 319, y / 239, None, None, None, confidence)
    return observation(
        frame.timestamp_ms,
        frameIndex=frame.index,
        width=320,
        height=240,
        runId="synthetic-visual-run",
        modelId="rtmo-s-test",
        poses=(Pose((point,), "RTMO_KEYPOINT_SCORE"),),
    )


def test_flow_follows_known_pixels_without_changing_raw_observations():
    image = texture()
    first = sample(image, 0, 0)
    raw = anchor(first)
    before = json.dumps(asdict(raw), sort_keys=True)
    tracker = VisualTracker()
    a = tracker.update(first, raw)
    assert a.kinds == {11: "MODEL"}
    moved = cv2.warpAffine(image, np.float32([[1, 0, 5], [0, 1, 3]]), (320, 240))
    b = tracker.update(sample(moved, 1, 33))
    assert b.points[11] == pytest.approx((135, 103), abs=0.15)
    assert b.kinds[11] == "FLOW" and b.age_ms == 33
    assert json.dumps(asdict(raw), sort_keys=True) == before
    assert not hasattr(b, "confidence") and not hasattr(b, "visibility")


@pytest.mark.parametrize("reason", ["missing", "confidence", "multiple", "outOfFrame"])
def test_current_rejected_model_point_disappears_immediately(reason):
    image = texture()
    tracker = VisualTracker()
    tracker.update(sample(image, 0, 0), anchor(sample(image, 0, 0)))
    frame = sample(image, 1, 33)
    raw = anchor(frame)
    if reason == "missing":
        raw = replace(raw, poses=(), poseCount=0)
    elif reason == "multiple":
        raw = replace(raw, poses=raw.poses * 2, poseCount=2)
    elif reason == "confidence":
        raw = anchor(frame, confidence=0.1)
    else:
        raw = anchor(frame, x=-1)
    assert not tracker.update(frame, raw).points
    assert not tracker.update(sample(image, 2, 66)).points


def test_expiry_blank_image_source_and_clock_change_do_not_keep_old_points():
    image = texture()
    tracker = VisualTracker(max_age_ms=100)
    frame = sample(image, 0, 0)
    tracker.update(frame, anchor(frame))
    assert not tracker.update(sample(image, 1, 101)).points
    tracker.update(frame, anchor(frame))
    assert not tracker.update(sample(np.zeros_like(image), 1, 33)).points
    tracker.update(frame, anchor(frame))
    assert not tracker.update(sample(image, 1, -1)).points
    # A new source is re-anchored to the new raw position, without previous smoothing.
    frame = sample(image, 2, 40)
    other = replace(anchor(frame, x=134), runId="another-run")
    assert tracker.update(frame, other).points[11] == pytest.approx((134, 100))


def test_anchor_adjustment_is_bounded_and_large_disagreement_uses_current_model():
    image = texture()
    tracker = VisualTracker()
    first = sample(image, 0, 0)
    tracker.update(first, anchor(first))
    second = sample(image, 1, 33)
    value = tracker.update(second, anchor(second, x=136))
    assert abs(value.points[11][0] - 136) <= 4
    third = sample(image, 2, 66)
    value = tracker.update(third, anchor(third, x=170))
    assert value.points[11] == pytest.approx((170, 100))
    assert value.kinds[11] == "MODEL"


def test_bad_anchor_and_geometry_change_cannot_attach_pose_to_wrong_frame():
    image = texture()
    frame = sample(image, 0, 0)
    tracker = VisualTracker()
    with pytest.raises(ValueError, match="original frame"):
        tracker.update(frame, replace(anchor(frame), frameIndex=1))
    tracker.update(frame, anchor(frame))
    other = replace(sample(image, 1, 33), geometry=replace(GEOMETRY, rotation=90))
    assert not tracker.update(other).points
