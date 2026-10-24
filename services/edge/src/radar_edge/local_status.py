"""Local telemetry files: bounded Windows sharing retries, no private error text."""

import json
from time import sleep
from uuid import uuid4

from radar_edge.errors import EdgeError


def safe_diagnostic(failure):
    """Keep type, OS codes and our code locations; never messages, paths or locals."""
    locations = []
    trace = failure.__traceback__
    while trace is not None:
        module = trace.tb_frame.f_globals.get("__name__", "")
        if module.startswith("radar_edge."):
            locations.append(
                {
                    "module": module,
                    "function": trace.tb_frame.f_code.co_name,
                    "line": trace.tb_lineno,
                }
            )
        trace = trace.tb_next
    return {
        "exceptionType": type(failure).__name__,
        "errno": getattr(failure, "errno", None),
        "winerror": getattr(failure, "winerror", None),
        "locations": locations[-8:],
    }


def publish_status(target, status):
    """Readers see complete JSON; retry only brief Windows rename/share conflicts."""
    temporary = target.with_name(f"{target.stem}.{uuid4()}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(status, indent=2), encoding="utf-8")
        for attempt in range(5):
            try:
                temporary.replace(target)
                return attempt
            except PermissionError as failure:
                if getattr(failure, "winerror", None) not in {5, 32} or attempt == 4:
                    raise
                sleep(0.02)
    except OSError as failure:
        raise EdgeError(
            "LOCAL_STATUS_WRITE_ERROR",
            "Falha ao atualizar o diagnóstico local; confira acesso e espaço em .local.",
        ) from failure
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass  # Best effort for private telemetry only; original I/O failure stays visible.
