"""Current observations and conservative transport hints; immutable envelopes stay intact."""

from datetime import datetime
from time import monotonic_ns, time
from uuid import uuid4

PROCESS_CLOCK_SESSION = str(uuid4())
MAX_FRAME_AGE_MS = 2000
DELIVERY_CURRENT_MS = 120000
CLOCK_TOLERANCE_MS = 30000


class ProcessingClock:
    session_id = PROCESS_CLOCK_SESSION

    def monotonic_ns(self):
        return monotonic_ns()

    def time(self):
        return time()


def delivery_freshness(payload, timing, now, now_ns, session_id):
    """A hint can only downgrade API classification, never upgrade an old receipt.

    A new process cannot prove continuity of its predecessor's monotonic clock.
    Preserve that uncertainty for a pending LIVE event; replay remains TEST.
    Native event timestamps are never changed.
    """
    if payload["mode"] != "LIVE":
        return "TEST", None, None
    detected = datetime.fromisoformat(payload["detectedAt"].replace("Z", "+00:00")).timestamp()
    occurred = datetime.fromisoformat(payload["occurredAt"].replace("Z", "+00:00")).timestamp()
    age = (now - detected) * 1000
    uncertain = detected > now + CLOCK_TOLERANCE_MS / 1000 or occurred > detected
    reason = "EVENT_CLOCK_INCOHERENT" if uncertain else None
    if timing:
        saved = timing["timing"]
        if saved["sessionId"] == session_id:
            elapsed = (now_ns - saved["recordedMonotonicNs"]) / 1e6
            wall_elapsed = (now - saved["recordedWallSeconds"]) * 1000
            age = max(age, saved["frameAgeAtRecordMs"] + elapsed)
            if elapsed < 0 or abs(wall_elapsed - elapsed) > CLOCK_TOLERANCE_MS:
                uncertain, reason = True, "WALL_MONOTONIC_DIVERGENCE"
        elif age <= DELIVERY_CURRENT_MS:
            uncertain, reason = True, "PROCESS_RESTART_CLOCK_NOT_VERIFIED"
        if timing.get("deliveryHint") == "CLOCK_UNCERTAIN":
            uncertain, reason = True, "PREVIOUS_CLOCK_UNCERTAINTY"
        if timing.get("deliveryHint") == "DELAYED":
            age = max(age, DELIVERY_CURRENT_MS + 1)
    if uncertain:
        return "CLOCK_UNCERTAIN", reason, age
    if age > DELIVERY_CURRENT_MS:
        return "DELAYED", "EVENT_EXCEEDS_CURRENT_WINDOW", age
    return "CURRENT", None, age
