"""Current health only; independent heartbeat and event-delivery threads."""

import copy
import json
import sqlite3
import threading
from collections import deque
from time import monotonic, monotonic_ns

import httpx

from radar_edge.contracts import validate_contract
from radar_edge.delivery import Delivery, credentials
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import SCHEMAS, WORKER_VERSION
from radar_edge.outbox import Outbox, utc_now


class LiveHealth:
    def __init__(self, config, run_id, calibration, clock=monotonic):
        self.config, self.clock = config, clock
        self.lock = threading.RLock()
        self.started = clock()
        self.last_frame = None
        self.last_inference = None
        self.times = deque(maxlen=300)
        self.capture = "RUNNING"
        self.flags = {"FRAME_TIMEOUT"}
        self.inference = "WARMING_UP"
        self.pending = 0
        self.run_id = run_id
        self.sequence = 0
        self.versions = {
            "worker": WORKER_VERSION,
            "model": config.model.variant,
            "policy": "floor-v0.1",
            "calibration": "unconfigured",
        }
        from radar_edge.model import get_model_spec

        self.versions["model"] = get_model_spec(config.model.variant).model_id
        from radar_edge.policy import configured_policy

        self.versions["policy"] = configured_policy(config.events.policy).version
        if calibration:
            self.versions["calibration"] = (
                f"{calibration['calibrationId']}-v{calibration['version']}"
            )
        self.network = {"heartbeat": "NOT_SENT", "events": "NOT_SENT"}
        self.run_conflict = False
        self.revision = 0
        self.source = None
        self.dark_since = None

    def update(self, capture=None, flags=None, inference=None):
        with self.lock:
            before = (self.capture, self.flags.copy(), self.inference)
            if capture is not None:
                self.capture = capture
            if flags is not None:
                self.flags = set(flags)
            if inference is not None:
                self.inference = inference
            if before != (self.capture, self.flags, self.inference):
                self.revision += 1

    def observation(self, o, features=None):
        with self.lock:
            now = self.clock()
            self.last_frame = now
            self.last_inference = now
            self.times.append((now, o.timestampMs))
            flags = set(features.reasons if features else ()) & {
                "FRAME_TIMEOUT",
                "LOW_FPS",
                "LOW_LIGHT",
                "POSSIBLE_FROZEN",
            }
            self.update(flags=flags, inference=o.inferenceState)

    def snapshot(self):
        with self.lock:
            now = self.clock()
            flags = self.flags.copy()
            age = None if self.last_frame is None else max(0, round((now - self.last_frame) * 1000))
            if self.source is not None and self.capture == "RUNNING":
                acquired = int(self.source.info[2])
                age = max(0, (monotonic_ns() - acquired) // 1000000) if acquired else None
                if self.source.info[0] < 0 or self.source.exhausted:
                    flags.add("CAPTURE_ERROR")
                if acquired and (monotonic_ns() - self.source.info[12]) / 1e9 >= 10:
                    flags.add("POSSIBLE_FROZEN")
                dark = self.source.info[13] < 25 and acquired
                self.dark_since = (
                    (self.dark_since if self.dark_since is not None else now) if dark else None
                )
                if self.dark_since is not None and now - self.dark_since >= 2:
                    flags.add("LOW_LIGHT")
            if self.capture == "RUNNING" and (age is None or age > 2000):
                flags.add("FRAME_TIMEOUT")
            recent = [(wall, t) for wall, t in self.times if now - wall <= 5]
            fps = 0.0
            if len(recent) > 1:
                span = recent[-1][0] - recent[0][0]
                if self.config.source.kind == "FILE":
                    span = (recent[-1][1] - recent[0][1]) / 1000
                fps = min(1000, (len(recent) - 1) / span) if span > 0 else 0.0
            if (
                self.config.source.kind == "WEBCAM"
                and self.capture == "RUNNING"
                and now - self.started >= 5
                and (
                    len(recent) < 2
                    or fps < 2
                    or self.last_inference is None
                    or now - self.last_inference > 2
                )
            ):
                flags.add("LOW_FPS")
            return {
                "schemaVersion": 1,
                "cameraId": self.config.cameraId,
                "runId": self.run_id,
                "mode": "LIVE" if self.config.source.kind == "WEBCAM" else "REPLAY",
                "sequence": self.sequence,
                "sentAt": utc_now(),
                "captureState": self.capture,
                "qualityFlags": sorted(flags),
                "analysisFps": fps,
                "outboxPending": self.pending,
                "lastFrameAgeMs": age,
                "inferenceState": self.inference,
                "versions": copy.copy(self.versions),
            }


class NetworkWorker:
    """Each thread owns its SQLite/HTTP objects; no inference thread performs HTTP."""

    def __init__(self, config, health):
        self.config, self.health = config, health
        self.stop = threading.Event()
        self.final_ack = threading.Event()
        self.threads = []

    def __enter__(self):
        if self.config.events.delivery.enabled:
            for target in (self._heartbeat_loop, self._delivery_loop):
                t = threading.Thread(target=target, daemon=True)
                self.threads.append(t)
                t.start()
        return self

    def _heartbeat_loop(self):
        try:
            url, token = credentials(self.config.events.delivery, self.config.cameraId)
        except EdgeError:
            self.health.network["heartbeat"] = "DELIVERY_CONFIG_INVALID"
            self.health.run_conflict = True
            return
        last_sent, revision = -10.0, -1
        with httpx.Client(
            timeout=self.config.events.delivery.timeoutSeconds,
            trust_env=False,
            follow_redirects=False,
        ) as client:
            while not self.stop.is_set():
                now = monotonic()
                value = self.health.snapshot()
                signature = (
                    value["captureState"],
                    tuple(value["qualityFlags"]),
                    value["inferenceState"],
                )
                due = now - last_sent >= 5 or signature != revision
                if due and now - last_sent >= 0.25:
                    self.health.sequence += 1
                    value["sequence"] = self.health.sequence
                    if not validate_contract("heartbeat-v1", value, SCHEMAS):
                        self.health.network["heartbeat"] = "HEARTBEAT_CONTRACT_ERROR"
                        return
                    try:
                        with client.stream(
                            "POST",
                            url + "/edge/heartbeat",
                            json=value,
                            headers={"Authorization": "Bearer " + token},
                        ) as response:
                            data = b""
                            for part in response.iter_bytes():
                                data += part
                                if len(data) > 65536:
                                    raise ValueError()
                            status = response.status_code
                            if status == 200:
                                ack = json.loads(data)
                                accepted = (
                                    ack.get("accepted") is True and ack.get("ignored") is False
                                )
                                self.health.network["heartbeat"] = (
                                    "ACCEPTED" if accepted else "RUN_RETIRED"
                                )
                                self.health.run_conflict = not accepted
                                if accepted and value["captureState"] in {"ENDED", "ERROR"}:
                                    self.final_ack.set()
                            elif status == 409:
                                self.health.run_conflict = True
                                self.health.network["heartbeat"] = "RUN_CONFLICT"
                            elif status in (401, 403):
                                self.health.network["heartbeat"] = "AUTH_BLOCKED"
                                self.health.run_conflict = True
                                return
                            else:
                                self.health.network["heartbeat"] = f"HTTP_{status}"
                    except (httpx.HTTPError, ValueError, TypeError):
                        self.health.network["heartbeat"] = "TRANSPORT_OR_ACK_ERROR"
                    last_sent, revision = now, signature
                self.stop.wait(0.1)

    def _delivery_loop(self):
        try:
            with Outbox(self.config.events.outboxPath, self.config.cameraId) as store:
                sender = Delivery(store, self.config.events.delivery)
                try:
                    last_prune = -60.0
                    while not self.stop.is_set():
                        if monotonic() - last_prune >= 60:
                            from radar_edge.retention import cleanup_diagnostics

                            cleanup_diagnostics(self.config.diagnostics.outputDirectory)
                            store.prune_confirmed(
                                self.config.events.delivery.confirmedRetentionDays
                            )
                            last_prune = monotonic()
                        summary = sender.flush(limit=1)
                        self.health.pending = sum(v for k, v in summary.items() if k != "DELIVERED")
                        self.health.network["events"] = summary
                        self.stop.wait(0.25)
                finally:
                    sender.close()
        except EdgeError as failure:
            self.health.network["events"] = failure.code
        except (sqlite3.Error, OSError):
            self.health.update(capture="ERROR", flags={"STORAGE_FULL"})
            self.health.network["events"] = "STORAGE_ERROR"

    def close(self, final=True):
        if self.stop.is_set():
            return
        if final and self.threads:
            if self.health.capture != "ERROR":
                self.health.update(capture="ENDED")
            self.final_ack.wait(timeout=self.config.events.delivery.timeoutSeconds + 0.5)
        self.stop.set()
        for thread in self.threads:
            thread.join(timeout=self.config.events.delivery.timeoutSeconds + 0.5)

    def __exit__(self, error_type, error, traceback):
        if error_type is not None and error_type is not KeyboardInterrupt:
            code = (
                error.code
                if isinstance(error, EdgeError)
                else "STORAGE_ERROR"
                if isinstance(error, sqlite3.Error)
                else "MODEL_ERROR"
            )
            flag = (
                "STORAGE_FULL"
                if code in {"STORAGE_ERROR", "STORAGE_FULL"}
                else "CALIBRATION_REQUIRED"
                if code.startswith("CALIBRATION")
                else "MODEL_ERROR"
                if code.startswith("MODEL")
                else "CAPTURE_ERROR"
            )
            self.health.update(capture="ERROR", flags={flag})
        self.close()
