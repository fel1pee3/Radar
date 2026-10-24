import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import cv2
import numpy as np
import pytest
import yaml

from radar_edge.calibration import calibrate
from radar_edge.config import EdgeConfig, load_config, private_path
from radar_edge.errors import EdgeError
from radar_edge.estimator import MediaPipeEstimator
from radar_edge.model import MODEL_SHA256, verify_model
from radar_edge.observations import Landmark, Pose, body_poses, pose_quality
from radar_edge.pipeline import doctor, run_pipeline
from radar_edge.preview import fit_display, select_floor
from radar_edge.source import FileSource, Frame, Geometry

MODEL = Path(__file__).resolve().parents[3] / ".local/models/pose_landmarker_lite.task"


def test_pose_quality_distinguishes_missing_partial_low_and_multiple():
    valid = Pose(tuple(Landmark(index, 0.5, 0.5, None, 0.9, 0.9) for index in range(11, 33)))
    assert pose_quality((), 0.5)[0] == "NO_POSE"
    assert pose_quality((valid, valid), 0.5)[0] == "MULTIPLE_POSES"
    assert pose_quality((valid,), 0.5) == ("ONE_VALID_POSE", ())
    for replacement, reason in (
        ({"x": None}, "MISSING_LANDMARK"),
        ({"x": -0.1}, "BODY_OUT_OF_FRAME"),
        ({"visibility": 0.2}, "LOW_LANDMARK_QUALITY"),
    ):
        points = list(valid.landmarks)
        points[0] = replace(points[0], **replacement)
        assert reason in pose_quality((Pose(tuple(points)),), 0.5)[1]
    partial = Pose(tuple(point for point in valid.landmarks if point.index != 23))
    assert "MISSING_LANDMARK" in pose_quality((partial,), 0.5)[1]


def test_portrait_display_and_clicks_keep_normalized_calibration(monkeypatch):
    image = np.zeros((1280, 640, 3), dtype=np.uint8)
    displayed = fit_display(image)
    assert displayed.shape[:2] == (720, 360)
    frame = Frame(0, 0, "MEDIA_PTS", image, Geometry(640, 1280, 640, 1280, 640, 1280, 0))
    closed = []

    def register(_name, callback):
        for x, y in ((0, 360), (359, 360), (359, 719)):
            callback(cv2.EVENT_LBUTTONDOWN, x, y, 0, None)

    monkeypatch.setattr(cv2, "namedWindow", lambda *_: None)
    monkeypatch.setattr(cv2, "setMouseCallback", register)
    monkeypatch.setattr(cv2, "imshow", lambda *_: None)
    monkeypatch.setattr(cv2, "waitKey", lambda *_: 13)
    monkeypatch.setattr(cv2, "getWindowProperty", lambda *_: 1)
    monkeypatch.setattr(cv2, "destroyWindow", lambda name: closed.append(name))
    points = select_floor(frame)
    assert points[0] == pytest.approx((0, 360 / 719))
    assert points[1] == pytest.approx((1, 360 / 719))
    assert points[2] == (1, 1)
    assert frame.bgr.shape[:2] == (1280, 640)
    assert len(closed) == 1


def test_conversion_keeps_unavailable_values_null_and_omits_face():
    points = [SimpleNamespace(x=0.3, y=0.6, z=0.1, visibility=0.9, presence=0.8) for _ in range(33)]
    points[11] = SimpleNamespace(x=float("nan"), y=0.6, z=None, visibility=None)
    poses = body_poses(SimpleNamespace(pose_landmarks=[points]))
    assert len(poses[0].landmarks) == 22
    assert poses[0].landmarks[0].x is None
    assert poses[0].landmarks[0].presence is None
    assert poses[0].landmarks[0].visibility is None
    assert poses[0].landmarks[0].index == 11


@pytest.fixture
def configured(tmp_path, monkeypatch, synthetic_video):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / ".local"
    directory.mkdir()
    config = EdgeConfig.model_validate(
        {
            "cameraId": str(uuid4()),
            "source": {
                "kind": "FILE",
                "path": str(synthetic_video),
                "videoId": "synthetic",
                "authorized": True,
            },
        }
    )
    points = directory / "points.json"
    points.write_text(json.dumps([[0, 0.5], [1, 0.5], [1, 1], [0, 1]]))
    return config, points


