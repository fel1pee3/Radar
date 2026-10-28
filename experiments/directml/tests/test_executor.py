"""Safety and measurement boundaries, without GPU, video or camera access."""

import json
from copy import deepcopy
from types import SimpleNamespace

import analyze
import numpy as np
import pytest
import runtime
import stream


class Options:
    def __init__(self):
        self.enable_mem_pattern = True
        self.overrides = {}

    def add_free_dimension_override_by_name(self, name, value):
        self.overrides[name] = value


ORT = SimpleNamespace(
    SessionOptions=Options, ExecutionMode=SimpleNamespace(ORT_SEQUENTIAL="SEQUENTIAL")
)


@pytest.mark.parametrize("backend", ["directml", "cpu-matched"])
def test_matched_cpu_and_dml_have_required_identical_session_options(backend):
    options = runtime.session_options(ORT, backend)
    assert options.execution_mode == "SEQUENTIAL"
    assert not options.enable_mem_pattern
    assert options.overrides == {"batch": 1}
    assert (options.intra_op_num_threads, options.inter_op_num_threads) == (4, 1)


def test_cpu_reference_keeps_original_memory_and_shape_defaults():
    options = runtime.session_options(ORT, "cpu-reference")
    assert options.enable_mem_pattern
    assert options.overrides == {}


def test_software_or_other_adapter_never_counts_as_verified_gpu():
    adapter = {
        "dxgiIndex": 0,
        "softwareAdapter": False,
        "vendorId": "0x1002",
        "deviceId": "0x15e7",
        "direct3d12FeatureLevels": {"12_0": {"supported": True}},
    }
    assert runtime.physical_adapter([adapter], 0) == adapter
    for key, value in [("softwareAdapter", True), ("vendorId", "0x1414"), ("deviceId", "0x0000")]:
        with pytest.raises(RuntimeError):
            runtime.physical_adapter([{**adapter, key: value}], 0)
    with pytest.raises(RuntimeError):
        runtime.physical_adapter([adapter], 1)


def test_host_ready_outputs_are_cpu_copies_and_errors_are_not_hidden():
    array = np.ones((1, 2), dtype=np.float32)
    session = runtime.HostReadySession(SimpleNamespace(run=lambda *_: [array]))
    result = session.run(["output"], {"input": array})
    array[0, 0] = 9
    assert result[0][0, 0] == 1
    assert session.calls[0]["cpuMaterializationMs"] >= 0
    assert len(session.drain()) == 1
    assert session.drain() == []

    def fail(*_):
        raise RuntimeError("device removed")

    session = runtime.HostReadySession(SimpleNamespace(run=fail))
    with pytest.raises(RuntimeError, match="device removed"):
        session.run([], {})
    assert session.last_error["message"] == "device removed"


def test_copy_does_not_accept_unannounced_precision_change():
    session = runtime.HostReadySession(
        SimpleNamespace(run=lambda *_: [np.ones(1, dtype=np.float16)])
    )
    with pytest.raises(RuntimeError, match="float32"):
        session.run([], {})


def kernel(provider, op):
    return {
        "cat": "Node",
        "name": f"{op}_kernel_time",
        "args": {"provider": provider, "op_name": op},
        "dur": 10,
    }


