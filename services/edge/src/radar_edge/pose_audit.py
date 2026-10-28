"""Offline geometry and RGB preparation; reference boxes never enter the product."""

from itertools import permutations
from math import hypot

import cv2
import numpy as np

GROUPS = {"shoulder": (11, 12), "hip": (23, 24), "knee": (25, 26), "ankle": (27, 28)}


def pose_input_from_bgr(image):
    """The pinned RTMPose deployment says Normalize(to_rgb=True); YOLOX stays BGR."""
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected uint8 BGR pixels")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def rotated_image(image, degrees):
    if degrees == 0:
        return image
    values = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    if degrees not in values:
        raise ValueError("Use only 0,90,180,270 degrees")
    return cv2.rotate(image, values[degrees])


def restore_point(x, y, width, height, degrees):
    """Pixel-center mapping. Anatomical array order and scores are unchanged."""
    if degrees == 0:
        return x, y
    if degrees == 90:
        return y, height - 1 - x
    if degrees == 180:
        return width - 1 - x, height - 1 - y
    if degrees == 270:
        return width - 1 - y, x
    raise ValueError("Invalid canonical orientation")


def rotate_box(box, width, height, degrees):
    """Continuous box edges differ from pixel centers by the deliberate minus-one."""
    x1, y1, x2, y2 = box
    if degrees == 0:
        return [x1, y1, x2, y2]
    if degrees == 90:
        return [height - y2, x1, height - y1, x2]
    if degrees == 180:
        return [width - x2, height - y2, width - x1, height - y1]
    if degrees == 270:
        return [y1, width - x2, y2, width - x1]
    raise ValueError("Invalid canonical orientation")


def restore_box(box, width, height, degrees):
    return rotate_box(
        box,
        height if degrees in (90, 270) else width,
        width if degrees in (90, 270) else height,
        (360 - degrees) % 360,
    )


def box_iou(a, b):
    lo = np.maximum(a[:2], b[:2])
    hi = np.minimum(a[2:], b[2:])
    intersection = float(np.prod(np.maximum(0, hi - lo)))
    union = (
        float(np.prod(np.maximum(0, np.array(a[2:]) - a[:2])))
        + float(np.prod(np.maximum(0, np.array(b[2:]) - b[:2])))
        - intersection
    )
    return intersection / union if union > 0 else 0.0


def assess_anatomy(points, reference, width, height):
    """Compare observable anatomy, not score counts; unknown sides are not invented."""
    if reference["box"] is None:
        return {
            "observablePoints": 0,
            "pck": None,
            "qualifiedVisibleSubset": False,
            "wholeEssentialPoseVerified": False,
            "details": [],
        }
    x1, y1, x2, y2 = reference["box"]
    tolerance = max(8, 0.05 * hypot((x2 - x1) * width, (y2 - y1) * height))
    details = []
    for group, indices in GROUPS.items():
        expected = reference["jointGroups"][group]["visiblePoints"]
        predicted = [(i, points.get(i, points.get(str(i)))) for i in indices]
        predicted = [(i, p) for i, p in predicted if p is not None and np.isfinite(p[:2]).all()]
        if not expected:
            continue
        # At most two joints in each group: choose a bijection, never reuse a point.
        alternatives = []
        for chosen in permutations(predicted, min(len(expected), len(predicted))):
            distances = [
                hypot((p[0] - e[0]) * width, (p[1] - e[1]) * height)
                for (_, p), e in zip(chosen, expected, strict=False)
            ]
            alternatives.append((sum(distances), chosen, distances))
        chosen, distances = (
            ((), []) if not alternatives else min(alternatives, key=lambda x: x[0])[1:]
        )
        for index, expected_point in enumerate(expected):
            distance = distances[index] if index < len(distances) else None
            details.append(
                {
                    "group": group,
                    "reference": expected_point,
                    "matchedIndex": chosen[index][0] if index < len(chosen) else None,
                    "distancePixels": distance,
                    "correct": distance is not None and distance <= tolerance,
                }
            )
    correct = sum(d["correct"] for d in details)
    groups = {d["group"] for d in details}
    return {
        "observablePoints": len(details),
        "correctPoints": correct,
        "pck": correct / len(details) if details else None,
        "tolerancePixels": tolerance,
        "qualifiedVisibleSubset": bool(details) and correct == len(details) and len(groups) == 4,
        "wholeEssentialPoseVerified": False,
        "qualificationLimit": "Hidden anatomy and anatomical laterality unverified",
        "details": details,
    }


ESSENTIAL_DIAGNOSTIC = (11, 12, 23, 24, 25, 26, 27, 28)


def native_shadow_readiness(points):
    """Legacy numeric mask only; SimCC scores remain uncalibrated native values.

    Human labels measure error; missing labels never change this mask.
    This does not authorize a detector event or certify visible anatomy.
    """
    details = []
    for index in ESSENTIAL_DIAGNOSTIC:
        p = points.get(index, points.get(str(index)))
        present = p is not None and len(p) >= 3
        finite = present and bool(np.isfinite(p[:3]).all())
        in_frame = finite and 0 <= p[0] <= 1 and 0 <= p[1] <= 1
        score_pass = finite and 0.5 <= p[2] <= 1
        details.append(
            {
                "index": index,
                "present": present,
                "finite": finite,
                "inFrame": bool(in_frame),
                "nativeScore": float(p[2]) if finite else None,
                "passesLegacyNumericMask": bool(in_frame and score_pass),
            }
        )
    count = sum(p["passesLegacyNumericMask"] for p in details)
    return {
        "nativeQualitySource": "RTMPOSE_SIMCC_SCORE",
        "nativeScoreCalibrationValidated": False,
        "legacyNumericProjectionOnly": True,
        "essentialMaskPassed": count,
        "essentialMaskRequired": 8,
        "readyForLegacyShadow": count == 8,
        "validTorsoPoints": sum(
            p["passesLegacyNumericMask"] and p["index"] in (11, 12, 23, 24) for p in details
        ),
        "descriptorCandidateForV3": count >= 4
        and sum(p["passesLegacyNumericMask"] and p["index"] in (11, 12, 23, 24) for p in details)
        >= 3,
        "humanReferenceRequired": False,
        "details": details,
    }


def localization_assessment(boxes, reference, width, height):
    """Assess, never select or merge, automatic detections against a body box."""
    current = [list(map(float, box)) for box in boxes]
    expected = reference["count"]
    if reference["box"] is None:
        return {
            "outputBoxes": len(current),
            "primaryLocated": False,
            "matchedBoxes": 0,
            "duplicatePrimaryMatches": 0,
            "unmatchedBoxes": len(current),
            "knownEmptyFalseBoxes": len(current) if expected == [0, 0] else None,
            "referenceIoUs": [],
            "assessmentOnly": True,
        }
    target = np.array(reference["box"]) * [width, height, width, height]
    overlaps = [box_iou(box, target) for box in current]
    matches = sum(iou >= 0.5 for iou in overlaps)
    return {
        "outputBoxes": len(current),
        "primaryLocated": matches > 0,
        "matchedBoxes": matches,
        "duplicatePrimaryMatches": max(0, matches - 1),
        "unmatchedBoxes": len(current) - matches,
        "knownEmptyFalseBoxes": None,
        "referenceIoUs": overlaps,
        "ambiguousAdditionalPeople": expected[1] > expected[0],
        "assessmentOnly": True,
    }
