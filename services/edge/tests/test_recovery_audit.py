"""Audit input/clock protection; synthetic inputs are not recognition evidence."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "recovery_audit", ROOT / "scripts/validation/audit-rtmo-recovery.py"
)
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


class Sequence:
    def __init__(self, timestamps):
        self.frames = iter(SimpleNamespace(timestamp_ms=t) for t in timestamps)

    def read(self):
        return next(self.frames, None)


def test_exact_frame_does_not_substitute_nearest_or_shift_clock():
    frame = audit_module.exact_frame(Sequence([0, 1000, 1200]), 1200)
    assert frame.timestamp_ms == 1200
    with pytest.raises(ValueError, match="sem aproximação"):
        audit_module.exact_frame(Sequence([0, 1000, 1200]), 1100)
    with pytest.raises(ValueError, match="não encontrado"):
        audit_module.exact_frame(Sequence([0, 1000]), 1200)


def test_webcam_is_rejected_before_any_source_or_model_opens(monkeypatch):
    config = SimpleNamespace(
        source=SimpleNamespace(kind="WEBCAM"), model=SimpleNamespace(variant="rtmo-s")
    )
    monkeypatch.setattr(audit_module, "load_config", lambda _: config)
    monkeypatch.setattr(audit_module, "FileSource", lambda *_: pytest.fail("Source opened"))
    case = audit_module.AuditCase(caseId="guard", configPath="unused", timestampMs=0)
    with pytest.raises(ValueError, match="não abre câmera"):
        audit_module.audit(case, 1)


def test_invalid_repeat_bound_is_rejected_before_config_io(monkeypatch):
    monkeypatch.setattr(audit_module, "load_config", lambda _: pytest.fail("Unexpected IO"))
    case = audit_module.AuditCase(caseId="guard", configPath="unused", timestampMs=0)
    for count in [0, 6]:
        with pytest.raises(ValueError, match="repetições"):
            audit_module.audit(case, count)


@pytest.mark.parametrize("timestamp", [True, -1, 1200.5, "1200"])
def test_manifest_keeps_exact_integer_timestamps(timestamp):
    with pytest.raises(ValidationError):
        audit_module.AuditCase(caseId="guard", configPath="unused", timestampMs=timestamp)
