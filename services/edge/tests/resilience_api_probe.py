"""Synthetic LIVE observations against the exclusive real Nest/PostgreSQL harness."""

import json
import os
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from time import monotonic_ns, time

import httpx
from temporal_support import GEOMETRY, calibration, observation

from radar_edge.config import EdgeConfig
from radar_edge.delivery import Delivery
from radar_edge.event_runtime import EventRuntime
from radar_edge.freshness import PROCESS_CLOCK_SESSION
from radar_edge.outbox import Outbox


class InjectedClock:
    session_id = PROCESS_CLOCK_SESSION

    def __init__(self):
        self.ns, self.wall = monotonic_ns(), time()

    def monotonic_ns(self):
        return self.ns

    def time(self):
        return self.wall

    def advance(self, ms):
        self.ns += round(ms * 1e6)
        self.wall += ms / 1000


def main():
    if not os.environ.get("RADAR_TEST_CONTAINER", "").startswith("radar-test-"):
        raise RuntimeError("Exclusive test resources required")
    c = EdgeConfig.model_validate(
        {
            "cameraId": os.environ["EDGE_TEST_CAMERA"],
            "source": {"kind": "WEBCAM", "index": 0, "authorized": True},
            "model": {"variant": "full", "path": ".local/models/pose_landmarker_full.task"},
            "events": {"enabled": True, "outboxPath": os.environ["EDGE_TEST_OUTBOX"]},
        }
    )
    action = sys.argv[1]
    injected = InjectedClock() if action == "paused-commit" else None
    if action in {"emit", "lost-ack", "paused-commit"}:
        with EventRuntime(c, calibration(), "SYNTHETIC-LIVE", GEOMETRY, clock=injected) as runtime:
            shift = int(os.environ.get("EDGE_TIME_SHIFT", "0"))
            anchor = (
                (datetime.now(UTC) + timedelta(seconds=shift))
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            runtime.run["anchor"] = anchor
            runtime.store.db.execute(
                "UPDATE executions SET anchor=? WHERE run_id=?", (anchor, runtime.run["run_id"])
            )
            runtime.store.db.commit()
            if injected:
                checkpoint = runtime.store.checkpoint

                def paused_checkpoint(*args, **kwargs):
                    checkpoint(*args, **kwargs)
                    if args[3]:
                        injected.advance(125000)

                runtime.store.checkpoint = paused_checkpoint
            for t in range(0, 2200, 200):
                if injected and t:
                    injected.advance(200)
                runtime.process(
                    replace(observation(t), mode="LIVE", cameraId=c.cameraId),
                    **({"acquired_ns": injected.ns} if injected else {}),
                )
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        before = store.db.execute("SELECT payload FROM outbox").fetchone()[0]
        client = None
        if action == "lost-ack":

            class LostAck:
                def stream(self, *args, **kwargs):
                    with httpx.Client(trust_env=False, timeout=5) as transport:
                        response = transport.request(*args, **kwargs)
                        assert response.status_code == 201
                    raise httpx.ReadTimeout("Synthetic ACK loss after commit")

            client = LostAck()
        sender = Delivery(
            store,
            c.events.delivery,
            client=client,
            clock=lambda: float(os.environ["EDGE_TEST_CLOCK"]),
            jitter=lambda a, b: 1.0,
            **(
                {
                    "freshness_clock": injected.time,
                    "monotonic_clock": injected.monotonic_ns,
                    "clock_session": injected.session_id,
                }
                if injected
                else {}
            ),
        )
        try:
            sender.flush(resume_auth=action == "resume")
        finally:
            sender.close()
        row = store.db.execute("SELECT * FROM outbox").fetchone()
        assert row["payload"] == before
        result = {
            "material": "SYNTHETIC_OBSERVATIONS_NO_CAMERA",
            "status": row["status"],
            "attempts": row["attempts"],
            "errorCode": row["error_code"],
            "eventId": row["event_id"],
            "confirmation": json.loads(row["ack"]) if row["ack"] else None,
            "preservedPayload": True,
            "interruptionInjected": injected is not None,
        }
        print(json.dumps(result))


if __name__ == "__main__":
    main()