def test_calibration_revision_and_no_frame_saved(configured):
    config, points = configured
    first = calibrate(config, 500, str(points), True)
    second = calibrate(config, 1000, str(points), True)
    assert first["calibrationId"] == second["calibrationId"]
    assert (first["version"], second["version"]) == (1, 2)
    saved = json.loads(Path(config.calibrationPath).read_text())
    assert saved["frameIndex"] == 10
    assert saved["timestampMs"] == 1000
    assert len(list(Path(".local").glob("calibration*.json"))) == 2
    assert not list(Path(".local").rglob("*.png"))
    assert not list(Path(".local").rglob("*.jpg"))
    with pytest.raises(EdgeError) as caught:
        calibrate(config, 0, str(points), False)
    assert caught.value.code == "FLOOR_CONFIRMATION_REQUIRED"
    with pytest.raises(EdgeError) as caught:
        calibrate(config, 10000, str(points), True)
    assert caught.value.code == "CALIBRATION_FRAME_MISSING"
    assert json.loads(Path(config.calibrationPath).read_text())["version"] == 2


def test_private_config_authorization_bounds_and_unknown_fields(configured):
    config, _ = configured
    path = Path(".local/config.yaml")
    for change in (
        {"source": {**config.source.model_dump(), "authorized": False}},
        {"source": {**config.source.model_dump(), "path": "rtsp://secret.invalid/video"}},
        {"source": {**config.source.model_dump(), "rotation": True}},
        {"source": {**config.source.model_dump(), "kind": "WEBCAM"}},
        {"processing": {"targetAnalysisFps": float("nan")}},
        {"unexpected": "private-secret-do-not-log"},
    ):
        path.write_text(yaml.safe_dump({**config.model_dump(), **change}), encoding="utf-8")
        with pytest.raises(EdgeError) as caught:
            load_config(path)
        assert "private-secret" not in str(caught.value)
    path.write_text(yaml.safe_dump(config.model_dump()), encoding="utf-8")
    assert load_config(path).source.authorized
    with pytest.raises(EdgeError):
        private_path("outside.json")
    with pytest.raises(EdgeError):
        private_path(".local/../outside.json")


def test_missing_calibration_fails_before_model_and_exports_are_opt_in(configured):
    config, _ = configured
    result, code = run_pipeline(config)
    assert code == 1
    assert result["error"]["code"] == "CALIBRATION_REQUIRED"
    assert not result["model"]["loaded"]
    assert not list(Path(".local").rglob("observations.jsonl"))


@pytest.fixture
def with_model(configured):
    config, points = configured
    if not MODEL.is_file():
        pytest.skip(
            "Official model unavailable; run radar-edge model-fetch for real inference tests"
        )
    target = Path(config.model.path)
    target.parent.mkdir(parents=True)
    shutil.copyfile(MODEL, target)
    calibrate(config, 0, str(points), True)
    return config


def test_real_cpu_model_on_synthetic_file_and_replay_speed_preserves_sequence(with_model):
    config = with_model
    diagnostic = doctor(config)
    assert diagnostic["modelLoaded"] and diagnostic["inferenceExecuted"]
    assert diagnostic["modelSha256"] == MODEL_SHA256
    assert diagnostic["poseCount"] == 0
    config.diagnostics.exportObservations = True
    fast, fast_code = run_pipeline(config)
    config.processing.replaySpeed = 2.0
    paced, paced_code = run_pipeline(config)
    assert (fast_code, paced_code) == (0, 0)
    assert fast["mediaSequenceSha256"] == paced["mediaSequenceSha256"]
    for result in (fast, paced):
        assert result["captureState"] == "ENDED"
        assert result["decodedFrames"] == 20
        assert result["metrics"]["analyzedFrames"] == 10
        assert result["metrics"]["skippedBySampling"] == 10
        assert result["metrics"]["inferenceStates"] == {"NO_POSE": 10}
        assert result["model"]["loaded"]
        assert result["metrics"]["inferenceMs"]["mean"] > 0
        assert not result["framesSaved"] and not result["incidentsEmitted"]
        exported = (
            Path(result["reportPath"]).with_name("observations.jsonl").read_text().splitlines()
        )
        assert [
            (json.loads(line)["frameIndex"], json.loads(line)["timestampMs"]) for line in exported
        ] == [(index, index * 100) for index in range(0, 20, 2)]
    assert paced["metrics"]["totalWallSeconds"] >= 0.9


