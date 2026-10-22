"""Bounded local HTTP delivery. Never recreate an envelope or log credentials."""

import json
import os
import re
from datetime import UTC, datetime
from time import time
from urllib.parse import urlparse
from uuid import UUID

import httpx

from radar_edge.config import private_path
from radar_edge.errors import EdgeError


def credentials(settings, camera_id):
    try:
        if settings.credentialFile:
            path = private_path(settings.credentialFile)
            if path.stat().st_size > 65536:
                raise ValueError()
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            if value["cameraId"] != camera_id:
                raise ValueError()
            url, token = value["apiUrl"], value["deviceToken"]
        else:
            url, token = os.environ["EDGE_API_URL"], os.environ["EDGE_DEVICE_TOKEN"]
        parsed = urlparse(url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") != "/v1"
        ):
            raise ValueError()
        if not isinstance(token, str) or len(token) < 20 or any(c.isspace() for c in token):
            raise ValueError()
        return url.rstrip("/"), token
    except (ValueError, OSError, KeyError, TypeError):
        raise EdgeError(
            "DELIVERY_CONFIG_INVALID",
            "Confira credencial privada da câmera e URL loopback da API; "
            "nenhum segredo foi exibido.",
        ) from None


def valid_ack(value, event_id, status):
    try:
        UUID(value["incidentId"])
        received = value["receivedAt"]
        return (
            value["eventId"] == event_id
            and value["deliveryClass"] == "TEST"
            and type(value["duplicate"]) is bool
            and value["duplicate"] == (status == 200)
            and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z", received))
            and datetime.fromisoformat(received.replace("Z", "+00:00")).tzinfo == UTC
        )
    except (ValueError, TypeError, KeyError):
        return False


class Delivery:
    def __init__(self, store, settings, client=None, clock=time):
        self.store, self.settings, self.clock = store, settings, clock
        self.url, token = credentials(settings, store.camera_id)
        self.client = client or httpx.Client(
            timeout=settings.timeoutSeconds, trust_env=False, follow_redirects=False
        )
        self.owned = client is None
        self.headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}

    def close(self):
        if self.owned:
            self.client.close()

    def flush(self, resume_auth=False):
        if resume_auth:
            with self.store.transaction():
                self.store.db.execute(
                    "UPDATE outbox SET status='PENDING',next_attempt=0 WHERE status='AUTH_BLOCKED'"
                )
        if self.store.db.execute(
            "SELECT 1 FROM outbox WHERE status='AUTH_BLOCKED' LIMIT 1"
        ).fetchone():
            return self.store.summary()
        rows = self.store.db.execute(
            "SELECT * FROM outbox WHERE status='PENDING' AND next_attempt<=? "
            "ORDER BY rowid LIMIT 20",
            (self.clock(),),
        ).fetchall()
        for row in rows:
            attempts, now = row["attempts"] + 1, self.clock()
            status, error, ack = "PENDING", None, None
            delay = min(60.0, 2.0 ** min(attempts - 1, 6))
            try:
                # Stream and cap even an untrusted/malformed local ACK.
                with self.client.stream(
                    "POST",
                    self.url + "/edge/events",
                    content=row["payload"].encode(),
                    headers=self.headers,
                ) as response:
                    data = b""
                    for part in response.iter_bytes():
                        data += part
                        if len(data) > 65536:
                            raise ValueError()
                    http_status = response.status_code
                    if http_status in {200, 201}:
                        value = json.loads(data)
                        if not valid_ack(value, row["event_id"], http_status):
                            raise ValueError()
                        status, ack = "DELIVERED", value
                    elif http_status in {401, 403}:
                        status, error = "AUTH_BLOCKED", f"HTTP_{http_status}"
                    elif http_status in {408, 429} or 500 <= http_status <= 599:
                        error = f"HTTP_{http_status}"
                        retry = response.headers.get("retry-after", "")
                        if retry.isdigit():
                            delay = max(delay, min(float(retry), 300))
                    else:
                        status, error = "PERMANENT_ERROR", f"HTTP_{http_status}"
            except httpx.HTTPError:
                error = "TRANSPORT_ERROR"
            except (ValueError, TypeError, KeyError):
                error = "INVALID_ACK"
            self.store.update_delivery(row["event_id"], status, attempts, now + delay, error, ack)
            if status == "AUTH_BLOCKED":
                break
        return self.store.summary()
