"""Deterministic adapter checks, not physical camera or perception evidence."""

from types import SimpleNamespace

import numpy as np
import pytest
from temporal_support import config

from radar_edge.config import SourceConfig, WebcamConfig
from radar_edge.errors import EdgeError
from radar_edge.live import run_live
from radar_edge.paced_file import PacedFileSource
from radar_edge.source import Frame, Geometry


def source(monkeypatch, *, decode_delay=0, fail=False):
    clock = [0]
    geometry = Geometry(32, 24, 32, 24, 32, 24, 0)
    frames = iter(
        Frame(i, i * 40, "MEDIA_PTS", np.full((24, 32, 3), i, np.uint8), geometry) for i in range(3)
    )

    class Reader:
        fps = 25

        def __init__(self, *_):
            pass

        def __enter__(self):
            return self

        def read(self):
            clock[0] += decode_delay
            if fail and clock[0] > 0:
                raise EdgeError("DECODE_ERROR", "synthetic decode failure")
            return next(frames, None)

        def metadata(self):
            return {"durationMsEstimate": 120, "kind": "FILE", "mode": "REPLAY"}

        def close(self):
            pass

    class Stop:
        stopped = False

        def is_set(self):
            return self.stopped

        def wait(self, seconds):
            clock[0] += round(seconds * 1e9)

        def set(self):
            self.stopped = True

    monkeypatch.setattr("radar_edge.paced_file.FileSource", Reader)
    monkeypatch.setattr("radar_edge.paced_file.monotonic_ns", lambda: clock[0])
    value = PacedFileSource(
        SourceConfig(path=".local/synthetic.avi", videoId="unit", authorized=True)
    )
    value.stop = Stop()
    return value, clock


def test_pacing_keeps_original_timestamps_and_overwrites_without_repeating(monkeypatch):
    value, clock = source(monkeypatch)
    with value:
        value._produce()
        assert clock[0] == 120_000_000
        last = value.snapshot()
        assert (last.index, last.timestamp_ms, last.timestamp_source) == (2, 80, "MEDIA_PTS")
        assert value.snapshot() is None
        assert value.dropped == 2 and value.published == 3
        assert value.metadata()["fullPlaybackCompleted"]
        assert value.metadata()["frameBufferCapacity"] == 1


def test_slow_decoder_drops_late_frames_instead_of_stretching_time(monkeypatch):
    value, _ = source(monkeypatch, decode_delay=100_000_000)
    with value:
        # Setup/calibration is excluded: start the media clock after that read.
        value.origin_ns = 100_000_000
        value._produce()
        assert value.late_skipped == 2 and value.published == 1
        assert value.snapshot().index == 0
        assert value.snapshot() is None


def test_decoder_failure_is_not_successful_empty_scene(monkeypatch):
    value, _ = source(monkeypatch)
    with value:
        value.reader.read = lambda: (_ for _ in ()).throw(EdgeError("DECODE_ERROR", "failed"))
        value._produce()
        assert value.exhausted and value.error_code == "DECODE_ERROR"
        assert not value.metadata()["fullPlaybackCompleted"]


def test_technical_guard_rejects_webcam_and_delivery_before_opening(monkeypatch):
    monkeypatch.setattr("radar_edge.live.WebcamSource", lambda *_: pytest.fail("webcam opened"))
    c = config()
    c.source = WebcamConfig(kind="WEBCAM", index=0, authorized=True)
    with pytest.raises(EdgeError, match="FILE"):
        run_live(c, technical_stream=True)
    c = config()
    c.events.delivery.enabled = True
    with pytest.raises(EdgeError, match="FILE"):
        run_live(c, technical_stream=True)
    with pytest.raises(ValueError):
        PacedFileSource(SimpleNamespace(kind="WEBCAM"))


def test_early_wait_is_rechecked_and_acquisition_is_actual_publication(monkeypatch):
    value, clock = source(monkeypatch)
    wait = value.stop.wait
    early = [True]

    def wake_early(seconds):
        wait(seconds)
        if early[0] and seconds > 0.003:
            clock[0] -= 3_000_000
            early[0] = False

    value.stop.wait = wake_early
    with value:
        value._produce()
        frame, acquired = value.latest
        assert frame.timestamp_ms == 80
        assert acquired == 80_000_000
        assert clock[0] == 120_000_000
        assert value.metadata()["frameAgeClock"] == "HOST_PUBLICATION_MONOTONIC_NOT_MEDIA_DUE"
