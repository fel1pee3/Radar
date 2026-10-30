"""Synthetic session ownership/controller tests; no GPU or recognition claim."""

import json

import numpy as np
import pytest
from test_posture_candidate import rtmo_observation
from test_preferred_rtmo import frame

from radar_edge.config import ModelConfig
from radar_edge.directml import DirectMlEstimator
from radar_edge.directml_reacquiring import DirectMlReacquiringEstimator
from radar_edge.errors import EdgeError
from radar_edge.estimator import create_estimator, executed_model_metadata
from radar_edge.model import get_model_spec
from radar_edge.reacquiring_rtmo import ReacquiringRtmoEstimator
from radar_edge.rtmo import RtmoEstimator


def fake_gpu(monkeypatch, tmp_path):
    calls = {"gpuEnter": 0, "profileEnd": 0}

    class Session:
        def run(self, names, inputs):
            assert names == ["dets", "keypoints"]
            assert inputs["input"].shape == (1, 3, 640, 640)
            assert inputs["input"].dtype == np.float32
            calls["sessionRun"] = calls.get("sessionRun", 0) + 1
            dets = np.array([[[80, 80, 420, 320, 0.99]]], dtype=np.float32)
            points = np.zeros((1, 1, 17, 3), dtype=np.float32)
            for index in range(17):
                points[0, 0, index] = (
                    100 + 10 * calls["sessionRun"] + index,
                    50 + index * 10,
                    0.99,
                )
            return [dets, points]

        def end_profiling(self):
            calls["profileEnd"] += 1
            path = tmp_path / "gpu-profile.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "cat": "Node",
                            "name": "gpu_kernel_time",
                            "args": {"provider": "DmlExecutionProvider", "op_name": "DmlFusedNode"},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            return str(path)

    session = Session()

    def gpu_enter(owner):
        calls["gpuEnter"] += 1
        owner.session = session
        owner.executor_metadata = {
            "requested": "DIRECTML",
            "runtime": "onnxruntime-directml",
            "version": "1.23.0",
            "providers": ["DmlExecutionProvider", "CPUExecutionProvider"],
            "adapter": {"vendorId": "0x1002", "deviceId": "0x15e7"},
        }
        return owner

    def cpu_enter(_):
        pytest.fail("The reacquisition controller must not initialize a CPU session.")

    monkeypatch.setattr(DirectMlEstimator, "__enter__", gpu_enter)
    monkeypatch.setattr(RtmoEstimator, "__enter__", cpu_enter)
    return session, calls


def test_one_gpu_session_delegates_current_processing_and_final_profile(monkeypatch, tmp_path):
    session, calls = fake_gpu(monkeypatch, tmp_path)
    estimator = create_estimator(
        "never-opened",
        "rtmo-s",
        "RTMO_PREFERRED_V2",
        executor="DIRECTML",
        operator_profile_prefix=tmp_path / "operators",
    )
    assert isinstance(estimator, DirectMlReacquiringEstimator)
    assert estimator.session is None and calls["gpuEnter"] == 0
    assert estimator._directml.profile_prefix == tmp_path / "operators"
    native = rtmo_observation(0).poses[0]

    def infer(_pixels):
        assert estimator._processing.session is session
        estimator._processing.perception_attempts.append(
            {
                "poseCount": 1,
                "usableEssentialCount": 8,
            }
        )
        return (native,), (), 0.99

    monkeypatch.setattr(estimator._processing, "infer_image", infer)
    with estimator as active:
        assert active is estimator
        assert estimator.session is estimator._directml.session is session
        assert estimator._processing.executor_metadata is estimator.executor_metadata
        poses, _ = estimator.estimate(frame(0))
        assert poses == (native,)
        assert estimator.perception_passes == ("ORIGINAL",)
        assert estimator.preferred == "ORIGINAL"
        assert estimator.perception_attempts[0]["strategy"]["strategy"] == "RTMO_PREFERRED_V2"
        estimator.reset_preference("SOURCE_RECONNECT")
        assert estimator.preferred is None
        estimator.estimate(frame(200))
        assert estimator.perception_passes[0] == "ORIGINAL"
        summary = estimator.strategy_summary()
        assert summary["strategy"] == "RTMO_PREFERRED_V2"
        assert summary["limits"] == {
            "maxCalls": 2,
            "extraCallStartMs": 220,
            "fullScanMs": 800,
            "leaseMs": 1600,
            "searchMs": 1600,
            "searchAnalyses": 8,
        }

    assert estimator.session is None and estimator._directml.session is None
    assert calls == {"gpuEnter": 1, "profileEnd": 1}
    info = executed_model_metadata(get_model_spec("rtmo-s"), estimator, "DIRECTML")
    assert info["delegate"] == "DIRECTML"
    assert info["executor"]["operatorProfile"]["gpuComputeProven"]
    assert info["executor"]["operatorProfile"]["nodeEventsByProvider"] == {
        "DmlExecutionProvider": 1,
    }
    estimator.close()
    assert calls["profileEnd"] == 1


