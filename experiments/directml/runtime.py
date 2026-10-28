"""Isolated RTMO executor helpers. Never selected by the normal worker."""

import ctypes as ct
import json
import os
from collections import Counter
from importlib import metadata
from pathlib import Path
from time import perf_counter

import numpy as np

BACKENDS = ("cpu-reference", "cpu-matched", "directml")


def session_options(ort, backend, profile_prefix=None):
    if backend not in BACKENDS:
        raise ValueError("Unknown experimental backend")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    if backend != "cpu-reference":
        options.enable_mem_pattern = False
        options.add_free_dimension_override_by_name("batch", 1)
    if profile_prefix:
        options.enable_profiling = True
        options.profile_file_prefix = str(profile_prefix)
    return options


def physical_adapter(inventory, index):
    selected = next((a for a in inventory if a["dxgiIndex"] == index), None)
    if (
        selected is None
        or selected["softwareAdapter"]
        or selected["vendorId"] != "0x1002"
        or selected["deviceId"] != "0x15e7"
        or not selected["direct3d12FeatureLevels"].get("12_0", {}).get("supported")
    ):
        raise RuntimeError("Expected the verified AMD 1002:15E7 D3D12 hardware adapter")
    return selected


def create_session(model_path, backend, profile_prefix=None, device_id=0):
    import onnxruntime as ort
    from radar_edge.model import verify_model

    expected = "1.23.2" if backend == "cpu-reference" else "1.23.0"
    if ort.__version__ != expected:
        raise RuntimeError(f"{backend} requires ORT {expected}; found {ort.__version__}")
    installed = [
        d.metadata["Name"]
        for d in metadata.distributions()
        if d.metadata["Name"].lower() in {"onnxruntime", "onnxruntime-gpu", "onnxruntime-directml"}
    ]
    if len(installed) != 1:
        raise RuntimeError("Require exactly one ONNX Runtime distribution per environment")
    provider = ["CPUExecutionProvider"]
    adapter = None
    if backend == "directml":
        from hardware import adapters

        adapter = physical_adapter(adapters(), device_id)
        if "DmlExecutionProvider" not in ort.get_available_providers():
            raise RuntimeError("DirectML provider is unavailable; CPU fallback is not a GPU proof")
        provider = [
            ("DmlExecutionProvider", {"device_id": device_id}),
            "CPUExecutionProvider",
        ]
    options = session_options(ort, backend, profile_prefix)
    checked = verify_model(model_path, "rtmo-s")
    started = perf_counter()
    native = ort.InferenceSession(str(checked), sess_options=options, providers=provider)
    initialization_ms = (perf_counter() - started) * 1000
    native.disable_fallback()
    if backend == "directml" and "DmlExecutionProvider" not in native.get_providers():
        raise RuntimeError("DirectML initialization fell back entirely to CPU")
    return native, {
        "backend": backend,
        "ortVersion": ort.__version__,
        "installedRuntime": installed,
        "actualProviders": native.get_providers(),
        "providerOptions": native.get_provider_options(),
        "adapter": adapter,
        "initializationMs": initialization_ms,
        "executionMode": "ORT_SEQUENTIAL",
        "memoryPattern": backend == "cpu-reference",
        "batchSessionOverride": None if backend == "cpu-reference" else 1,
        "intraOpThreads": 4,
        "interOpThreads": 1,
        "input": [(x.name, x.shape, x.type) for x in native.get_inputs()],
        "output": [(x.name, x.shape, x.type) for x in native.get_outputs()],
        "automaticSessionFallbackDisabled": True,
    }


class HostReadySession:
    """Run() returns materialized CPU arrays. Retain tensors only outside timed persistence."""

    def __init__(self, native):
        self.native = native
        self.calls = []
        self.last_error = None

    def run(self, names, feed):
        started = perf_counter()
        try:
            outputs = self.native.run(names, feed)
            completed = perf_counter()
            ready = [np.array(x, copy=True, order="C") for x in outputs]
            materialized = perf_counter()
        except Exception as exc:
            self.last_error = {"type": type(exc).__name__, "message": str(exc)}
            raise
        if not all(x.dtype == np.float32 for x in ready):
            raise RuntimeError("RTMO CPU outputs must remain float32")
        self.calls.append(
            {
                "sessionRunMs": (completed - started) * 1000,
                "cpuMaterializationMs": (materialized - completed) * 1000,
                "feed": feed,
                "outputs": ready,
            }
        )
        return ready

    def drain(self):
        result, self.calls = self.calls, []
        return result


