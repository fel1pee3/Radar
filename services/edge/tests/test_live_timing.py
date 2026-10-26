"""Telemetry clocks are not video time, and never alter a temporal decision."""

from dataclasses import replace

from temporal_support import observation

from radar_edge.metrics import Metrics


def test_live_frame_age_is_separate_from_source_clock_and_bounded_aggregation():
    metrics = Metrics()
    metrics.add(
        replace(
            observation(1000),
            mode="LIVE",
            frameAgeAtAnalysisStartMs=12,
            frameAgeAfterInferenceMs=112,
        )
    )
    metrics.add(
        replace(
            observation(1200),
            mode="LIVE",
            frameAgeAtAnalysisStartMs=8,
            frameAgeAfterInferenceMs=208,
        )
    )
    report = metrics.summary()
    assert report["analysisSamplesPerMediaSecond"] == 5
    assert report["liveFrameAgeMs"]["frameAgeAtAnalysisStartMs"] == {
        "samples": 2,
        "mean": 10,
        "max": 12,
    }
    assert report["liveFrameAgeMs"]["frameAgeAfterInferenceMs"] == {
        "samples": 2,
        "mean": 160,
        "max": 208,
    }
    assert not any(
        isinstance(value, list) for age in metrics.live_age.values() for value in age.values()
    )


def test_file_does_not_invent_live_age_from_replay_speed():
    metrics = Metrics()
    metrics.add(observation(0))
    assert all(
        value["samples"] == 0 and value["mean"] is None
        for value in metrics.summary()["liveFrameAgeMs"].values()
    )
