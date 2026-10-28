"""Regression reruns must not truncate old logs before refusing old outputs."""

import json

import pytest
from run_functional import execute


@pytest.mark.parametrize("bom", [False, True])
def test_existing_regression_is_rejected_before_truncating_log(tmp_path, bom):
    log = tmp_path / "functional-directml-old.log"
    log.write_text("preserved run", encoding="utf-8")
    protocol = tmp_path / "protocol.json"
    protocol.write_text(
        json.dumps({"outputRoot": str(tmp_path), "cases": []}),
        encoding="utf-8-sig" if bom else "utf-8",
    )
    with pytest.raises(ValueError, match="preservados"):
        execute(protocol, native_worker=True)
    assert log.read_text(encoding="utf-8") == "preserved run"
