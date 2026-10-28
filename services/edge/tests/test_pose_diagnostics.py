"""Offline diagnostics: partial human labels never loosen native event requirements."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from temporal_support import calibration, config, observation

from radar_edge.policy import Policy
from radar_edge.pose_audit import (
    GROUPS,
    assess_anatomy,
    localization_assessment,
    native_shadow_readiness,
)
from radar_edge.posture_multiclass import MulticlassClassifier

ROOT = Path(__file__).resolve().parents[3]


def script(name):
    spec = importlib.util.spec_from_file_location(
        "radar_test_" + name.replace("-", "_"), ROOT / "scripts/validation" / name
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def points():
    return {
        p.index: [p.x, p.y, 0.9]
        for p in observation(0).poses[0].landmarks
        if p.index in (11, 12, 23, 24, 25, 26, 27, 28)
    }


def reference():
    return {
        "box": [0, 0, 1, 1],
        "count": [1, 1],
        "jointGroups": {
            group: {"visiblePoints": [[0.9, 0.7]] if group == "ankle" else []} for group in GROUPS
        },
    }


def v3_classifier():
    classifier = object.__new__(MulticlassClassifier)
    classifier.artifact = SimpleNamespace(
        version="synthetic-test",
        qualityThreshold=0.5,
        decisionThreshold=0.65,
        marginThreshold=0.15,
    )
    classifier.settings = SimpleNamespace(
        method="MULTICLASS_BODY_V3", excludedRegions=[], supportRegions=[]
    )
    classifier.geometry = {"width": 640, "height": 360, "rotation": 0}
    classifier._floor = calibration()["floorPolygon"]
    classifier.scores = lambda vector: np.array([0.01, 0.01, 0.01, 0.97])
    return classifier


def shadow(current, ref=None):
    module = script("audit-pose-reference.py")
    cfg = config().model_copy(
        update={"posture": config().posture.model_copy(update={"method": "MULTICLASS_BODY_V3"})}
    )
    cal = {**calibration(), "geometry": {"rotation": 0}}
    return module.classify_shadow(
        current,
        {"width": 640, "height": 360, "frameIndex": 0, "timestampMs": 0, "meanLuminance": 100},
        reference() if ref is None else ref,
        cfg,
        v3_classifier(),
        Policy(version="floor-rtmo-score-test", qualitySource="RTMO_KEYPOINT_SCORE"),
        cal,
        5.0,
    )


def test_full_prediction_can_be_probed_without_any_human_joint_coordinates():
    result = shadow(points(), {"box": None, "jointGroups": {}})
    assert result is not None and result["posture"] == "LYING"
    assert result["legacyClassifierScored"]
    assert result["requiresCompleteHumanReference"] is False
    assert result["eventsAuthorized"] is False
    assert result["wholeBodyAnatomyValidated"] is False


def test_v3_partial_diagnostic_never_promotes_incomplete_lying_to_event_evidence():
    current = {key: value for key, value in points().items() if key in (11, 12, 23, 25)}
    result = shadow(current)
    assert result is not None and result["posture"] == "LYING"
    assert result["legacyPartialDescriptorUsed"]
    assert "FLOOR_BODY_EVIDENCE_INCOMPLETE" in result["reasons"]
    assert not result["legacyCandidate"] and not result["eligible"]
    assert result["eventsAuthorized"] is False


@pytest.mark.parametrize("keys", [(11, 12, 23), (11, 12, 25, 27)])
def test_missing_native_descriptor_requirements_block_probe_even_with_human_labels(keys):
    current = {key: value for key, value in points().items() if key in keys}
    full_human = reference()
    for group in GROUPS:
        full_human["jointGroups"][group]["visiblePoints"] = [[0.2, 0.7], [0.3, 0.7]]
    assert shadow(current, full_human) is None


def test_native_scores_are_not_clipped_rescaled_or_renamed_as_visibility():
    current = points()
    original = copy.deepcopy(current)
    result = shadow(current)
    assert current == original and result["nativeScoresPreserved"]
    assert result["readiness"]["nativeQualitySource"] == "RTMPOSE_SIMCC_SCORE"
    assert result["readiness"]["nativeScoreCalibrationValidated"] is False
    assert result["nativeScoreProjection"].startswith("UNVALIDATED")


def test_low_native_quality_and_out_of_frame_are_not_repaired_by_human_reference():
    current = points()
    for key in (11, 12):
        current[key][2] = 0.49
    current[23][0] = -0.1
    readiness = native_shadow_readiness(current)
    assert not readiness["descriptorCandidateForV3"]
    assert shadow(current) is None


def test_single_observable_ankle_measures_one_point_without_claiming_full_body():
    assessment = assess_anatomy(points(), reference(), 640, 360)
    assert assessment["observablePoints"] == 1
    assert assessment["pck"] == 1
    assert not assessment["qualifiedVisibleSubset"]
    assert assessment["wholeEssentialPoseVerified"] is False


def test_box_assessment_preserves_duplicate_and_false_boxes_without_fusion():
    current = np.array([[0, 0, 60, 60], [1, 1, 59, 59], [75, 75, 90, 90]], dtype=float)
    original = current.copy()
    result = localization_assessment(current, {"box": [0, 0, 0.6, 0.6], "count": [1, 1]}, 100, 100)
    assert result["duplicatePrimaryMatches"] == 1 and result["unmatchedBoxes"] == 1
    assert result["outputBoxes"] == 3 and np.array_equal(current, original)
    empty = localization_assessment(current, {"box": None, "count": [0, 0]}, 100, 100)
    assert empty["knownEmptyFalseBoxes"] == 3


def test_cached_reference_identity_must_match_before_any_reassessment(tmp_path):
    module = script("reassess-pose-cache.py")
    ref = tmp_path / "current.json"
    old = tmp_path / "cached-ref.json"
    cache = tmp_path / "cache.json"
    ref.write_text("{}", encoding="utf-8")
    old.write_text("{}", encoding="utf-8")
    cache.write_text(json.dumps({"referenceSha256": "wrong"}), encoding="utf-8")
    with pytest.raises(ValueError, match="reference identity"):
        module.reassess(ref, cache, old, ".local/no-inference")


def test_cached_geometry_change_is_rejected_even_when_image_path_is_unchanged(
    tmp_path, monkeypatch
):
    module = script("reassess-pose-cache.py")
    monkeypatch.chdir(tmp_path)
    image = np.zeros((4, 4, 3), np.uint8)
    cv2.imwrite("source.png", image)
    frame = {
        "frameSha256": hashlib.sha256(image.tobytes()).hexdigest(),
        "timestampMs": 0,
        "width": 4,
        "height": 4,
        "videoSha256": "synthetic-video",
        "imagePath": "source.png",
    }
    old = {"annotations": {"F": {"frame": frame}}}
    new = {"annotations": {"F": {"frame": {**frame, "width": 5}}}}
    Path("old.json").write_text(json.dumps(old), encoding="utf-8")
    Path("current.json").write_text(json.dumps(new), encoding="utf-8")
    cache = {
        "referenceSha256": hashlib.sha256(Path("old.json").read_bytes()).hexdigest(),
        "models": {
            "detector": "ceb11c07298f95c50d7c5abeb906d03340c85f23aa79e3e66966e7fb6c307250",
            "pose": "9aeb635b83f86aea45cf45d85798f7eba1a162de8e0d721c44e54fe5eebaf47d",
        },
    }
    Path("cache.json").write_text(json.dumps(cache), encoding="utf-8")
    with pytest.raises(ValueError, match="identity or geometry"):
        module.reassess(Path("current.json"), Path("cache.json"), Path("old.json"), ".local/test")
