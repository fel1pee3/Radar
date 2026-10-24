import json
from dataclasses import asdict, replace

import numpy as np
import pytest
from temporal_support import observation

from radar_edge.observations import Landmark, Pose
from radar_edge.visual_smoothing import VisualSmoother


def sample(t, x=130.0, confidence=0.9):
    point = Landmark(11, x / 639, 100 / 359, None, None, None, confidence)
    return observation(
        t,
        width=640,
        height=360,
        runId="visual-research",
        modelId="rtmo-s-test",
        poses=(Pose((point,), "RTMO_KEYPOINT_SCORE"),),
    )


def test_known_stationary_noise_is_reduced_without_mutating_observations():
    rng = np.random.default_rng(731)
    smoother = VisualSmoother()
    errors, filtered = [], []
    for n in range(300):
        noise = float(rng.normal(0, 2))
        raw = sample(round(n * 1000 / 30), 130 + noise)
        before = json.dumps(asdict(raw), sort_keys=True)
        value = smoother.update(raw)[11][0]
        assert json.dumps(asdict(raw), sort_keys=True) == before
        errors.append(noise)
        filtered.append(value - 130)
    assert np.std(filtered[30:]) < np.std(errors[30:]) * 0.65


@pytest.mark.parametrize("condition", ["missing", "lowScore", "multiple", "outOfFrame"])
def test_current_rejection_removes_old_point_and_resets_history(condition):
    smoother = VisualSmoother()
    smoother.update(sample(0))
    raw = sample(33)
    if condition == "missing":
        raw = replace(raw, poses=(), poseCount=0)
    if condition == "lowScore":
        raw = sample(33, confidence=0.1)
    if condition == "multiple":
        raw = replace(raw, poses=raw.poses * 2, poseCount=2)
    if condition == "outOfFrame":
        raw = sample(33, x=-1)
    assert smoother.update(raw) == {}
    assert not smoother.states
    assert smoother.update(sample(66, x=180))[11][0] == pytest.approx(180)


@pytest.mark.parametrize("change", ["clock", "gap", "run", "calibration", "geometry"])
def test_discontinuity_uses_current_raw_position_without_old_history(change):
    smoother = VisualSmoother()
    smoother.update(sample(100))
    raw = sample(133, x=180)
    if change == "clock":
        raw = replace(raw, timestampMs=50)
    if change == "gap":
        raw = replace(raw, timestampMs=400)
    if change == "run":
        raw = replace(raw, runId="other")
    if change == "calibration":
        raw = replace(raw, calibrationVersion=raw.calibrationVersion + 1)
    if change == "geometry":
        raw = replace(raw, rotation=90)
    assert smoother.update(raw)[11][0] == pytest.approx(180)


def test_step_response_and_maximum_current_offset():
    smoother = VisualSmoother()
    smoother.update(sample(0))
    errors = []
    for n in range(1, 8):
        value = smoother.update(sample(round(n * 1000 / 30), 160))[11][0]
        errors.append(abs(160 - value))
    assert max(errors) <= 8.000001
    assert errors[1] <= 3


def test_portrait_render_maps_filtered_source_pixels_to_display():
    from radar_edge.preview import render
    from radar_edge.source import Frame, Geometry

    raw = replace(sample(0), width=320, height=960)
    point = replace(raw.poses[0].landmarks[0], x=0.5, y=0.5)
    raw = replace(raw, poses=(Pose((point,), "RTMO_KEYPOINT_SCORE"),))
    frame = Frame(
        0,
        0,
        "MEDIA_PTS",
        np.zeros((960, 320, 3), dtype=np.uint8),
        Geometry(320, 960, 320, 960, 320, 960, 0),
    )
    pixels = VisualSmoother().update(raw)
    result = render(frame, raw, (), 0.5, visual_points=pixels)
    cyan = np.all(result[:720] == (255, 210, 40), axis=2)
    y, x = np.where(cyan)
    assert abs(float(x.mean()) - 120) < 2
    assert abs(float(y.mean()) - 360) < 2
    assert not frame.bgr.any()


def test_pause_redraw_does_not_filter_same_observation_again(monkeypatch):
    import radar_edge.preview as module
    from radar_edge.source import Frame, Geometry

    for name in ("namedWindow", "imshow", "destroyWindow"):
        monkeypatch.setattr(module.cv2, name, lambda *_: None)
    monkeypatch.setattr(module.cv2, "waitKey", lambda *_: -1)
    monkeypatch.setattr(module.cv2, "getWindowProperty", lambda *_: 1)
    preview = module.LocalPreview(True)
    preview.blocking_pause = False
    preview.enable_stabilization()
    calls = []
    update = preview._smoother.update

    def recorded(*args):
        calls.append(args[0].timestampMs)
        return update(*args)

    monkeypatch.setattr(preview._smoother, "update", recorded)
    frame = Frame(
        0,
        0,
        "MEDIA_PTS",
        np.zeros((360, 640, 3), dtype=np.uint8),
        Geometry(640, 360, 640, 360, 640, 360, 0),
    )
    with preview:
        preview.show(frame, sample(0), (), 0.5)
        preview.set_paused(True)
        preview.set_paused(False)
        assert calls == [0]


def test_stabilized_preview_rejects_pose_from_another_frame():
    from radar_edge.errors import EdgeError
    from radar_edge.preview import LocalPreview
    from radar_edge.source import Frame, Geometry

    preview = LocalPreview(True)
    preview.enable_stabilization()
    frame = Frame(
        2,
        33,
        "MEDIA_PTS",
        np.zeros((360, 640, 3), dtype=np.uint8),
        Geometry(640, 360, 640, 360, 640, 360, 0),
    )
    with pytest.raises(EdgeError) as failure:
        preview.show(frame, sample(0), (), 0.5)
    assert failure.value.code == "PREVIEW_FRAME_MISMATCH"