def test_real_estimator_monotonicity_rgb_and_release(with_model):
    with FileSource(with_model.source) as source:
        frame = source.read()
    estimator = MediaPipeEstimator(with_model.model.path)
    with estimator:
        assert estimator.estimate(frame)[0] == ()
        with pytest.raises(EdgeError) as caught:
            estimator.estimate(frame)
        assert caught.value.code == "MODEL_TIMESTAMP_ERROR"
    assert estimator.landmarker is None
    assert source.capture is None


def test_limit_stop_and_bounded_export(with_model):
    with_model.processing.maxObservations = 3
    with_model.diagnostics.exportObservations = True
    with_model.diagnostics.maxExportObservations = 1
    result, code = run_pipeline(with_model)
    assert code == 0
    assert result["captureState"] == "STOPPED_LIMIT"
    assert result["metrics"]["analyzedFrames"] == 3
    assert result["observationExport"]["count"] == 1
    assert result["observationExport"]["truncated"]


def test_model_failure_releases_resources_and_cannot_become_no_pose(configured, monkeypatch):
    config, points = configured
    calibrate(config, 0, str(points), True)
    closed = []

    class FailedEstimator:
        def __init__(self, _path, _variant="lite"):
            pass

        def __enter__(self):
            return self

        def estimate(self, _frame):
            raise EdgeError("MODEL_INFERENCE_ERROR", "Falha de teste, sem inferência.")

        def __exit__(self, *_):
            closed.append(True)

    monkeypatch.setattr("radar_edge.estimator.MediaPipeEstimator", FailedEstimator)
    result, code = run_pipeline(config)
    assert code == 1
    assert result["captureState"] == "ERROR"
    assert result["error"]["code"] == "MODEL_INFERENCE_ERROR"
    assert result["metrics"]["inferenceStates"] == {}
    assert closed == [True]


def test_hash_tamper_cannot_load_a_different_model(configured):
    config, _ = configured
    target = Path(config.model.path)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"tampered model")
    with pytest.raises(EdgeError) as caught:
        verify_model(target)
    assert caught.value.code == "MODEL_HASH_MISMATCH"


@pytest.mark.parametrize("interrupted", [True, False])
def test_requested_stop_or_keyboard_interrupt_closes_source_model_preview(
    configured, monkeypatch, interrupted
):
    config, points = configured
    calibrate(config, 0, str(points), True)
    closed = []
    original_close = FileSource.close

    def close_source(self):
        original_close(self)
        closed.append("source")

    class TestEstimator:
        def __init__(self, _path, _variant="lite"):
            pass

        def __enter__(self):
            return self

        def estimate(self, _frame):
            if interrupted:
                raise KeyboardInterrupt()
            return (), 1.0

        def __exit__(self, *_):
            closed.append("model")

    class TestPreview:
        def __init__(self, _enabled, _start_paused=False):
            self.paused_seconds = 0.0

        def __enter__(self):
            return self

        def show(self, *_):
            return False

        def __exit__(self, *_):
            closed.append("preview")

    monkeypatch.setattr(FileSource, "close", close_source)
    monkeypatch.setattr("radar_edge.estimator.MediaPipeEstimator", TestEstimator)
    monkeypatch.setattr("radar_edge.pipeline.LocalPreview", TestPreview)
    result, code = run_pipeline(config)
    assert code == (130 if interrupted else 0)
    assert result["captureState"] == ("INTERRUPTED" if interrupted else "STOPPED_REQUEST")
    assert closed == ["preview", "model", "source"]


def test_cli_missing_file_reports_controlled_error_without_private_path(configured):
    config, _ = configured
    config.source.path = ".local/private-secret-video-name.mp4"
    path = Path(".local/missing.yaml")
    path.write_text(yaml.safe_dump(config.model_dump()), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from radar_edge.cli import main; main()",
            "doctor",
            "--config",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert result.returncode == 1
    assert '"code": "FILE_MISSING"' in result.stderr
    assert "private-secret-video-name" not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(os.environ.get("RADAR_TEST_GUI") != "1", reason="Explicit local GUI test")
def test_real_preview_window_stops_by_limit_and_closes(with_model):
    with_model.processing.preview = True
    with_model.processing.maxObservations = 2
    result, code = run_pipeline(with_model)
    assert code == 0
    assert result["captureState"] == "STOPPED_LIMIT"
    assert result["metrics"]["analyzedFrames"] == 2
    # Window was actually created/drawn/destroyed; no human inspection is implied.
    assert cv2.getWindowProperty("Radar - poses locais REPLAY", cv2.WND_PROP_VISIBLE) < 1
