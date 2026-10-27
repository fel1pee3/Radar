"""Technical 1x FILE stream: monotonic pacing, one latest slot, never a webcam."""

import hashlib
import threading
from datetime import UTC, datetime
from time import monotonic_ns

import cv2

from radar_edge.errors import EdgeError
from radar_edge.source import FileSource


class PacedFileSource:
    def __init__(self, config, max_width=640):
        if config.kind != "FILE":
            raise ValueError("Technical stream requires an authorized FILE")
        self.reader = FileSource(config, max_width)
        self.config = config
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = None
        self.latest = self.first = None
        self.last_index = -1
        self.frames_read = self.delivered = self.dropped = 0
        self.published = self.late_skipped = 0
        self.last_acquired_ns = self.origin_ns = 0
        self.start_utc = datetime.now(UTC)
        self.geometry = None
        self.info = [0.0] * 14
        self.ended = self.exhausted = False
        self.full_playback_completed = False
        self.error_code = None
        self.reconnects = 0
        self.max_publish_lag_ms = 0.0
        self.paused = False

    def __enter__(self):
        if not self.config.authorized:
            raise EdgeError("VIDEO_AUTHORIZATION_REQUIRED", "Autorize o arquivo local.")
        self.reader.__enter__()
        self.first = self.reader.read()
        if self.first is None:
            raise EdgeError("FILE_INVALID", "Arquivo sem primeiro frame.")
        self.geometry = self.first.geometry
        return self

    def read(self):
        # Calibration only, before starting the clock. Never an observation.
        return self.first

    def start_stream(self):
        if self.thread is not None:
            raise ValueError("A FILE stream cannot be restarted or looped")
        self.origin_ns = monotonic_ns()
        self.start_utc = datetime.now(UTC)
        self.thread = threading.Thread(target=self._produce, daemon=True)
        self.thread.start()

    def _wait_until(self, due):
        # A timeout can wake early; never publish a future media deadline.
        while not self.stop.is_set():
            remaining = due - monotonic_ns()
            if remaining <= 0:
                return
            self.stop.wait(remaining / 1e9)

    def _produce(self):
        try:
            frame = self.first
            previous_digest = identical_since = None
            period_ns = round(1e9 / self.reader.fps) if self.reader.fps else 40_000_000
            while frame is not None and not self.stop.is_set():
                due = self.origin_ns + frame.timestamp_ms * 1_000_000
                self._wait_until(due)
                if self.stop.is_set():
                    break
                lag = max(0, monotonic_ns() - due) / 1e6
                self.max_publish_lag_ms = max(self.max_publish_lag_ms, lag)
                self.frames_read += 1
                if lag * 1e6 > period_ns or self.paused:
                    self.late_skipped += 1
                else:
                    with self.lock:
                        acquired = monotonic_ns()
                        digest = hashlib.sha256(frame.bgr.tobytes()).hexdigest()
                        if digest != previous_digest:
                            identical_since = acquired
                        previous_digest = digest
                        if self.latest is not None and self.latest[0].index > self.last_index:
                            self.dropped += 1
                        self.latest = (frame, acquired)
                        self.published += 1
                        self.info[0] = 1
                        self.info[1] = self.frames_read
                        self.info[2] = acquired
                        self.info[12] = identical_since
                        self.info[13] = float(cv2.cvtColor(frame.bgr, cv2.COLOR_BGR2GRAY).mean())
                frame = self.reader.read()
            duration = self.reader.metadata().get("durationMsEstimate")
            if duration:
                self._wait_until(self.origin_ns + round(duration * 1e6))
            self.full_playback_completed = frame is None and not self.stop.is_set()
        except EdgeError as error:
            self.error_code = error.code
            self.exhausted = True
        except Exception:
            self.error_code = "FILE_STREAM_ERROR"
            self.exhausted = True
        finally:
            self.ended = True

    def snapshot(self):
        with self.lock:
            if self.latest is None or self.latest[0].index <= self.last_index:
                return None
            frame, acquired = self.latest
            self.last_index = frame.index
            self.last_acquired_ns = acquired
            self.delivered += 1
            return frame

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def metadata(self):
        return {
            **self.reader.metadata(),
            "executionKind": "TECHNICAL_PACED_FILE_NOT_WEBCAM",
            "playbackRate": 1,
            "frameAgeClock": "HOST_PUBLICATION_MONOTONIC_NOT_MEDIA_DUE",
            "framesDecoded": self.frames_read,
            "framesPublished": self.published,
            "framesConsumed": self.delivered,
            "framesOverwritten": self.dropped,
            "framesSkippedProducerLate": self.late_skipped,
            "maximumProducerLagMs": self.max_publish_lag_ms,
            "frameBufferCapacity": 1,
            "frameBufferPolicy": "LATEST_ONLY_OVERWRITE_NOT_FIFO",
            "hostMonotonicOriginNs": self.origin_ns,
            "hostOriginUtc": self.start_utc.isoformat(),
            "reconnects": 0,
            "errorCode": self.error_code,
            "ended": self.ended,
            "fullPlaybackCompleted": self.full_playback_completed,
        }

    def close(self):
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                raise EdgeError("FILE_STREAM_STOP_TIMEOUT", "Decoder do arquivo não encerrou.")
        self.reader.close()

    def __exit__(self, *_):
        self.close()
