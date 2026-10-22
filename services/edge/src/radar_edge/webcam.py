"""Native Windows camera in an isolated process; one shared latest-frame slot."""

import ctypes
import hashlib
import multiprocessing as mp
import os
import threading
from dataclasses import asdict
from datetime import UTC, datetime
from time import monotonic, monotonic_ns

import cv2
import numpy as np

from radar_edge.config import private_path
from radar_edge.errors import EdgeError
from radar_edge.outbox import FileLock
from radar_edge.source import Frame, Geometry, orient_frame

MAX_BYTES = 640 * 2048 * 3


def _watch_parent():
    parent = mp.parent_process()
    while parent is not None and parent.is_alive():
        threading.Event().wait(0.5)
    if parent is not None:
        os._exit(0)  # Also releases the driver if read() is blocked when the owner dies.


def _capture(settings, max_width, pixels, info, lock, stop):
    threading.Thread(target=_watch_parent, daemon=True).start()
    capture = None
    try:
        backend = {"DSHOW": cv2.CAP_DSHOW, "MSMF": cv2.CAP_MSMF}[settings["backend"]]
        capture = cv2.VideoCapture(settings["index"], backend)
        if not capture.isOpened():
            info[0] = -1
            return
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
        capture.set(cv2.CAP_PROP_FPS, settings["fps"])
        info[11] = capture.get(cv2.CAP_PROP_FPS)
        count = 0
        last_digest = None
        identical_since = None
        while not stop.is_set():
            ok, image = capture.read()
            acquired = monotonic_ns()
            if not ok or image is None:
                info[0] = -2
                return
            if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                info[0] = -3
                return
            image, geometry = orient_frame(image, settings["rotation"], max_width)
            if image.nbytes > MAX_BYTES:
                info[0] = -3
                return
            count += 1
            digest = hashlib.sha256(image.tobytes()).hexdigest()
            if digest != last_digest:
                identical_since = acquired
            last_digest = digest
            if lock.acquire(timeout=0.1):
                try:
                    np.frombuffer(pixels, dtype=np.uint8)[: image.size] = image.reshape(-1)
                    info[1:10] = [count, acquired, *asdict(geometry).values()]
                    info[12] = identical_since
                    info[13] = float(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).mean())
                    info[0] = 1
                finally:
                    lock.release()
    except Exception:
        info[0] = -2  # Never serialize driver exceptions or private device details.
    finally:
        if capture is not None:
            capture.release()