def test_gpu_failure_is_propagated_without_cpu_substitution(monkeypatch):
    calls = []

    def failing_gpu(_):
        calls.append("gpu")
        raise EdgeError("DIRECTML_INITIALIZATION_FAILED", "synthetic GPU failure")

    def cpu_enter(_):
        pytest.fail("CPU substitution is forbidden.")

    monkeypatch.setattr(DirectMlEstimator, "__enter__", failing_gpu)
    monkeypatch.setattr(RtmoEstimator, "__enter__", cpu_enter)
    estimator = create_estimator("never-opened", "rtmo-s", "RTMO_PREFERRED_V2", executor="DIRECTML")
    with pytest.raises(EdgeError) as failure:
        estimator.__enter__()
    assert failure.value.code == "DIRECTML_INITIALIZATION_FAILED"
    assert calls == ["gpu"] and estimator.session is None
    assert estimator.executor_metadata is None


def test_explicit_allowlist_preserves_default_adaptive_and_cpu_routes():
    ModelConfig(
        variant="rtmo-s",
        path="never-opened.onnx",
        executor="DIRECTML",
        recovery="RTMO_PREFERRED_V2",
    )
    assert isinstance(
        create_estimator("never-opened", "rtmo-s", "RTMO_ADAPTIVE_V3", executor="DIRECTML"),
        DirectMlEstimator,
    )
    assert isinstance(
        create_estimator("never-opened", "rtmo-s", "RTMO_PREFERRED_V2"), ReacquiringRtmoEstimator
    )
    assert ModelConfig().executor == "CPU"
    for recovery, runtime in (
        ("RTMO_PREFERRED_V1", "REFERENCE_4_SPIN"),
        ("RTMO_PREFERRED_V2", "CPU_2_SPIN"),
    ):
        with pytest.raises(EdgeError):
            create_estimator(
                "never-opened",
                "rtmo-s",
                recovery,
                runtime_profile=runtime,
                executor="DIRECTML",
            )
        with pytest.raises(ValueError):
            ModelConfig(
                variant="rtmo-s",
                path="never-opened.onnx",
                executor="DIRECTML",
                recovery=recovery,
                runtimeProfile=runtime,
            )


def test_unchanged_inference_path_uses_the_shared_gpu_session(monkeypatch, tmp_path):
    session, calls = fake_gpu(monkeypatch, tmp_path)
    with create_estimator(
        "never-opened", "rtmo-s", "RTMO_PREFERRED_V2", executor="DIRECTML"
    ) as estimator:
        first, _ = estimator.estimate(frame(0))
        second, _ = estimator.estimate(frame(200))
        assert estimator.session is session
        assert calls["sessionRun"] == 2
        assert len(first) == len(second) == 1
        assert second[0].landmarks[0].x > first[0].landmarks[0].x
        assert estimator.perception_passes == ("ORIGINAL",)
        assert "sessionRunMs" in estimator.perception_attempts[0]
        assert estimator.perception_attempts[0]["strategy"]["calls"] == 1
    assert estimator.session is None
