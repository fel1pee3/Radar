"""V2 priorities on synthetic current observations; not visual/hardware evidence."""

from dataclasses import replace

import numpy as np
import pytest
from test_posture_candidate import rtmo_observation
from test_preferred_rtmo import frame

from radar_edge.reacquiring_rtmo import ReacquiringRtmoEstimator


def controlled(monkeypatch, callback, proposal=False):
    model = ReacquiringRtmoEstimator("never-opened")
    native = rtmo_observation(0).poses[0]
    calls = []

    def run(path, image, box):
        calls.append((image.timestamp_ms, path))
        count = callback(image.timestamp_ms, path)
        model.proposal = np.array([10, 20, 400, 300]) if proposal and path == "ORIGINAL" else None
        poses = (
            replace(
                native,
                landmarks=tuple(
                    replace(p, x=(image.timestamp_ms % 1000) / 1000) for p in native.landmarks
                ),
            ),
        ) * count
        model.perception_attempts.append(
            {"pass": path, "poseCount": count, "usableEssentialCount": 8 if count == 1 else 0}
        )
        return poses, (), 0.9

    monkeypatch.setattr(model, "_run_path", run)
    return model, calls


def test_failed_preference_uses_current_original_and_leaves_reacquisition(monkeypatch):
    model, calls = controlled(
        monkeypatch, lambda t, p: int((t == 0 and p == "ROTATE_270") or (t > 0 and p == "ORIGINAL"))
    )
    model.estimate(frame(0))
    poses, _ = model.estimate(frame(200))
    assert calls[-2:] == [(200, "ROTATE_270"), (200, "ORIGINAL")]
    assert poses[0].landmarks[0].x == 0.2 and model.preferred == "ORIGINAL"
    model.estimate(frame(400))
    assert calls[-1] == (400, "ORIGINAL")


def test_each_untracked_image_gets_original_before_continuing_search(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(t >= 400 and p == "ROTATE_180"))
    for t in (0, 200, 400):
        poses, _ = model.estimate(frame(t))
        paths = [p for ts, p in calls if ts == t]
        assert paths[0] == "ORIGINAL" and len(paths) <= 2
    assert poses and model.preferred == "ROTATE_180"
    model.estimate(frame(600))
    assert calls[-1] == (600, "ROTATE_180")


def test_failed_crop_does_not_starve_orientation_search(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"), proposal=True)
    model.estimate(frame(0))
    poses, _ = model.estimate(frame(200))
    assert calls == [
        (0, "ORIGINAL"),
        (0, "PERSON_PROPOSAL_CROP"),
        (200, "ORIGINAL"),
        (200, "ROTATE_270"),
    ]
    assert poses and model.proposal is None


def test_budget_defers_original_but_it_is_first_in_next_analysis(monkeypatch):
    clock = [0.0]

    def response(t, p):
        if t == 200:
            clock[0] = 0.230
            return 0
        return int(p == ("ROTATE_270" if t == 0 else "ORIGINAL"))

    model, calls = controlled(monkeypatch, response)
    monkeypatch.setattr("radar_edge.reacquiring_rtmo.perf_counter", lambda: clock[0])
    model.estimate(frame(0))
    poses, _ = model.estimate(frame(200))
    assert not poses and calls[-1] == (200, "ROTATE_270")
    diagnostic = model.perception_attempts[0]["strategy"]
    assert diagnostic["originalDeferredAfterFailure"]
    assert diagnostic["nextAnalysisPriority"] == "ORIGINAL"
    assert "EXTRA_CALL_BUDGET" in diagnostic["transitions"]
    clock[0] = 0
    poses, _ = model.estimate(frame(400))
    assert calls[-1] == (400, "ORIGINAL") and poses[0].landmarks[0].x == 0.4


@pytest.mark.parametrize("reason", ["SOURCE_RECONNECT", "PAUSE_OR_RESUME", "SOURCE_UNAVAILABLE"])
def test_external_interruption_forces_current_canonical_first(monkeypatch, reason):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    model.estimate(frame(0))
    model.reset_preference(reason)
    model.estimate(frame(200))
    assert [p for t, p in calls if t == 200][0] == "ORIGINAL"


def test_geometry_and_gap_break_preference(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: int(p == "ROTATE_270"))
    model.estimate(frame(0))
    model.estimate(frame(200, (480, 640, 3)))
    model.estimate(frame(1000, (480, 640, 3)))
    for t in (200, 1000):
        assert [p for ts, p in calls if ts == t][0] == "ORIGINAL"


def test_audit_retains_multiple_people_and_clears_preference(monkeypatch):
    model, _ = controlled(
        monkeypatch, lambda t, p: 2 if t == 800 and p == "ORIGINAL" else int(p == "ROTATE_270")
    )
    for t in range(0, 801, 200):
        poses, _ = model.estimate(frame(t))
    assert len(poses) == 2 and model.preferred is None


def test_exhausted_search_remains_inconclusive_and_canonical_first(monkeypatch):
    model, calls = controlled(monkeypatch, lambda t, p: 0)
    for t in range(0, 4400, 200):
        poses, _ = model.estimate(frame(t))
        paths = [p for ts, p in calls if ts == t]
        assert paths[0] == "ORIGINAL" and len(paths) <= 2
        assert not poses and model.preferred is None
        assert model.perception_attempts[0]["strategy"]["nextAnalysisPriority"] == "ORIGINAL"
    assert model.counts["reset.SEARCH_CYCLE_EXHAUSTED"] > 0