def profile_summary(path):
    events = json.loads(Path(path).read_text(encoding="utf-8"))
    kernels = [
        e
        for e in events
        if e.get("cat") == "Node"
        and e.get("args", {}).get("provider")
        and e.get("name", "").endswith("_kernel_time")
    ]
    by_provider = {}
    for provider in sorted({e["args"]["provider"] for e in kernels}):
        selected = [e for e in kernels if e["args"]["provider"] == provider]
        by_provider[provider] = {
            "kernelEvents": len(selected),
            "reportedOps": dict(Counter(e["args"].get("op_name") for e in selected)),
            "hostTimelineDurationUs": sum(e.get("dur", 0) for e in selected),
        }
    transfers = [e for e in kernels if "Memcpy" in e["args"].get("op_name", "")]
    fences = [
        e
        for e in events
        if e.get("cat") == "Node"
        and ("_fence_before" in e.get("name", "") or "_fence_after" in e.get("name", ""))
    ]
    gpu = [e for e in kernels if e["args"]["provider"] == "DmlExecutionProvider"]
    compute = [
        e
        for e in gpu
        if "DmlFusedNode" in e["args"].get("op_name", "")
        or e["args"].get("op_name") in {"Conv", "FusedConv", "MatMul", "FusedMatMul", "Gemm"}
    ]
    return {
        "providers": by_provider,
        "gpuComputeProven": bool(compute),
        "gpuFusedPartitionNames": sorted(
            {e["args"]["op_name"] for e in compute if "DmlFusedNode" in e["args"]["op_name"]}
        ),
        "explicitTransfers": {
            "events": len(transfers),
            "types": dict(Counter(e["args"]["op_name"] for e in transfers)),
            "hostTimelineDurationUs": sum(e.get("dur", 0) for e in transfers),
        },
        "fenceEvents": len(fences),
        "fenceHostTimelineDurationUs": sum(e.get("dur", 0) for e in fences),
        "timingLimit": (
            "ORT host timeline; not exclusive GPU hardware kernel time; fused internals opaque"
        ),
    }


def process_memory():
    if os.name != "nt":
        return {"supported": False}

    class Counters(ct.Structure):
        _fields_ = [
            ("cb", ct.c_uint32),
            ("faults", ct.c_uint32),
            ("peakWorkingSet", ct.c_size_t),
            ("workingSet", ct.c_size_t),
            ("quotaPeakPaged", ct.c_size_t),
            ("quotaPaged", ct.c_size_t),
            ("quotaPeakNonPaged", ct.c_size_t),
            ("quotaNonPaged", ct.c_size_t),
            ("pagefile", ct.c_size_t),
            ("peakPagefile", ct.c_size_t),
            ("privateUsage", ct.c_size_t),
        ]

    kernel = ct.WinDLL("kernel32.dll")
    kernel.GetCurrentProcess.restype = ct.c_void_p
    function = ct.WinDLL("psapi.dll").GetProcessMemoryInfo
    function.argtypes = [ct.c_void_p, ct.POINTER(Counters), ct.c_uint32]
    function.restype = ct.c_int
    counters = Counters()
    counters.cb = ct.sizeof(counters)
    if not function(kernel.GetCurrentProcess(), ct.byref(counters), counters.cb):
        raise ct.WinError()
    return {
        "supported": True,
        "workingSetBytes": counters.workingSet,
        "peakWorkingSetBytes": counters.peakWorkingSet,
        "privateUsageBytes": counters.privateUsage,
        "scope": (
            "process memory includes startup/profile buffers; "
            "excludes complete device/driver accounting"
        ),
    }
