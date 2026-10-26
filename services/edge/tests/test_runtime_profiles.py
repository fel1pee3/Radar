"""CPU experiment boundaries: explicit backend, isolated episodes, unchanged gates."""

from temporal_support import GEOMETRY, calibration, config

from radar_edge.config import ModelConfig
from radar_edge.event_runtime import EventRuntime


def test_diagnostics_keep_episode_identity_but_cpu_experiment_does_not_resume_it():
    c = config()
    c.model = ModelConfig(variant="rtmo-s", path=".local/unit.onnx")
    c.events.policy = {
        "version": "floor-rtmo-score-unit-v1",
        "qualitySource": "RTMO_KEYPOINT_SCORE",
    }
    reference = EventRuntime(c, calibration(), "synthetic", GEOMETRY).fingerprint
    c.diagnostics.profileProcessing = True
    assert EventRuntime(c, calibration(), "synthetic", GEOMETRY).fingerprint == reference
    c.model.runtimeProfile = "CPU_4_SLEEP"
    assert EventRuntime(c, calibration(), "synthetic", GEOMETRY).fingerprint != reference
    c.model.runtimeProfile = "REFERENCE_4_SPIN"
    assert EventRuntime(c, calibration(), "synthetic", GEOMETRY).fingerprint == reference
