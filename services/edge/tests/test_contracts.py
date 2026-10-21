import json
from pathlib import Path

import pytest

from radar_edge.contracts import validate_contract

ROOT = Path(__file__).resolve().parents[3] / "packages" / "contracts"
CASES = json.loads((ROOT / "fixtures" / "cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_shared_contract(case):
    assert (
        validate_contract(case["schema"], case["value"], ROOT / "src" / "schemas") == case["valid"]
    )


def test_non_finite_number():
    value = json.loads((ROOT / "fixtures" / "event-simulated.json").read_text(encoding="utf-8"))
    value["pose"] = [{"index": 11, "x": float("inf"), "y": 0, "visibility": 1}]
    assert not validate_contract("event-v1", value, ROOT / "src" / "schemas")
