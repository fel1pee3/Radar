import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from temporal_support import POLYGON, config, observation

from radar_edge.calibration import calibrate
from radar_edge.evaluation import evaluate_manifest
from radar_edge.model import file_hash
from radar_edge.pipeline import run_pipeline


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    path = Path(".local/synthetic.avi")
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (640, 360))
    assert writer.isOpened()
    for i in range(140):
        writer.write(np.full((360, 640, 3), 60 + i, dtype=np.uint8))
    writer.release()
    c = config()
    c.source.path = str(path)
    points = Path(".local/points.json")
    points.write_text(json.dumps(POLYGON))
    calibrate(c, 0, str(points), True)

    class Estimator:
        def __init__(self, *_):
            self.timestamps = []

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def estimate(self, frame):
            self.timestamps.append(frame.timestamp_ms)
            assert self.timestamps == sorted(set(self.timestamps))
            floor = not 4000 <= frame.timestamp_ms < 10000
            return observation(frame.timestamp_ms, floor).poses, 1.0

    monkeypatch.setattr("radar_edge.pipeline.MediaPipeEstimator", Estimator)
    return c


def test_checkpoint_resume_never_replays_decisions_or_old_rearm_time(prepared):
    c = prepared
    c.processing.maxObservations = 21
    first, code = run_pipeline(c)
    assert code == 0 and first["temporal"]["generatedEvents"] == 1
    original = first["temporal"]["events"][0]
    assert first["runId"] == first["temporal"]["runId"]
    c.processing.maxObservations = 11
    second, code = run_pipeline(c)
    assert code == 0 and second["trackerWarmupObservations"] == 21
    assert first["runId"] == second["runId"]
    assert second["temporal"]["generatedEvents"] == 0 and second["temporal"]["state"] == "REARMING"
    c.processing.maxObservations = None
    final, code = run_pipeline(c)
    assert code == 0 and final["captureState"] == "ENDED"
    assert final["trackerWarmupObservations"] == 32
    assert final["temporal"]["generatedEvents"] == 1
    assert len(final["temporal"]["events"]) == 2 and final["temporal"]["events"][0] == original
    again, code = run_pipeline(c)
    assert code == 0 and again["temporal"]["alreadyCompleted"]
    assert again["metrics"]["analyzedFrames"] == 0 and again["temporal"]["generatedEvents"] == 0
    assert again["temporal"]["events"] == final["temporal"]["events"]


def test_explicit_full_model_is_recorded_and_cannot_resume_lite_execution(prepared):
    from radar_edge.config import ModelConfig
    from radar_edge.model import get_model_spec
    from radar_edge.outbox import Outbox

    c = prepared
    first, code = run_pipeline(c)
    assert code == 0
    c.model = ModelConfig(variant="full", path=".local/models/pose_landmarker_full.task")
    conflict, code = run_pipeline(c)
    assert code == 1 and conflict["error"]["code"] == "SOURCE_CONFIG_CONFLICT"
    c.events.outboxPath = ".local/full-isolated.sqlite"
    full, code = run_pipeline(c)
    assert code == 0
    spec = get_model_spec("full")
    assert full["model"]["id"] == spec.model_id
    assert full["model"]["sha256"] == spec.sha256
    with Outbox(c.events.outboxPath, c.cameraId) as store:
        assert store.events(full["runId"])[0]["versions"]["model"] == spec.model_id
    assert full["temporal"]["generatedEvents"] == first["temporal"]["generatedEvents"]


@pytest.mark.parametrize("speed", [0.5, 2.0])
def test_preview_pause_does_not_speed_up_remaining_replay_or_count_as_floor_time(
    prepared, monkeypatch, speed
):
    clock = [0.0]
    waits = []

    def sleep(seconds):
        waits.append(seconds)
        clock[0] += seconds

    class Preview:
        def __init__(self, enabled, start_paused):
            assert enabled and start_paused
            self.paused_seconds = 0.0

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def show(self, *_):
            if not self.paused_seconds:
                clock[0] += 10
                self.paused_seconds = 10.0
            return True

    monkeypatch.setattr("radar_edge.pipeline.LocalPreview", Preview)
    monkeypatch.setattr("radar_edge.pipeline.perf_counter", lambda: clock[0])
    monkeypatch.setattr("radar_edge.pipeline.sleep", sleep)
    prepared.processing.preview = prepared.processing.previewStartPaused = True
    prepared.processing.replaySpeed = speed
    result, code = run_pipeline(prepared)
    assert code == 0
    assert result["previewPausedSeconds"] == 10.0
    assert sum(waits) == pytest.approx(13.8 / speed)
    assert result["temporal"]["events"][0]["sourceOffsetMs"] == 2000


def test_evaluate_runs_isolated_with_exact_exclusion_overlap_and_no_http(prepared):
    import yaml

    c = prepared
    path = Path(".local/evaluation-config.yaml")
    path.write_text(yaml.safe_dump(c.model_dump()), encoding="utf-8")
    manifest = {
        "videos": [
            {
                "videoId": c.source.videoId,
                "config": str(path),
                "sha256": file_hash(Path(c.source.path)),
                "authorized": True,
                "retention": "OWNER_MANAGED",
                "personPseudonym": "synthetic-01",
                "sessionId": "synthetic-session",
                "environmentId": "fixture",
                "role": "EVALUATION",
                "material": "SYNTHETIC",
                "durationMs": 14000,
                "fps": 10.0,
                "annotationsComplete": True,
                "targets": [
                    {"startMs": 0, "endMs": 3900, "kind": "PERSON_ON_FLOOR"},
                    {"startMs": 10000, "endMs": 13900, "kind": "POSSIBLE_FALL"},
                ],
                "excluded": [{"startMs": 4000, "endMs": 5000}],
            }
        ]
    }
    mf = Path(".local/manifest.json")
    mf.write_text(json.dumps(manifest))
    result, code = evaluate_manifest(mf)
    assert code == 0 and not result["httpDeliveryEnabled"]
    row = result["results"][0]
    assert row["matching"]["PERSON_ON_FLOOR"]["matched"] == 1
    assert row["matching"]["POSSIBLE_FALL"]["matched"] == 1
    assert row["matching"]["PERSON_ON_FLOOR"]["recall"] == 1
    assert row["eligibleMediaMs"] == 12800 and row["observedMediaMs"] == 13800
    assert not Path(c.events.outboxPath).exists()
    second, code = evaluate_manifest(mf)
    assert code == 0 and result["reportPath"] != second["reportPath"]
