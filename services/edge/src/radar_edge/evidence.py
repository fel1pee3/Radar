"""One event frame, never a later frame; optional JPEG delivery after metadata ACK."""

import json
from datetime import UTC, datetime
from uuid import UUID

import cv2


def encode_snapshot(frame, observation):
    if (
        frame is None
        or frame.index != observation.frameIndex
        or frame.timestamp_ms != observation.timestampMs
    ):
        raise ValueError("Snapshot frame does not match event instant")
    image = frame.bgr
    height, width = image.shape[:2]
    if max(height, width) > 1280:
        image = cv2.resize(
            image,
            (round(width * 1280 / max(height, width)), round(height * 1280 / max(height, width))),
        )
    try:
        success, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    except cv2.error:
        raise ValueError("JPEG encoding failed") from None
    if not success or encoded.nbytes > 2 * 1024 * 1024:
        raise ValueError("JPEG encoding exceeded limit")
    return encoded.tobytes()


def flush_snapshots(delivery, resume_auth=False, limit=1):
    store, now = delivery.store, delivery.clock()
    instant = (
        datetime.fromtimestamp(now, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )
    with store.transaction():
        store.db.execute(
            "UPDATE snapshots SET "
            "jpeg=NULL,status='EXPIRED',error_code='SNAPSHOT_EXPIRED' WHERE "
            "expires_at<=? AND status NOT IN ('DELIVERED','EXPIRED')",
            (instant,),
        )
        if resume_auth:
            store.db.execute(
                "UPDATE snapshots SET status='PENDING',next_attempt=0 WHERE status='AUTH_BLOCKED'"
            )
    if store.db.execute("SELECT 1 FROM snapshots WHERE status='AUTH_BLOCKED' LIMIT 1").fetchone():
        return
    rows = store.db.execute(
        "SELECT s.*,o.ack FROM snapshots s JOIN outbox o USING(event_id) WHERE "
        "s.status='PENDING' AND o.status='DELIVERED' AND s.next_attempt<=? ORDER BY "
        "s.rowid LIMIT ?",
        (now, limit),
    ).fetchall()
    for row in rows:
        status, error = "PENDING", None
        attempts = row["attempts"] + 1
        ack = json.loads(row["ack"])
        try:
            with delivery.client.stream(
                "POST",
                delivery.url + f"/edge/events/{row['event_id']}/snapshot",
                content=row["jpeg"],
                headers={
                    "Authorization": delivery.headers["Authorization"],
                    "Content-Type": "image/jpeg",
                },
            ) as response:
                data = b""
                for chunk in response.iter_bytes():
                    data += chunk
                    if len(data) > 65536:
                        raise ValueError()
                code = response.status_code
                if code in {200, 201}:
                    value = json.loads(data)
                    UUID(value["incidentId"])
                    if (
                        value.get("eventId") != row["event_id"]
                        or value["incidentId"] != ack["incidentId"]
                        or value.get("hash") != row["hash"]
                        or type(value.get("duplicate")) is not bool
                    ):
                        raise ValueError()
                    status = "DELIVERED"
                elif code in {401, 403}:
                    status, error = "AUTH_BLOCKED", f"HTTP_{code}"
                elif code in {408, 429} or 500 <= code <= 599:
                    error = f"HTTP_{code}"
                else:
                    status, error = "PERMANENT_ERROR", f"HTTP_{code}"
        except (ValueError, KeyError, TypeError):
            error = "INVALID_SNAPSHOT_ACK"
        except Exception:
            # No library URL, authorization or body reaches a log.
            error = "SNAPSHOT_TRANSPORT_ERROR"
        with store.transaction():
            store.db.execute(
                "UPDATE snapshots SET "
                "status=?,attempts=?,next_attempt=?,error_code=?,jpeg=CASE WHEN "
                "?='DELIVERED' THEN NULL ELSE jpeg END WHERE event_id=?",
                (
                    status,
                    attempts,
                    now + min(30, 2 ** min(attempts - 1, 5)),
                    error,
                    status,
                    row["event_id"],
                ),
            )
        if status == "DELIVERED":
            store.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        if status == "AUTH_BLOCKED":
            break
