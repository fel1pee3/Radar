"""Synthetic inverse-transform test; never loads a model or opens capture."""

import importlib.util
from pathlib import Path

import pytest

from radar_edge.observations import Landmark, Pose


@pytest.mark.parametrize("width", [640, 359])
def test_mirror_inverse_preserves_pixel_centers_and_anatomy_as_an_involution(width):
    filename = Path(__file__).resolve().parents[3] / "scripts/validation/probe-rtmo-mirror.py"
    spec = importlib.util.spec_from_file_location("radar_mirror_probe_test", filename)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    indices = sorted(probe.MIRROR_BODY_INDEX)
    points = tuple(
        Landmark(
            index, (number * 7) / width, 0.1 + number * 0.03, None, None, None, 0.51 + number * 0.02
        )
        for number, index in enumerate(indices)
    )
    poses = (Pose(points, "RTMO_KEYPOINT_SCORE"),)
    boxes = ((0.1, 0.2, 0.8, 0.9, 0.83),)
    once, boxes_once = probe.restore_mirror(poses, boxes, width)
    by_index = {point.index: point for point in once[0].landmarks}
    for point in points:
        restored = by_index[probe.MIRROR_BODY_INDEX[point.index]]
        assert restored.x == pytest.approx((width - 1 - point.x * width) / width)
        assert restored.y == point.y and restored.confidence == point.confidence
        assert restored.visibility is None and restored.presence is None
    twice, boxes_twice = probe.restore_mirror(once, boxes_once, width)
    assert twice[0].qualitySource == poses[0].qualitySource
    for original, restored in zip(points, twice[0].landmarks, strict=True):
        assert restored.index == original.index
        assert restored.x == pytest.approx(original.x)
        assert restored.y == original.y and restored.confidence == original.confidence
    assert boxes_once[0][0] == pytest.approx((width - 1) / width - 0.8)
    assert boxes_once[0][2] == pytest.approx((width - 1) / width - 0.1)
    assert boxes_twice[0] == pytest.approx(boxes[0])
