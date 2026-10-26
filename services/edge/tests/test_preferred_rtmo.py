"""Synthetic controller faults and native-coordinate mapping; no physical evidence."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from test_posture_candidate import rtmo_observation

from radar_edge.preferred_rtmo import PreferredRtmoEstimator


def frame(t, shape=(360, 640, 3)):
    return SimpleNamespace(timestamp_ms=t, bgr=np.full(shape, t % 255, np.uint8))


def controlled(monkeypatch, callback):
    model = PreferredRtmoEstimator("never-opened")
    native = rtmo_observation(0).poses[0]
    calls = []

    def run(path, image, proposal):
        calls.append((image.timestamp_ms, path))
        result = callback(image.timestamp_ms, path)
        poses = (
            replace(
                native,
                landmarks=tuple(
                    replace(p, x=(image.timestamp_ms % 1000) / 1000) for p in native.landmarks
                ),
            ),
        ) * result
        model.proposal = None
        model.perception_attempts.append(
            {"pass": path, "poseCount": result, "usableEssentialCount": 8 if result == 1 else 0}
        )
        return poses, (), 0.9

    monkeypatch.setattr(model, "_run_path", run)
    return model, calls


def test_preference_saves_repeated_failures_but_every_pose_is_from_current_frame(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    for t in (0, 200, 400, 600, 800):
        poses, _ = model.estimate(frame(t))
        assert len(poses) == 1 and poses[0].landmarks[0].x == t / 1000
    assert [p for t, p in calls if t == 200] == ["ROTATE_270"]
    assert [p for t, p in calls if t == 800] == ["ORIGINAL", "ROTATE_270"]
    assert not any(isinstance(v, np.ndarray) for v in vars(model).values())


def test_lost_current_pose_is_not_filled_and_search_can_find_another_orientation(monkeypatch):
    model, calls = controlled(
        monkeypatch,
        lambda t, p: int((t == 0 and p == "ROTATE_270") or (t >= 400 and p == "ROTATE_90")),
    )
    model.estimate(frame(0))
    poses, _ = model.estimate(frame(200))
    assert not poses and model.preferred is None
    assert calls[-2:] == [(200, "ROTATE_270"), (200, "ORIGINAL")]
    poses, _ = model.estimate(frame(400))
    assert poses and model.preferred == "ROTATE_90"


@pytest.mark.parametrize("reason", ["SOURCE_RECONNECT", "PAUSE_OR_RESUME", "SOURCE_UNAVAILABLE"])
def test_external_break_invalidates_preference_and_requires_canonical_image(monkeypatch, reason):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    model.estimate(frame(0))
    model.reset_preference(reason)
    model.estimate(frame(200))
    assert [p for t, p in calls if t == 200][0] == "ORIGINAL"
    assert model.strategy_summary()["counts"]["reset." + reason] == 1


def test_geometry_and_input_gap_invalidate_without_modifying_timestamps(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    model.estimate(frame(0))
    model.estimate(frame(200, (480, 640, 3)))
    model.estimate(frame(1000, (480, 640, 3)))
    assert [p for t, p in calls if t == 200][0] == "ORIGINAL"
    assert [p for t, p in calls if t == 1000][0] == "ORIGINAL"
    assert model.previous_ms == 1000
    assert model.counts["reset.GEOMETRY_CHANGED"] == model.counts["reset.INPUT_GAP"] == 1


def test_canonical_audit_does_not_hide_a_second_person(monkeypatch):
    model, _ = controlled(
        monkeypatch, lambda t, p: 2 if t == 800 and p == "ORIGINAL" else int(p == "ROTATE_270")
    )
    for t in range(0, 801, 200):
        poses, _ = model.estimate(frame(t))
    assert len(poses) == 2 and model.preferred is None


def test_no_pose_search_is_finite_and_never_means_empty(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: 0)
    for t in range(0, 4200, 200):
        poses, _ = model.estimate(frame(t))
        assert not poses and model.preferred is None
        assert sum(ts == t for ts, _ in calls) <= 2
    assert model.counts["inconclusive"] == 21
    assert model.counts["reset.SEARCH_CYCLE_EXHAUSTED"] > 0
    assert set(p for _, p in calls) >= {
        "ORIGINAL",
        "ROTATE_270",
        "ROTATE_90",
        "ROTATE_180",
        "CENTER_80",
    }


def test_slow_native_call_defers_extra_work_without_claiming_current_pose(monkeypatch):
    clock = [0.0]
    model, calls = controlled(monkeypatch, lambda t, p: clock.__setitem__(0, 0.230) or 0)
    monkeypatch.setattr("radar_edge.preferred_rtmo.perf_counter", lambda: clock[0])
    poses, _ = model.estimate(frame(0))
    assert not poses and len(calls) == 1 and model.counts["extraCallDeferred"] == 1


def test_expired_lease_is_not_renewed_from_an_old_success(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    model.estimate(frame(0))
    model.lease_until = 200
    model.estimate(frame(200))
    assert [p for t, p in calls if t == 200][0] == "ORIGINAL"
    assert model.counts["reset.LEASE_EXPIRED"] == 1


def test_periodic_audit_does_not_spend_rotation_budget_on_redundant_crop(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    actual = model._run_path

    def with_proposal(path, image, proposal):
        result = actual(path, image, proposal)
        if path == "ORIGINAL":
            model.proposal = np.array([10, 100, 400, 200])
        return result

    monkeypatch.setattr(model, "_run_path", with_proposal)
    for t in (0, 200, 400, 600, 800):
        model.estimate(frame(t))
    assert [p for t, p in calls if t == 800] == ["ORIGINAL", "ROTATE_270"]


def test_proposal_crop_never_uses_a_box_from_a_previous_frame(monkeypatch):
    model = PreferredRtmoEstimator("never-opened")
    native = rtmo_observation(0).poses[0]
    boxes = []

    def infer(pixels):
        model.proposal = np.array([20, 30, 200, 300]) if not boxes else None
        model.perception_attempts.append({})
        return (), (), 0.6

    def crop(image, box):
        boxes.append(tuple(box))
        model.perception_attempts.append({})
        return (native,), (), 0.9

    monkeypatch.setattr(model, "infer_image", infer)
    monkeypatch.setattr(model, "proposal_crop", crop)
    model.estimate(frame(0))
    assert boxes == [(20, 30, 200, 300)] and model.proposal is None
    # Test the next canonical pass with a missing ROI; no crop gets the old box.
    monkeypatch.setattr(
        model, "quarter_turn", lambda *args: model.perception_attempts.append({}) or ((), (), 0.1)
    )
    model.estimate(frame(200))
    assert len(boxes) == 1


@pytest.mark.parametrize("path", ["ROTATE_90", "ROTATE_270", "ROTATE_180", "CENTER_80"])
def test_transform_restores_original_coordinates_and_native_labels(monkeypatch, path):
    model = PreferredRtmoEstimator("never-opened")
    w, h, x, y = 640, 360, 127, 249
    native = rtmo_observation(0).poses[0]
    if path == "ROTATE_90":
        qx, qy = (h - 1 - y) / h, x / w
    elif path == "ROTATE_270":
        qx, qy = y / h, (w - 1 - x) / w
    elif path == "ROTATE_180":
        qx, qy = (w - 1 - x) / w, (h - 1 - y) / h
    else:
        qx, qy = (x - 64) / 512, (y - 36) / 288
    transformed = replace(native, landmarks=tuple(replace(p, x=qx, y=qy) for p in native.landmarks))

    def infer(pixels):
        model.perception_attempts.append({})
        return (transformed,), ((qx, qy, qx, qy, 0.9),), 0.9

    monkeypatch.setattr(model, "infer_image", infer)
    poses, boxes, _ = model._run_path(path, frame(0), None)
    assert boxes[0][:4] == pytest.approx((x / w, y / h, x / w, y / h))
    for a, b in zip(native.landmarks, poses[0].landmarks, strict=True):
        assert (b.x, b.y) == pytest.approx((x / w, y / h))
        assert (b.index, b.confidence, b.visibility, b.presence) == (
            a.index,
            a.confidence,
            None,
            None,
        )
