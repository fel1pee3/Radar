"""Synthetic LIVE observations against the exclusive real Nest/PostgreSQL harness."""

import json
import os
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import httpx
from temporal_support import GEOMETRY, calibration, observation

from radar_edge.config import EdgeConfig
from radar_edge.delivery import Delivery
from radar_edge.event_runtime import EventRuntime
from radar_edge.outbox import Outbox


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
    if action in {"emit", "lost-ack"}:
        with EventRuntime(c, calibration(), "SYNTHETIC-LIVE", GEOMETRY) as runtime:
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
            for t in range(0, 2200, 200):
                runtime.process(replace(observation(t), mode="LIVE", cameraId=c.cameraId))
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
        }
        print(json.dumps(result))


if __name__ == "__main__":
    main()
