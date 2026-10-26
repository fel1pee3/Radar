"""Fresh-image quarter turns: geometry, quality, ambiguity and bounded work."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from test_posture_candidate import rtmo_observation

from radar_edge.rtmo import RtmoEstimator


@pytest.mark.parametrize("clockwise", [True, False])
def test_quarter_turn_restores_pixel_locations_and_body_labels(monkeypatch, clockwise):
    model = RtmoEstimator("not-opened", recovery="RTMO_ADAPTIVE_V3")
    w, h, x, y = 640, 360, 127, 249
    native = rtmo_observation(0).poses[0]
    qx, qy = ((h - 1 - y) / h, x / w) if clockwise else (y / h, (w - 1 - x) / w)
    turned = replace(native, landmarks=tuple(replace(p, x=qx, y=qy) for p in native.landmarks))
    shapes = []

    def infer(image):
        shapes.append(image.shape)
        return (turned,), ((qx, qy, qx, qy, 0.9),), 0.9

    monkeypatch.setattr(model, "infer_image", infer)
    poses, boxes, score = model.quarter_turn(np.zeros((h, w, 3), np.uint8), clockwise)
    assert shapes == [(w, h, 3)]
    assert score == 0.9 and boxes[0][:4] == pytest.approx((x / w, y / h, x / w, y / h))
    for original, restored in zip(native.landmarks, poses[0].landmarks, strict=True):
        assert restored.x == pytest.approx(x / w) and restored.y == pytest.approx(y / h)
        assert restored.index == original.index and restored.confidence == original.confidence
        assert restored.visibility is None and restored.presence is None


@pytest.mark.parametrize(
    "case", ["no_proposal", "vertical", "good_pose", "multiple", "weak_proposal"]
)
def test_no_quarter_turn_without_current_horizontal_failed_detection(monkeypatch, case):
    model = RtmoEstimator("not-opened", recovery="RTMO_ADAPTIVE_V3")
    native = rtmo_observation(0).poses[0]
    calls = []

    def infer(image):
        calls.append(image.shape)
        model.proposal = None if case == "no_proposal" else np.array([10, 10, 40, 300])
        if case == "weak_proposal":
            model.proposal = np.array([10, 100, 600, 200])
        model.proposal_essential = 7 if case == "weak_proposal" else 8
        return (
            (
                (native,) * (2 if case == "multiple" else 1)
                if case in {"good_pose", "multiple"}
                else ()
            ),
            (),
            0.9,
        )

    monkeypatch.setattr(model, "infer_image", infer)
    model.estimate(SimpleNamespace(timestamp_ms=10, bgr=np.zeros((360, 640, 3), np.uint8)))
    assert not set(model.perception_passes) & {"ROTATE_90", "ROTATE_270"}
    assert len(calls) <= 4


def test_failed_turns_fall_back_without_accepting_partial_pose_or_stale_points(monkeypatch):
    model = RtmoEstimator("not-opened", recovery="RTMO_ADAPTIVE_V3")
    partial = replace(rtmo_observation(0).poses[0], landmarks=())
    calls = []

    def infer(image):
        calls.append(image.shape)
        model.proposal = np.array([100, 160, 500, 250])
        model.proposal_essential = 8
        return ((partial,) if len(calls) in {3, 4} else ()), (), 0.8

    monkeypatch.setattr(model, "infer_image", infer)
    frame = SimpleNamespace(timestamp_ms=0, bgr=np.zeros((360, 640, 3), np.uint8))
    poses, _ = model.estimate(frame)
    assert not poses
    assert model.perception_passes == (
        "ORIGINAL",
        "PERSON_PROPOSAL_CROP",
        "ROTATE_270",
        "ROTATE_90",
        "ROTATE_180",
        "CENTER_80",
    )
    assert len(calls) == 6
    model.estimate(SimpleNamespace(timestamp_ms=200, bgr=frame.bgr))
    assert len(calls) == 12  # All attempts are fresh; no previous successful body is replayed.


def test_multiple_people_in_recovery_are_preserved(monkeypatch):
    model = RtmoEstimator("not-opened", recovery="RTMO_ADAPTIVE_V3")
    native = rtmo_observation(0).poses[0]
    calls = []

    def infer(image):
        calls.append(1)
        model.proposal = np.array([100, 160, 500, 250])
        model.proposal_essential = 8
        return ((native, native) if len(calls) == 3 else ()), (), 0.9

    monkeypatch.setattr(model, "infer_image", infer)
    poses, _ = model.estimate(
        SimpleNamespace(timestamp_ms=0, bgr=np.zeros((360, 640, 3), np.uint8))
    )
    assert len(poses) == 2 and len(calls) == 3
