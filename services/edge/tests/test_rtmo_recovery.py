"""Coordinate/ambiguity risks; synthetic outputs, no physical perception claim."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from test_posture_candidate import rtmo_observation

from radar_edge.errors import EdgeError
from radar_edge.rtmo import RtmoEstimator


def test_inverted_pass_restores_original_coordinates_scores_and_timestamp(monkeypatch):
    model = RtmoEstimator(".local/not-opened.onnx", recovery="RTMO_ADAPTIVE_V1")
    pose = rtmo_observation(0).poses[0]
    native = replace(pose, landmarks=tuple(replace(p, x=0.25, y=0.4) for p in pose.landmarks))
    responses = iter([((), (), 0.6), ((native,), ((0.1, 0.2, 0.6, 0.7, 0.9),), 0.9)])
    monkeypatch.setattr(model, "infer_image", lambda image: next(responses))
    frame = SimpleNamespace(timestamp_ms=1234, bgr=np.zeros((360, 640, 3), np.uint8))
    poses, duration = model.estimate(frame)
    p = poses[0].landmarks[0]
    assert p.x == pytest.approx(639 / 640 - 0.25) and p.y == pytest.approx(359 / 360 - 0.4)
    assert p.confidence == native.landmarks[0].confidence and p.visibility is None
    assert model.perception_passes == ("ORIGINAL", "ROTATE_180") and duration >= 0
    with pytest.raises(EdgeError, match="Timestamps"):
        model.estimate(frame)


def test_person_crop_restores_absolute_coordinates_with_padding(monkeypatch):
    model = RtmoEstimator(".local/not-opened.onnx", recovery="RTMO_ADAPTIVE_V2")
    pose = rtmo_observation(0).poses[0]
    native = replace(pose, landmarks=tuple(replace(p, x=0.5, y=0.5) for p in pose.landmarks))
    monkeypatch.setattr(
        model, "infer_image", lambda image: ((native,), ((0.1, 0.2, 0.8, 0.9, 0.85),), 0.85)
    )
    poses, boxes, score = model.proposal_crop(
        np.zeros((400, 600, 3), np.uint8), (200, 100, 400, 300)
    )
    assert poses[0].landmarks[0].x == 0.5 and poses[0].landmarks[0].y == 0.5
    assert boxes[0][0] == pytest.approx(180 / 600) and score == 0.85


def test_multiple_people_are_never_replaced_by_one_crop(monkeypatch):
    model = RtmoEstimator(".local/not-opened.onnx", recovery="RTMO_ADAPTIVE_V2")
    pose = rtmo_observation(0).poses[0]
    calls = []

    def infer(image):
        calls.append(1)
        model.proposal = np.array([20, 20, 100, 200])
        return (pose, pose), ((0, 0, 0.5, 1, 0.9), (0, 0, 0.5, 1, 0.9)), 0.9

    monkeypatch.setattr(model, "infer_image", infer)
    poses, _ = model.estimate(
        SimpleNamespace(timestamp_ms=0, bgr=np.zeros((360, 640, 3), np.uint8))
    )
    assert len(poses) == 2 and len(calls) == 1
