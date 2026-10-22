"""Capture adapter faults with synthetic frames; not physical webcam evidence."""

import threading
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from radar_edge.config import WebcamConfig
from radar_edge.webcam import MAX_BYTES, WebcamSource, _capture


def settings(**changes):
    return WebcamConfig(kind="WEBCAM", index=0, authorized=True, reconnectAttempts=0, **changes)


def test_capture_slot_is_bounded_and_contains_latest_acquisition(monkeypatch):
    source = WebcamSource(settings())
    source.pixels = source.context.RawArray("B", MAX_BYTES)
    source.info = source.context.RawArray("d", 14)
    source.lock = threading.Lock()
    source.stop = threading.Event()
    released = []

    class Capture:
        def __init__(self, index, backend):
            assert index == 0 and backend == cv2.CAP_DSHOW

        def isOpened(self):
            return True

        def set(self, *_):
            return True

        def get(self, *_):
            return 30.0

        def read(self):
            count = int(source.info[1]) + 1
            if count == 100:
                source.stop.set()
            return True, np.full((240, 320, 3), count, dtype=np.uint8)

        def release(self):
            released.append(True)

    monkeypatch.setattr("radar_edge.webcam.cv2.VideoCapture", Capture)
    monkeypatch.setattr("radar_edge.webcam._watch_parent", lambda: None)
    _capture(source.config.model_dump(), 640, source.pixels, source.info, source.lock, source.stop)
    assert source.info[1] == 100 and len(source.pixels) == MAX_BYTES
    source.process = SimpleNamespace(is_alive=lambda: True)
    source.started = 0.0
    frame = source.snapshot()
    assert frame.index == 99 and (frame.bgr == 100).all()
    assert frame.timestamp_source == "HOST_MONOTONIC"
    assert source.snapshot() is None  # Same frame is never analyzed twice.
    assert source.dropped == 99 and released == [True]


def test_stale_slot_is_not_returned_as_new_frame(monkeypatch):
    source = WebcamSource(settings())
    source.pixels = source.context.RawArray("B", MAX_BYTES)
    source.info = source.context.RawArray("d", 14)
    source.lock = threading.Lock()
    source.info[0:3] = [1, 1, 1]  # Ancient acquisition, although slot contains pixels.
    source.process = SimpleNamespace(is_alive=lambda: True)
    source.started = 0.0
    assert source.snapshot() is None
    assert source.exhausted and source.state == "ERROR" and source.delivered == 0


@pytest.mark.parametrize("opened,error", [(False, -1), (True, -2)])
def test_open_or_read_failure_is_explicit_and_releases_driver(monkeypatch, opened, error):
    source = WebcamSource(settings())
    released = []
    capture = SimpleNamespace(
        isOpened=lambda: opened,
        set=lambda *_: True,
        get=lambda *_: 30.0,
        read=lambda: (False, None),
        release=lambda: released.append(True),
    )
    monkeypatch.setattr("radar_edge.webcam.cv2.VideoCapture", lambda *_: capture)
    monkeypatch.setattr("radar_edge.webcam._watch_parent", lambda: None)
    info = source.context.RawArray("d", 14)
    _capture(
        source.config.model_dump(),
        640,
        source.context.RawArray("B", MAX_BYTES),
        info,
        threading.Lock(),
        threading.Event(),
    )
    assert info[0] == error and released == [True]


def test_native_hang_is_bounded_by_process_termination():
    source = WebcamSource(settings())
    calls = []
    alive = [True]
    source.stop = threading.Event()
    source.process = SimpleNamespace(
        join=lambda **_: calls.append("join"),
        is_alive=lambda: alive[0],
        terminate=lambda: (alive.__setitem__(0, False), calls.append("terminate")),
        close=lambda: calls.append("close"),
    )
    source.close()
    assert calls == ["join", "terminate", "join", "close"]
    assert source.process is None


def test_abandoned_ipc_lock_becomes_error_instead_of_waiting_forever():
    source = WebcamSource(settings())
    source.process = SimpleNamespace(is_alive=lambda: False)
    source.lock = SimpleNamespace(acquire=lambda **_: False)
    source.started = 0.0
    assert source.snapshot() is None
    assert source.exhausted and source.state == "ERROR"


def test_second_worker_cannot_open_device_even_with_another_camera_id(tmp_path, monkeypatch):
    from radar_edge.errors import EdgeError

    monkeypatch.chdir(tmp_path)
    opened = []
    monkeypatch.setattr(WebcamSource, "_launch", lambda self: opened.append(True))
    with WebcamSource(settings()) as first:
        with pytest.raises(EdgeError) as failure:
            with WebcamSource(settings()):
                pytest.fail("Second source opened")
        assert failure.value.code == "WORKER_LOCKED" and len(opened) == 1
        first.pause()  # Paused worker still owns the bench, though the driver is released.
        with pytest.raises(EdgeError):
            with WebcamSource(settings()):
                pytest.fail("Paused source lost its ownership")
    with WebcamSource(settings()):
        assert len(opened) == 2


def test_capture_recovery_discards_old_slot_and_stops_at_retry_limit(tmp_path, monkeypatch):
    from radar_edge.source import Geometry

    monkeypatch.chdir(tmp_path)
    clock = [100_000_000_000]
    monkeypatch.setattr("radar_edge.webcam.monotonic_ns", lambda: clock[0])
    monkeypatch.setattr("radar_edge.webcam.monotonic", lambda: clock[0] / 1e9)
    c = settings()
    c.reconnectAttempts = 2
    source = WebcamSource(c)
    context = source.context
    processes = []

    class Process:
        def __init__(self, **_):
            self.alive, self.closed = False, False
            processes.append(self)

        def start(self):
            self.alive = True

        def is_alive(self):
            return self.alive

        def join(self, **_):
            self.alive = False

        def close(self):
            self.closed = True

    # Real shared buffers; child driver responses are injected, with no camera.
    source.context = SimpleNamespace(
        RawArray=context.RawArray, Lock=threading.Lock, Event=threading.Event, Process=Process
    )
    geometry = Geometry(320, 240, 320, 240, 320, 240, 0)
    with source:
        clock[0] += 1_000_000
        source.info[:10] = [1, 5, clock[0], *vars(geometry).values()]
        first = source.snapshot()
        old_slot, old_lock = source.info, source.lock
        source.info[0] = -2  # Driver read failed after the last good acquisition.
        clock[0] += 1_000_000_000
        assert source.snapshot() is None and source.reconnects == 1
        assert processes[0].closed and source.info is not old_slot and source.lock is not old_lock
        assert source.snapshot() is None  # No replay of pixels from the failed session.
        source.info[:10] = [1, 1, clock[0], *vars(geometry).values()]
        source.pixels[0] = 99
        recovered = source.snapshot()
        assert recovered.index > first.index and recovered.timestamp_ms > first.timestamp_ms
        assert recovered.bgr[0, 0, 0] == 99
        source.info[0] = -2
        clock[0] += 1_000_000_000
        assert source.snapshot() is None and source.reconnects == 2
        source.info[0] = -2
        clock[0] += 1_000_000_000
        assert source.snapshot() is None and source.exhausted and source.state == "ERROR"
        assert len(processes) == 3  # Initial open plus two retries, never an unbounded loop.
    assert all(p.closed for p in processes)
