"""Synthetic rendering checks; no GUI or personal frames are opened."""

from dataclasses import replace

import numpy as np
import pytest
from temporal_support import observation

from radar_edge.observations import Landmark, Pose
from radar_edge.preview import LocalPreview, diagnostic_lines, render, usable_point
from radar_edge.source import Frame, Geometry


@pytest.mark.parametrize(
    "changes",
    [
        {"presence": 0.1},
        {"presence": None},
        {"visibility": 0.1},
        {"visibility": float("nan")},
        {"presence": float("nan")},
        {"x": float("nan")},
        {"y": float("inf")},
        {"x": -0.1},
        {"presence": 1.1},
    ],
)
def test_green_never_claims_low_presence_or_nonfinite_points_are_usable(changes):
    point = Landmark(11, 0.4, 0.5, None, 0.9, 0.9)
    assert usable_point(point, 0.5)
    assert not usable_point(replace(point, **changes), 0.5)


def test_render_hides_bad_presence_and_never_reuses_previous_pose():
    frame = Frame(
        0,
        0,
        "MEDIA_PTS",
        np.zeros((360, 640, 3), dtype=np.uint8),
        Geometry(640, 360, 640, 360, 640, 360, 0),
    )
    valid = observation(0)
    rendered = render(frame, valid, (), 0.5)
    green = np.array((90, 220, 100), dtype=np.uint8)
    assert np.any(np.all(rendered[:360] == green, axis=2))
    low = replace(
        valid,
        poses=(Pose(tuple(replace(point, presence=0.1) for point in valid.poses[0].landmarks)),),
    )
    hidden = render(frame, low, (), 0.5)
    assert not np.any(np.all(hidden[:360] == green, axis=2))
    absent = render(frame, replace(valid, poses=(), poseCount=0), (), 0.5)
    assert not np.any(np.all(absent[:360] == green, axis=2))
    assert not frame.bgr.any()  # Rendering does not change source pixels.
    lines = diagnostic_lines(low, 0.5)
    assert any("Pose insuficiente" in line for line in lines)
    assert any("visibilidade/presenca insuficiente" in line for line in lines)
    assert any("nao confirma pessoa no piso" in line for line in lines)


def test_live_preview_accepts_remote_resume_and_q_while_paused(monkeypatch):
    import radar_edge.preview as module

    keys = iter([-1, -1, ord(" "), ord("q")])
    transitions = []
    monkeypatch.setattr(module.cv2, "namedWindow", lambda *_: None)
    monkeypatch.setattr(module.cv2, "imshow", lambda *_: None)
    monkeypatch.setattr(module.cv2, "waitKey", lambda *_: next(keys))
    monkeypatch.setattr(module.cv2, "getWindowProperty", lambda *_: 1)
    monkeypatch.setattr(module.cv2, "destroyWindow", lambda *_: None)
    frame = Frame(
        0,
        0,
        "HOST_MONOTONIC",
        np.zeros((360, 640, 3), dtype=np.uint8),
        Geometry(640, 360, 640, 360, 640, 360, 0),
    )
    preview = LocalPreview(True)
    preview.blocking_pause = False
    preview.on_pause = transitions.append
    preview.__enter__()
    assert preview.show(frame, observation(0), (), 0.5)
    preview.set_paused(True)  # Remote pause must not enter a blocking GUI loop.
    assert preview.poll() and preview.paused
    preview.set_paused(False)  # A subsequent terminal command can resume.
    assert preview.poll() and preview.paused  # Space pauses again, without blocking.
    assert not preview.poll()  # Q remains responsive while capture is released.
    assert transitions == [True, False, True]  # Q never reopens the camera to stop it.
    monkeypatch.setattr(module.cv2, "waitKey", lambda *_: -1)
    preview.close()
    assert preview._last_view is None


@pytest.mark.parametrize("field,value", [("x", float("nan")), ("y", float("inf"))])
def test_render_nonfinite_coordinates_reports_quality_without_crashing(field, value):
    o = observation(0)
    points = tuple(replace(point, **{field: value}) for point in o.poses[0].landmarks)
    o = replace(o, poses=(Pose(points),))
    frame = Frame(
        0,
        0,
        "MEDIA_PTS",
        np.zeros((360, 640, 3), dtype=np.uint8),
        Geometry(640, 360, 640, 360, 640, 360, 0),
    )
    assert render(frame, o, (), 0.5).shape[0] > 360
    assert any("fora do quadro" in line for line in diagnostic_lines(o, 0.5))


@pytest.mark.parametrize("keys,expected", [([32], True), ([27], False), ([ord("q")], False)])
def test_start_paused_waits_for_intent_and_releases_topmost(monkeypatch, keys, expected):
    import radar_edge.preview as preview_module

    clock = [1.0]
    topmost = []
    shown = []
    sequence = iter([-1, -1, *keys])

    def wait(_):
        clock[0] += 1.0
        return next(sequence)

    monkeypatch.setattr(preview_module, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(preview_module.cv2, "namedWindow", lambda *_: None)
    monkeypatch.setattr(preview_module.cv2, "setWindowProperty", lambda *v: topmost.append(v[-1]))
    monkeypatch.setattr(preview_module.cv2, "getWindowProperty", lambda *_: 1.0)
    monkeypatch.setattr(preview_module.cv2, "imshow", lambda _, value: shown.append(value))
    monkeypatch.setattr(preview_module.cv2, "waitKey", wait)
    monkeypatch.setattr(preview_module.cv2, "destroyWindow", lambda *_: None)
    frame = Frame(
        0,
        0,
        "MEDIA_PTS",
        np.zeros((360, 640, 3), dtype=np.uint8),
        Geometry(640, 360, 640, 360, 640, 360, 0),
    )
    preview = LocalPreview(True, start_paused=True)
    preview.__enter__()
    assert preview.show(frame, observation(0), (), 0.5) is expected
    assert preview.paused_seconds == 3.0 and not preview.paused
    assert topmost == [1, 0]
    # Avoid another key read during cleanup in this synthetic test.
    monkeypatch.setattr(preview_module.cv2, "waitKey", lambda *_: -1)
    preview.close()
    assert shown


@pytest.mark.parametrize(
    "argument,enabled,paused", [("--preview-paused", True, True), ("--no-preview", False, False)]
)
def test_cli_preview_control_is_explicit_and_preserves_no_preview(
    monkeypatch, capsys, argument, enabled, paused
):
    import json
    import sys
    from unittest.mock import Mock

    from temporal_support import config

    from radar_edge.cli import main

    c = config()
    c.processing.preview = c.processing.previewStartPaused = True
    run = Mock(return_value=({"status": "ok"}, 0))
    monkeypatch.setattr("radar_edge.config.load_config", lambda _: c)
    monkeypatch.setattr("radar_edge.pipeline.run_pipeline", run)
    monkeypatch.setattr(sys, "argv", ["radar-edge", "run", argument])
    main()
    used = run.call_args.args[0].processing
    assert used.preview is enabled and used.previewStartPaused is paused
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
