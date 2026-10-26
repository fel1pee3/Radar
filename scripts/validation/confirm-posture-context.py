"""Run only after visually confirming the fixed camera floor; never opens camera."""

import argparse
import json

from radar_edge.errors import EdgeError
from radar_edge.posture_context import confirm_context

parser = argparse.ArgumentParser(
    description="Confirma contexto V3 e preserva fila anterior."
)
parser.add_argument("--config", required=True)
parser.add_argument("--confirmed", action="store_true")
args = parser.parse_args()
try:
    print(json.dumps(confirm_context(args.config, args.confirmed)))
except (EdgeError, OSError, ValueError) as error:
    print(
        json.dumps(
            {
                "status": "error",
                "code": getattr(error, "code", "CONTEXT_PREPARATION_FAILED"),
                "message": getattr(
                    error, "message", "Confira configuracao e acesso local."
                ),
            }
        )
    )
    raise SystemExit(1) from None
