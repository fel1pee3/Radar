"""Native device failures must never silently become an acceleration result."""

import sys
from types import SimpleNamespace

import pytest
import runtime


@pytest.fixture
def fake_native(monkeypatch):
    adapter = {
        "dxgiIndex": 0,
        "softwareAdapter": False,
        "vendorId": "0x1002",
        "deviceId": "0x15e7",
        "direct3d12FeatureLevels": {"12_0": {"supported": True}},
    }

    class Options:
        def add_free_dimension_override_by_name(self, *_):
            pass

    native = SimpleNamespace(
        disable_fallback=lambda: None,
        get_providers=lambda: ["CPUExecutionProvider"],
    )
    ort = SimpleNamespace(
        __version__="1.23.0",
        SessionOptions=Options,
        ExecutionMode=SimpleNamespace(ORT_SEQUENTIAL="SEQUENTIAL"),
        get_available_providers=lambda: ["DmlExecutionProvider", "CPUExecutionProvider"],
        InferenceSession=lambda *_, **__: native,
    )
    monkeypatch.setitem(sys.modules, "onnxruntime", ort)
    monkeypatch.setitem(sys.modules, "hardware", SimpleNamespace(adapters=lambda: [adapter]))
    monkeypatch.setattr(
        runtime.metadata,
        "distributions",
        lambda: [SimpleNamespace(metadata={"Name": "onnxruntime-directml"})],
    )
    from radar_edge import model

    monkeypatch.setattr(model, "verify_model", lambda *_: "checked-model.onnx")
    return ort


def test_cpu_only_initialization_is_rejected_even_if_gpu_was_available(fake_native):
    with pytest.raises(RuntimeError, match="fell back entirely"):
        runtime.create_session("unused", "directml")


def test_missing_provider_stops_before_session_creation(fake_native):
    fake_native.get_available_providers = lambda: ["CPUExecutionProvider"]
    with pytest.raises(RuntimeError, match="provider is unavailable"):
        runtime.create_session("unused", "directml")


def test_conflicting_runtime_distributions_are_rejected(fake_native, monkeypatch):
    monkeypatch.setattr(
        runtime.metadata,
        "distributions",
        lambda: [
            SimpleNamespace(metadata={"Name": name})
            for name in ("onnxruntime", "onnxruntime-directml")
        ],
    )
    with pytest.raises(RuntimeError, match="exactly one"):
        runtime.create_session("unused", "directml")


def test_unmeasured_runtime_version_is_rejected(fake_native):
    fake_native.__version__ = "1.99.0"
    with pytest.raises(RuntimeError, match="requires ORT"):
        runtime.create_session("unused", "directml")
