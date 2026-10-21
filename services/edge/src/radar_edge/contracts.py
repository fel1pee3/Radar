"""Validação de contratos JSON; sem captura, rede ou inferência."""

import json
import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker

NAMES = {"event-v1", "heartbeat-v1", "incident-action-v1"}
FORMATS = FormatChecker()


@FORMATS.checks("date-time")
def valid_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return True
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


@lru_cache(maxsize=3)
def validator(directory: Path, name: str) -> Draft7Validator:
    if name not in NAMES:
        raise ValueError("Contrato desconhecido.")
    schema = json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema, format_checker=FORMATS)


def finite_json(value: object) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(finite_json(item) for item in value)
    return True


def validate_contract(name: str, value: object, schema_directory: Path) -> bool:
    if not finite_json(value) or not validator(schema_directory, name).is_valid(value):
        return False
    if name == "event-v1":
        indices = [point["index"] for point in value["pose"]]
        if len(set(indices)) != len(indices):
            return False
    return True