def test_provider_or_copy_alone_does_not_prove_gpu_compute(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(
        json.dumps(
            [
                kernel("CPUExecutionProvider", "Conv"),
                kernel("DmlExecutionProvider", "MemcpyFromHost"),
            ]
        ),
        encoding="utf-8",
    )
    assert not runtime.profile_summary(path)["gpuComputeProven"]


def test_profile_preserves_cpu_ops_and_explicit_transfers(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(
        json.dumps(
            [
                kernel("DmlExecutionProvider", "DmlFusedNode_1_9"),
                kernel("DmlExecutionProvider", "MatMul"),
                kernel("DmlExecutionProvider", "MemcpyToHost"),
                kernel("CPUExecutionProvider", "NonMaxSuppression"),
            ]
        ),
        encoding="utf-8",
    )
    result = runtime.profile_summary(path)
    assert result["gpuComputeProven"]
    assert result["providers"]["CPUExecutionProvider"]["reportedOps"] == {"NonMaxSuppression": 1}
    assert result["explicitTransfers"]["types"] == {"MemcpyToHost": 1}


def row():
    return {
        "poseCount": 1,
        "paths": ["ORIGINAL"],
        "poseState": "ONE_VALID_POSE",
        "poseReasons": [],
        "posture": "LYING",
        "eligible": True,
        "candidate": True,
        "reasons": [],
        "regionState": "ON_FLOOR",
        "boxes": [[0.1, 0.2, 0.5, 0.8, 0.99]],
        "poses": [{"landmarks": [{"index": 11, "x": 0.2, "y": 0.3, "confidence": 0.8}]}],
        "calls": [],
    }


TOLERANCE = {"boxPixelsMaxAbs": 0.5, "pointPixelsMaxAbs": 1, "scoresMaxAbs": 0.005}


def test_small_non_bitwise_error_allowed_but_acceptance_change_reported():
    reference, candidate = row(), row()
    candidate["poses"][0]["landmarks"][0]["x"] += 0.00001
    comparison = analyze.compare_rows(reference, candidate, 640, 360, TOLERANCE)
    assert comparison["behaviorPreserved"]
    assert comparison["withinInvestigationTolerance"]
    candidate["eligible"] = False
    assert analyze.compare_rows(reference, candidate, 640, 360, TOLERANCE)[
        "changedBehaviorFields"
    ] == ["eligible"]


def test_large_joint_or_score_error_fails_numeric_check():
    candidate = row()
    candidate["poses"][0]["landmarks"][0]["x"] += 0.1
    assert not analyze.compare_rows(row(), candidate, 640, 360, TOLERANCE)[
        "withinInvestigationTolerance"
    ]
    candidate = row()
    candidate["boxes"][0][4] -= 0.02
    assert not analyze.compare_rows(row(), candidate, 640, 360, TOLERANCE)[
        "withinInvestigationTolerance"
    ]


def test_same_pixels_required_before_comparing_native_output():
    reference, candidate = row(), row()
    reference["calls"] = [{"pass": "ORIGINAL", "inputTensorSha256": "old"}]
    candidate["calls"] = [{"pass": "ORIGINAL", "inputTensorSha256": "new"}]
    assert not analyze.compare_rows(reference, candidate, 640, 360, TOLERANCE)[
        "sameFeedTensorInputs"
    ]


def test_box_order_is_not_a_behavior_change_in_assessment():
    reference = row()
    reference["boxes"].append([0.6, 0.1, 0.9, 0.8, 0.9])
    reference["poses"].append(deepcopy(reference["poses"][0]))
    reference["poseCount"] = 2
    candidate = deepcopy(reference)
    candidate["boxes"].reverse()
    candidate["poses"].reverse()
    result = analyze.compare_rows(reference, candidate, 640, 360, TOLERANCE)
    assert result["bodyPointMaxDeltaPx"] == 0
    assert result["behaviorPreserved"]


def test_process_local_factory_restores_reference_even_when_run_fails():
    import radar_edge.rtmo as rtmo

    original = rtmo.RtmoEstimator
    with pytest.raises(RuntimeError, match="interrupted"):
        with stream.experimental_factory("directml", []):
            assert rtmo.RtmoEstimator is not original
            raise RuntimeError("interrupted")
    assert rtmo.RtmoEstimator is original


def test_file_guard_precedes_any_session_or_source_open(monkeypatch, tmp_path):
    from radar_edge import config

    monkeypatch.setattr(
        config,
        "load_config",
        lambda _: SimpleNamespace(source=SimpleNamespace(kind="WEBCAM", authorized=True)),
    )
    monkeypatch.setattr(
        stream,
        "create_session",
        lambda *_: pytest.fail("camera must be rejected before session creation"),
    )
    with pytest.raises(ValueError, match="no camera"):
        stream.measure("unused", tmp_path / "must-not-exist", "directml")
    assert not (tmp_path / "must-not-exist").exists()
