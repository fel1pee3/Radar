"""Backend boundaries: no fabricated visibility, ambiguity or temporal bypass."""

import hashlib
import io
import zipfile
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from pydantic import ValidationError
from temporal_support import GEOMETRY, POLYGON, calibration, config, observation

from radar_edge.config import EdgeConfig
from radar_edge.engine import TemporalEngine
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime, event_payload
from radar_edge.features import extract_features
from radar_edge.model import get_model_spec
from radar_edge.observations import Pose, point_confidence, pose_quality
from radar_edge.policy import DEFAULT_POLICY, configured_policy
from radar_edge.preview import usable_point
from radar_edge.rtmo import COCO_TO_BODY, RtmoEstimator, decode_outputs

POLICY = configured_policy(
    {"version": "floor-rtmo-score-v0.1", "qualitySource": "RTMO_KEYPOINT_SCORE"}
)


def rtmo_observation(t):
    original = observation(t)
    points = tuple(
        replace(p, visibility=None, presence=None, confidence=0.99)
        for p in original.poses[0].landmarks
        if p.index in COCO_TO_BODY.values()
    )
    return replace(
        original,
        modelId=get_model_spec("rtmo-s").model_id,
        poses=(Pose(points, "RTMO_KEYPOINT_SCORE"),),
    )


def outputs(boxes):
    detections = np.array([boxes], dtype=np.float32).reshape(1, len(boxes), 5)
    keypoints = np.zeros((1, len(boxes), 17, 3), dtype=np.float32)
    keypoints[..., 0] = 100
    keypoints[..., 1] = 50
    keypoints[..., 2] = 0.9
    return [detections, keypoints]


def test_coco_mapping_excludes_face_and_does_not_invent_presence_or_depth():
    result = outputs([[10, 10, 110, 210, 0.9]])
    result[1][0, 0, 11, :2] = [200, 300]
    poses = decode_outputs(result, 2, 320, 240)
    assert len(poses) == 1
    assert {p.index for p in poses[0].landmarks} == set(COCO_TO_BODY.values())
    hip = next(p for p in poses[0].landmarks if p.index == 23)
    assert hip.x == pytest.approx(0.3125) and hip.y == pytest.approx(0.625)
    assert hip.visibility is None and hip.presence is None and hip.z is None
    assert hip.confidence == pytest.approx(0.9)


def test_nms_removes_duplicate_boxes_but_preserves_two_people():
    poses = decode_outputs(
        outputs([[0, 0, 100, 200, 0.95], [1, 1, 101, 201, 0.9], [300, 0, 400, 200, 0.85]]),
        1,
        640,
        360,
    )
    assert len(poses) == 2
    assert pose_quality(poses, 0.5)[0] == "MULTIPLE_POSES"
    assert not decode_outputs(outputs([[0, 0, 100, 200, 0.1]]), 1, 640, 360)
    assert not decode_outputs(outputs([]), 1, 640, 360)


def test_invalid_native_output_is_not_reported_as_no_pose():
    invalid = outputs([[0, 0, 100, 200, 0.9]])
    invalid[1][0, 0, 15, 2] = np.nan
    with pytest.raises(ValueError):
        decode_outputs(invalid, 1, 640, 360)
    with pytest.raises(ValueError):
        decode_outputs(invalid[:1], 1, 640, 360)
    estimator = RtmoEstimator(".local/unused.onnx")
    estimator.session = object()
    with pytest.raises(EdgeError) as caught:
        from radar_edge.source import Frame

        estimator.estimate(Frame(0, 0, "MEDIA_PTS", np.zeros((360, 640, 3), np.uint8), GEOMETRY))
    assert caught.value.code == "MODEL_INFERENCE_ERROR"


def test_score_quality_is_explicit_and_cannot_pass_a_mediapipe_policy():
    o = rtmo_observation(0)
    assert pose_quality(o.poses, 0.5) == ("ONE_VALID_POSE", ())
    assert extract_features(o, POLYGON, POLICY).candidate
    assert "QUALITY_POLICY_MISMATCH" in extract_features(o, POLYGON).reasons
    point = o.poses[0].landmarks[0]
    assert not usable_point(point, 0.5)
    assert usable_point(point, 0.5, "RTMO_KEYPOINT_SCORE")
    assert point_confidence(replace(point, presence=0.99), "RTMO_KEYPOINT_SCORE") is None
    assert point_confidence(point, "UNKNOWN") is None
    bad = replace(
        o,
        poses=(
            replace(
                o.poses[0],
                landmarks=tuple(
                    replace(p, confidence=0.1) if p.index == 28 else p for p in o.poses[0].landmarks
                ),
            ),
        ),
    )
    assert not extract_features(bad, POLYGON, POLICY).eligible