class WebcamSource:
    def __init__(self, config, max_width=640):
        self.config, self.max_width = config, max_width
        self.context = mp.get_context("spawn")
        self.process = None
        self.geometry = None
        self.frames_read = self.delivered = self.dropped = 0
        self.reconnects = 0
        self.last_index = 0
        self.index_offset = 0
        self.last_acquired_ns = None
        self.origin_ns = monotonic_ns()
        self.start_utc = datetime.now(UTC)
        self.state = "WARMING_UP"
        self.error_code = None
        self.exhausted = False
        self._last_reconnect = 0.0
        self.device_lock = None

    def _launch(self):
        self.pixels = self.context.RawArray(ctypes.c_ubyte, MAX_BYTES)
        self.info = self.context.RawArray(ctypes.c_double, 14)
        self.lock = self.context.Lock()
        self.stop = self.context.Event()
        self.process = self.context.Process(
            target=_capture,
            args=(
                self.config.model_dump(),
                self.max_width,
                self.pixels,
                self.info,
                self.lock,
                self.stop,
            ),
            daemon=True,
        )
        self.started = monotonic()
        self.process.start()

    def __enter__(self):
        if not self.config.authorized:
            raise EdgeError("CAMERA_AUTHORIZATION_REQUIRED", "Autorize a webcam na configuração.")
        # Keep ownership while paused as well; two logical cameras must not
        # compete for the same physical device in this single-source bench.
        self.device_lock = FileLock(private_path(".local/edge-locks/webcam-bench.lock"))
        self.device_lock.__enter__()
        try:
            self._launch()
        except BaseException:
            self.close()
            raise
        return self

    def _release(self):
        if self.process is not None:
            self.stop.set()
            self.process.join(timeout=1)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=2)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=1)
            self.process.close()
            self.process = None

    def snapshot(self):
        if self.process is None:
            return None
        now = monotonic()
        if not self.lock.acquire(timeout=0.05):
            elapsed = (
                (monotonic_ns() - self.last_acquired_ns) / 1e9
                if self.last_acquired_ns
                else now - self.started
            )
            timeout = (
                self.config.frameTimeoutSeconds
                if self.last_acquired_ns
                else self.config.openTimeoutSeconds
            )
            if elapsed > timeout:
                self.state, self.error_code = "ERROR", "CAPTURE_ERROR"
                self._recover(self.last_index, now)
            return None
        try:
            values = list(self.info)
            state, count, acquired = int(values[0]), int(values[1]), int(values[2])
            age = (monotonic_ns() - acquired) / 1e9 if acquired else now - self.started
            timed_out = age > (
                self.config.frameTimeoutSeconds if acquired else self.config.openTimeoutSeconds
            )
            bad = state < 0 or timed_out or not self.process.is_alive()
            if bad:
                self.state = "ERROR"
                self.error_code = "CAMERA_OPEN_FAILED" if state == -1 else "CAPTURE_ERROR"
                image = None
            elif count <= self.last_index:
                return None
            else:
                geometry = Geometry(*map(int, values[3:10]))
                if self.geometry is not None and geometry != self.geometry:
                    self.exhausted = True
                    raise EdgeError("SOURCE_GEOMETRY_CHANGED", "Enquadramento mudou; recalibre.")
                self.geometry = geometry
                image = (
                    np.frombuffer(self.pixels, dtype=np.uint8)[
                        : geometry.width * geometry.height * 3
                    ]
                    .reshape(geometry.height, geometry.width, 3)
                    .copy()
                )
        finally:
            self.lock.release()
        if bad:
            self._recover(count, now)
            return None
        self.dropped += max(0, count - self.last_index - 1)
        self.last_index = count
        self.frames_read = self.index_offset + count
        self.delivered += 1
        self.last_acquired_ns = acquired
        self.state, self.error_code = "RUNNING", None
        return Frame(
            self.frames_read - 1,
            (acquired - self.origin_ns) // 1000000,
            "HOST_MONOTONIC",
            image,
            self.geometry,
        )

    def _recover(self, count, now):
        if self.reconnects < self.config.reconnectAttempts:
            if now - self._last_reconnect >= self.config.reconnectDelaySeconds:
                self.index_offset += max(self.last_index, count)
                self._release()
                self.reconnects += 1
                self.last_index = 0
                self._last_reconnect = now
                self._launch()  # New IPC; never reuse locks from a killed process.
        else:
            self.exhausted = True

    def read(self):
        deadline = monotonic() + self.config.openTimeoutSeconds
        while monotonic() < deadline:
            frame = self.snapshot()
            if frame is not None:
                return frame
            if self.exhausted:
                break
            self.stop.wait(0.02)
        raise EdgeError(
            self.error_code or "FRAME_TIMEOUT",
            "Webcam sem frame novo. Confira índice, privacidade do Windows, "
            "tampa física e aplicativos que possam ocupar a câmera.",
        )

    def metadata(self):
        return {
            "kind": "WEBCAM",
            "mode": "LIVE",
            "index": self.config.index,
            "backend": self.config.backend,
            "fpsMetadata": float(self.info[11]) if hasattr(self, "info") else None,
            "geometry": asdict(self.geometry) if self.geometry else None,
            "framesAcquired": self.frames_read,
            "framesConsumed": self.delivered,
            "framesOverwritten": self.dropped,
            "reconnects": self.reconnects,
            "captureState": self.state,
            "errorCode": self.error_code,
        }

    def close(self):
        try:
            self._release()
        finally:
            if self.device_lock is not None:
                self.device_lock.__exit__(None, None, None)
                self.device_lock = None

    def pause(self):
        self.index_offset += self.last_index
        self.last_index = 0
        self._release()
        self.state = "PAUSED"

    def resume(self):
        self.exhausted = False
        self._launch()
        self.state = "WARMING_UP"

    def __exit__(self, *_):
        self.close()


def probe(config, seconds=5.0, preview=False):
    from radar_edge.preview import fit_display

    start = monotonic()
    first = last = None
    first_index = last_index = None
    count = 0
    with WebcamSource(config.source, config.processing.maxWidth) as source:
        try:
            while monotonic() - start < seconds + config.source.openTimeoutSeconds:
                frame = source.snapshot()
                if frame is None:
                    if source.exhausted:
                        raise EdgeError(
                            source.error_code, "Webcam indisponível; confira índice/permite uso."
                        )
                    source.stop.wait(0.01)
                    continue
                first = frame.timestamp_ms if first is None else first
                last = frame.timestamp_ms
                first_index = frame.index if first_index is None else first_index
                last_index = frame.index
                count += 1
                if preview:
                    image = fit_display(frame.bgr)
                    cv2.putText(
                        image,
                        "LIVE | Diagnostico local | Q/Esc sair",
                        (8, 24),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )
                    cv2.imshow("Radar - diagnostico webcam LIVE", image)
                    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                        break
                if last - first >= seconds * 1000:
                    break
            result = source.metadata()
        finally:
            if preview:
                cv2.destroyAllWindows()
    if not count:
        raise EdgeError("CAMERA_NO_FRAMES", "Nenhum frame físico foi recebido.")
    return {
        "status": "ok",
        "command": "probe",
        **result,
        "sampledFrames": count,
        "captureFpsMeasured": (last_index - first_index) * 1000 / (last - first)
        if last > first
        else None,
        "consumedFpsMeasured": (count - 1) * 1000 / (last - first) if last > first else None,
        "framesSaved": False,
        "inferenceExecuted": False,
    }
