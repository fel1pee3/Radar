"""Real loopback HTTP + durable synthetic JPEG. No video, model or device access."""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
from temporal_support import GEOMETRY, calibration, config, observation

from radar_edge.delivery import Delivery
from radar_edge.event_runtime import EventRuntime
from radar_edge.outbox import Outbox

c = config()
c.cameraId = os.environ["EDGE_TEST_CAMERA"]
c.events.outboxPath = os.environ["EDGE_TEST_OUTBOX"]
c.events.evidenceMode = "snapshot"
c.events.snapshotAuthorized = True
c.events.delivery.enabled = True
c.events.delivery.credentialFile = None
Path(c.events.outboxPath).parent.mkdir(parents=True, exist_ok=True)
if sys.argv[1] == "emit":
    with EventRuntime(
        c,
        {**calibration(), "cameraId": c.cameraId},
        "synthetic-jpeg",
        GEOMETRY,
        async_delivery=True,
    ) as runtime:
        for t in range(0, 2400, 200):
            from dataclasses import replace

            o = replace(observation(t), cameraId=c.cameraId)
            runtime.process(
                o,
                SimpleNamespace(
                    index=o.frameIndex,
                    timestamp_ms=o.timestampMs,
                    bgr=np.full((60, 80, 3), 120, dtype=np.uint8),
                ),
            )
with Outbox(c.events.outboxPath, c.cameraId) as store:
    real = httpx.Client(timeout=5, trust_env=False, follow_redirects=False)

    class LostAck:
        def stream(self, *args, **kw):
            if str(args[1]).endswith("/snapshot"):
                response = real.post(args[1], **kw)
                if response.status_code not in {200, 201}:
                    raise ValueError("Snapshot HTTP failed")
                raise httpx.ReadError("SYNTHETIC_ACK_LOSS")
            return real.stream(*args, **kw)

    client = LostAck() if sys.argv[1] == "emit" else real
    try:
        d = Delivery(
            store,
            c.events.delivery,
            client=client,
            clock=lambda: (
                datetime.now(UTC).timestamp() + (1000 if sys.argv[1] == "deliver" else 100)
            ),
        )
        d.flush()
        row = store.items()[0]
        print(
            json.dumps(
                {
                    "eventId": row["eventId"],
                    "status": row["status"],
                    "confirmation": row["confirmation"],
                    "snapshots": store.snapshot_summary(),
                }
            )
        )
    finally:
        real.close()
