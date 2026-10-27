"""Color and coordinate contracts for offline perception diagnosis, not accuracy proof."""

import cv2
import numpy as np
import pytest

from radar_edge.pose_audit import (
    GROUPS,
    assess_anatomy,
    pose_input_from_bgr,
    restore_box,
    restore_point,
    rotated_image,
)


def test_pose_color_follows_rgb_deployment_without_changing_detector_pixels():
    bgr = np.full((4, 6, 3), (10, 70, 210), dtype=np.uint8)
    expected = bgr.copy()
    rgb = pose_input_from_bgr(bgr)
    assert np.array_equal(bgr, expected)
    assert tuple(rgb[2, 3]) == (210, 70, 10)
    normalized = (rgb[2, 3] - np.array([123.675, 116.28, 103.53])) / np.array(
        [58.395, 57.12, 57.375]
    )
    assert normalized[0] > 0 and normalized[2] < 0
    assert rgb.flags.c_contiguous


@pytest.mark.parametrize("angle", [0, 90, 180, 270])
def test_point_restoration_matches_actual_cv2_pixels(angle):
    image = np.zeros((5, 9, 3), np.uint8)
    image[1, 6] = (20, 100, 220)
    rotated = rotated_image(image, angle)
    ys, xs = np.where(np.all(rotated == (20, 100, 220), axis=2))
    assert len(xs) == 1
    assert restore_point(int(xs[0]), int(ys[0]), 9, 5, angle) == (6, 1)


@pytest.mark.parametrize("angle", [0, 90, 180, 270])
def test_box_edges_restore_an_actual_rotated_mask(angle):
    image = np.zeros((5, 9), np.uint8)
    image[1:4, 2:8] = 255
    if angle:
        choices = {
            90: cv2.ROTATE_90_CLOCKWISE,
            180: cv2.ROTATE_180,
            270: cv2.ROTATE_90_COUNTERCLOCKWISE,
        }
        image = cv2.rotate(image, choices[angle])
    y, x = np.where(image)
    observed = [int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1]
    assert restore_box(observed, 9, 5, angle) == [2, 1, 8, 4]


def reference():
    return {
        "box": [0, 0, 1, 1],
        "jointGroups": {group: {"visiblePoints": [[0.2, 0.3], [0.8, 0.3]]} for group in GROUPS},
    }


def test_high_native_scores_cannot_replace_anatomical_correspondence():
    points = {i: [0.9, 0.9, 1.0] for pair in GROUPS.values() for i in pair}
    result = assess_anatomy(points, reference(), 640, 360)
    assert result["pck"] == 0 and not result["qualifiedVisibleSubset"]


def test_hidden_reference_joints_are_not_filled_or_certified():
    ref = reference()
    ref["jointGroups"]["hip"]["visiblePoints"] = []
    points = {
        i: [0.2 if k == 0 else 0.8, 0.3, 0.9]
        for pair in GROUPS.values()
        for k, i in enumerate(pair)
    }
    result = assess_anatomy(points, ref, 640, 360)
    assert result["observablePoints"] == 6
    assert result["pck"] == 1
    assert not result["qualifiedVisibleSubset"]
    assert not result["wholeEssentialPoseVerified"]


def test_laterality_ambiguity_uses_a_bijection_not_one_point_twice():
    ref = reference()
    points = {i: [0.2, 0.3, 0.9] for pair in GROUPS.values() for i in pair}
    result = assess_anatomy(points, ref, 640, 360)
    assert result["correctPoints"] == 4 and result["pck"] == 0.5
