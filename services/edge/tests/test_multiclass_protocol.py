"""Session grouping and provenance are checked before fitting or opening media."""

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from radar_edge.posture_multiclass_training import MulticlassTrainingManifest, labeled_poses


def protocol():
    clip = {
        "videoId": "a",
        "configuration": ".local/a.yaml",
        "sourceSha256": "1" * 64,
        "observations": ".local/a.jsonl",
        "observationsSha256": "2" * 64,
        "format": "DECISION_TRACE_ESSENTIAL",
        "partition": "TRAIN",
        "groupId": "recording-a",
        "participantId": "same-person",
        "sessionId": "session-a",
        "environmentId": "room-a",
        "permission": "CC-BY-4.0",
        "permissionEvidence": "Source metadata verified locally",
        "annotationsConfirmed": True,
        "classIntervals": [],
    }
    return {
        "schemaVersion": 2,
        "trainingAuthorized": True,
        "version": "test-v3",
        "splitProtocol": "RECORDING_GROUPS_POSSIBLE_SHARED_PARTICIPANTS",
        "clips": [
            clip,
            {
                **clip,
                "videoId": "b",
                "sourceSha256": "3" * 64,
                "partition": "SELECTION",
                "groupId": "recording-b",
                "sessionId": "session-b",
            },
        ],
    }


def test_recording_groups_not_random_frames_even_if_person_shared():
    data = protocol()
    assert MulticlassTrainingManifest.model_validate(data).clips[0].participantId == "same-person"
    for key in ["groupId", "sessionId"]:
        broken = protocol()
        broken["clips"][1][key] = broken["clips"][0][key]
        with pytest.raises(ValidationError, match="leakage"):
            MulticlassTrainingManifest.model_validate(broken)


def test_absent_pose_records_still_must_have_monotonic_timestamps(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".local").mkdir()
    path = Path(".local/a.jsonl")
    path.write_text(
        "\n".join(
            json.dumps({"recordType": "DECISION", "inferenceState": "NO_POSE", "timestampMs": t})
            for t in [200, 100]
        )
    )
    data = protocol()
    data["clips"][0]["observationsSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    clip = MulticlassTrainingManifest.model_validate(data).clips[0]
    with pytest.raises(ValueError, match="Nonmonotonic"):
        list(labeled_poses(clip))