def test_temporal_persistence_and_score_payload_keep_contract_semantics():
    engine = TemporalEngine(POLICY)
    emissions = []
    for t in range(0, 2600, 200):
        o = rtmo_observation(t)
        f = extract_features(o, POLYGON, POLICY)
        if emission := engine.step(f):
            emissions.append((o, f, emission))
    assert len(emissions) == 1 and emissions[0][2].detectedMs == 2000
    o, f, emission = emissions[0]
    payload = event_payload(
        o, f, emission, {"anchor": "2026-10-23T12:00:00Z", "run_id": o.runId}, POLICY, "skeleton"
    )
    assert len(payload["pose"]) == 12
    assert all("confidence" in p and "visibility" not in p for p in payload["pose"])


def test_score_configuration_requires_explicit_version_and_model_policy_pairing():
    values = config().model_dump()
    values["model"] = {"variant": "rtmo-s", "path": ".local/models/rtmo_s_body7_640.onnx"}
    with pytest.raises(ValidationError):
        EdgeConfig.model_validate(values)
    values["events"]["policy"] = {
        "version": "floor-rtmo-score-v0.1",
        "qualitySource": "RTMO_KEYPOINT_SCORE",
    }
    assert EdgeConfig.model_validate(values).model.variant == "rtmo-s"
    with pytest.raises(ValueError):
        configured_policy({"qualitySource": "RTMO_KEYPOINT_SCORE"})


def test_legacy_fingerprint_is_unchanged_and_score_threshold_is_part_of_new_fingerprint(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    assert "qualitySource" not in DEFAULT_POLICY.to_dict()
    assert "minKeypointScore" not in DEFAULT_POLICY.to_dict()
    c = config()
    original = EventRuntime(c, calibration(), "synthetic-hash", GEOMETRY).fingerprint
    c.processing.minKeypointScore = 0.8
    assert EventRuntime(c, calibration(), "synthetic-hash", GEOMETRY).fingerprint == original
    c.model.variant = "rtmo-s"
    c.model.path = ".local/models/rtmo_s_body7_640.onnx"
    c.events.policy = {"version": "floor-rtmo-score-v0.1", "qualitySource": "RTMO_KEYPOINT_SCORE"}
    with pytest.raises(EdgeError) as caught:
        EventRuntime(c, calibration(), "synthetic-hash", GEOMETRY)
    assert caught.value.code == "POLICY_QUALITY_CONFLICT"
    c.processing.minKeypointScore = 0.5
    first = EventRuntime(c, calibration(), "synthetic-hash", GEOMETRY).fingerprint
    c.processing.minKeypointScore = 0.8
    c.events.policy.update({"version": "floor-rtmo-score-test2", "minKeypointScore": 0.8})
    assert EventRuntime(c, calibration(), "synthetic-hash", GEOMETRY).fingerprint != first


def test_pinned_archive_is_verified_and_never_extracts_untrusted_paths(tmp_path, monkeypatch):
    from radar_edge import model

    monkeypatch.chdir(tmp_path)
    content = b"synthetic-test-model"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("../../outside.onnx", content)
        archive.writestr("../../unexpected.txt", b"not extracted")
    data = stream.getvalue()
    spec = replace(
        model.get_model_spec("rtmo-s"),
        sha256=hashlib.sha256(content).hexdigest(),
        archive_sha256=hashlib.sha256(data).hexdigest(),
    )
    monkeypatch.setattr(model, "MODEL_SPECS", {"rtmo-s": spec})

    @contextmanager
    def response(*args, **kwargs):
        value = Mock()
        value.iter_bytes.return_value = [data]
        yield value

    monkeypatch.setattr(model.httpx, "stream", response)
    assert model.fetch_model(variant="rtmo-s")["sha256"] == spec.sha256
    assert Path(spec.default_path).read_bytes() == content
    assert not Path("outside.onnx").exists()
    assert not Path("unexpected.txt").exists()
    Path(spec.default_path).unlink()
    monkeypatch.setattr(model, "MODEL_SPECS", {"rtmo-s": replace(spec, archive_sha256="0" * 64)})
    with pytest.raises(EdgeError) as caught:
        model.fetch_model(variant="rtmo-s")
    assert caught.value.code == "MODEL_HASH_MISMATCH"
    assert not Path(spec.default_path).exists()
    assert not list(Path(".local/models").glob("*.part"))
