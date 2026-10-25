"""Reproducible fitting and split isolation; synthetic data cannot certify accuracy."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from pydantic import ValidationError
from temporal_support import GEOMETRY
from test_posture_candidate import candidate, rtmo_observation

from radar_edge.errors import EdgeError
from radar_edge.posture_training import TrainingManifest, train_posture


def manifest_files(tmp_path, monkeypatch):
    c, cal = candidate(tmp_path, monkeypatch)
    cal.update(schemaVersion=1, operatorConfirmed=True, cameraId=c.cameraId)
    cal["geometry"] = asdict(GEOMETRY)
    Path(".local/calibration.json").write_text(json.dumps(cal))
    c.calibrationPath = ".local/calibration.json"
    c.posture = c.posture.model_copy(update={"method": "BASELINE"})
    c.events.policy = {"version": "floor-rtmo-score-v0.1", "qualitySource": "RTMO_KEYPOINT_SCORE"}
    clips = []
    for index, floor in enumerate([False, True]):
        source = Path(f".local/clip-{index}.bin")
        source.write_bytes(f"synthetic material {index}".encode())
        c.source.path = str(source)
        config_path = Path(f".local/config-{index}.json")
        # The actual baseline settings are intentionally free of candidate context.
        raw = c.model_dump()
        raw.pop("posture")
        config_path.write_text(json.dumps(raw))
        observations = Path(f".local/observations-{index}.jsonl")
        observations.write_text(
            "".join(
                json.dumps(rtmo_observation(t, floor).to_dict()) + "\n" for t in range(0, 6000, 200)
            )
        )
        clips.append(
            {
                "videoId": f"synthetic-{index}",
                "configuration": str(config_path),
                "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "observations": str(observations),
                "observationsSha256": hashlib.sha256(observations.read_bytes()).hexdigest(),
                "partition": "TRAIN",
                "participantId": "synthetic-train",
                "sessionId": None,
                "environmentId": "synthetic-room",
                "permission": "OWNER_RECORDED_AUTHORIZED",
                "permissionEvidence": "Synthetic test fixture only; no real accuracy claim.",
                "annotationsConfirmed": True,
                "floorIntervals": [{"startMs": 0, "endMs": 6000}] if floor else [],
            }
        )
    clips.append(
        {
            **clips[0],
            "videoId": "never-read-selection",
            "configuration": ".local/absent",
            "sourceSha256": "f" * 64,
            "observations": ".local/never-read.jsonl",
            "observationsSha256": "e" * 64,
            "partition": "SELECTION",
            "participantId": "synthetic-selection",
        }
    )
    return {
        "schemaVersion": 1,
        "trainingAuthorized": True,
        "version": "synthetic-training-v1",
        "installationId": "synthetic-room",
        "sessionIndependenceEstablished": False,
        "clips": clips,
    }


def test_training_is_deterministic_and_never_opens_selection_inputs(tmp_path, monkeypatch):
    manifest = manifest_files(tmp_path, monkeypatch)
    path = Path(".local/manifest.json")
    path.write_text(json.dumps(manifest))
    first = train_posture(str(path), ".local/trained-a.json")
    second = train_posture(str(path), ".local/trained-b.json")
    assert first["sha256"] == second["sha256"]
    assert first["trainingObservations"] >= 20
    assert not first["cameraOpened"] and not first["approved"]
    with pytest.raises(EdgeError) as failure:
        train_posture(str(path), ".local/trained-a.json")
    assert failure.value.code == "POSTURE_OUTPUT_EXISTS"


def test_participant_or_known_session_leakage_is_rejected(tmp_path, monkeypatch):
    manifest = manifest_files(tmp_path, monkeypatch)
    manifest["clips"][-1]["participantId"] = "synthetic-train"
    with pytest.raises(ValidationError, match="leakage"):
        TrainingManifest.model_validate(manifest)
    manifest["clips"][-1]["participantId"] = "synthetic-selection"
    for clip in manifest["clips"]:
        clip["sessionId"] = "same-session"
    with pytest.raises(ValidationError, match="leakage"):
        TrainingManifest.model_validate(manifest)


def test_explicit_new_session_split_can_evaluate_same_person_without_identity_generalization(
    tmp_path, monkeypatch
):
    manifest = manifest_files(tmp_path, monkeypatch)
    manifest["splitStrategy"] = "SESSION"
    manifest["sessionIndependenceEstablished"] = True
    for clip in manifest["clips"]:
        clip["participantId"] = "same-founder"
        clip["sessionId"] = "recording-a" if clip["partition"] == "TRAIN" else "recording-b"
    assert TrainingManifest.model_validate(manifest).splitStrategy == "SESSION"
