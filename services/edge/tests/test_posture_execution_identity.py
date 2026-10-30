"""New context options preserve old queue identity unless explicitly enabled."""

from copy import deepcopy

import pytest
from temporal_support import GEOMETRY, config
from test_posture_candidate import rtmo_observation
from test_posture_multiclass import classifier

from radar_edge import event_runtime
from radar_edge.errors import EdgeError
from radar_edge.event_runtime import EventRuntime, posture_execution_context


def settings_and_calibration(tmp_path, monkeypatch, method):
    model, cal, policy = classifier(tmp_path, monkeypatch, 3)
    c = config()
    c.model.variant = "rtmo-s"
    c.model.path = ".local/not-opened.onnx"
    c.posture = model.settings
    c.posture.method = method
    c.events.policy = policy.to_dict()
    if method == "MULTICLASS_CONTEXT_V4":
        c.events.policy["version"] = "floor-rtmo-score-posture-context-v4-synthetic"
    return c, cal


def historical_posture_fields(settings):
    """The original config serializer had no fields for the two new options."""
    value = settings.model_dump()
    value.pop("floorContextStrategy")
    value.pop("postureAmbiguityStrategy")
    return value


@pytest.mark.parametrize("method", ["MULTICLASS_BODY_V3", "MULTICLASS_CONTEXT_V4"])
def test_default_options_resume_original_execution_and_checkpoint(tmp_path, monkeypatch, method):
    c, cal = settings_and_calibration(tmp_path, monkeypatch, method)
    # Populate a queue using the exact posture dictionary shape before the two
    # options existed. The new code must resume it without changing its identity.
    with monkeypatch.context() as original:
        original.setattr(event_runtime, "posture_execution_context", historical_posture_fields)
        with EventRuntime(c, cal, "same-video-bytes", GEOMETRY) as run:
            run.process(rtmo_observation(0))
            row = dict(run.store.db.execute("SELECT * FROM executions").fetchone())
            assert row["frame_index"] == 0

    with EventRuntime(c, cal, "same-video-bytes", GEOMETRY) as resumed:
        assert resumed.resumed
        assert resumed.run["run_id"] == row["run_id"]
        assert resumed.run["fingerprint"] == row["fingerprint"]
        assert resumed.run["anchor"] == row["anchor"]
        assert resumed.run["frame_index"] == 0
        assert resumed.run["timestamp_ms"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("floorContextStrategy", "ARTICULATED_ARM_V1"),
        ("postureAmbiguityStrategy", "NON_FLOOR_GROUP_V1"),
    ],
)
def test_opt_in_changes_identity_and_refuses_legacy_queue(tmp_path, monkeypatch, field, value):
    c, cal = settings_and_calibration(tmp_path, monkeypatch, "MULTICLASS_CONTEXT_V4")
    with EventRuntime(c, cal, "same-video-bytes", GEOMETRY) as run:
        run.process(rtmo_observation(0))
        original = dict(run.store.db.execute("SELECT * FROM executions").fetchone())

    changed = deepcopy(c)
    setattr(changed.posture, field, value)
    assert posture_execution_context(changed.posture)[field] == value
    with pytest.raises(EdgeError) as failure:
        with EventRuntime(changed, cal, "same-video-bytes", GEOMETRY):
            pytest.fail("An opt-in must not silently reuse an earlier episode.")
    assert failure.value.code == "SOURCE_CONFIG_CONFLICT"

    with EventRuntime(c, cal, "same-video-bytes", GEOMETRY) as preserved:
        assert preserved.resumed
        assert dict(preserved.store.db.execute("SELECT * FROM executions").fetchone()) == original


def test_only_new_unused_fields_are_removed(tmp_path, monkeypatch):
    c, _ = settings_and_calibration(tmp_path, monkeypatch, "MULTICLASS_CONTEXT_V4")
    value = posture_execution_context(c.posture)
    assert value == historical_posture_fields(c.posture)
    assert value["excludedRegions"] == [] and value["supportRegions"] == []
    assert value["operatorConfirmed"] is True
