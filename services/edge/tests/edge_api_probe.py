"""Invoked only by the exclusive API integration harness; synthetic observations."""

import json
import os
from dataclasses import replace
from pathlib import Path
from time import time
from uuid import uuid4

import httpx
from temporal_support import GEOMETRY, calibration, config, observation

from radar_edge.config import DeliveryConfig
from radar_edge.delivery import Delivery
from radar_edge.event_runtime import EventRuntime


def main():
    if not os.environ.get("RADAR_TEST_CONTAINER", "").startswith("radar-test-"):
        raise RuntimeError("Exclusive integration harness required")
    c = config()
    c.cameraId = os.environ["EDGE_TEST_CAMERA"]
    c.events.outboxPath = f".local/etapa05/integration/{uuid4()}/outbox.sqlite"
    cal = calibration()
    with EventRuntime(c, cal, "synthetic-integration", GEOMETRY) as runtime:
        for t in range(0, 2400, 200):
            runtime.process(replace(observation(t), cameraId=c.cameraId))
        event = runtime.store.events(runtime.run["run_id"])[0]
        original = runtime.store.db.execute("SELECT payload FROM outbox").fetchone()[0]

        # Real Nest + PostgreSQL commits, then the client loses the ACK.
        class LostAckClient:
            def stream(self, *args, **kwargs):
                with httpx.Client(trust_env=False, timeout=5) as client:
                    response = client.request(*args, **kwargs)
                    assert response.status_code == 201
                raise httpx.ReadTimeout("Injected after server commit")

        sender = Delivery(runtime.store, DeliveryConfig(), LostAckClient())
        assert sender.flush() == {"PENDING": 1}
    # Reopen actual SQLite and restore active episode; do not re-create envelope.
    with EventRuntime(c, cal, "synthetic-integration", GEOMETRY) as runtime:
        assert runtime.engine.state == "ACTIVE"
        for t in range(2400, 4000, 200):
            runtime.process(replace(observation(t), cameraId=c.cameraId))
        assert len(runtime.store.events(runtime.run["run_id"])) == 1
        sender = Delivery(runtime.store, DeliveryConfig(), clock=lambda: time() + 10)
        try:
            assert sender.flush() == {"DELIVERED": 1}
        finally:
            sender.close()
        row = runtime.store.db.execute("SELECT * FROM outbox").fetchone()
        ack = json.loads(row["ack"])
        assert ack["duplicate"] is True and ack["eventId"] == event["eventId"]
        assert row["payload"] == original and row["attempts"] == 2
        assert all(11 <= p["index"] <= 32 for p in event["pose"])
        print(
            json.dumps(
                {
                    "material": "SYNTHETIC_OBSERVATIONS",
                    "eventId": event["eventId"],
                    "incidentId": ack["incidentId"],
                    "outbox": runtime.store.summary(),
                    "duplicateAck": ack["duplicate"],
                    "mode": event["mode"],
                }
            )
        )
    assert Path(c.events.outboxPath).exists()


if __name__ == "__main__":
    main()
