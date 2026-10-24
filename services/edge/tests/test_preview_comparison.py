"""Comparison cannot use the wrong video/model or open a WEBCAM source."""

import json
import runpy
from pathlib import Path

import pytest
from temporal_support import observation

from radar_edge.config import EdgeConfig
from radar_edge.model import file_hash, get_model_spec

SCRIPT = Path(__file__).resolve().parents[3] / "scripts/validation/compare-preview.py"


@pytest.mark.parametrize("mismatch", ["video", "model", "camera", "duplicate"])
def test_saved_analysis_identity_guards(tmp_path, monkeypatch, synthetic_video, mismatch):
    monkeypatch.chdir(tmp_path)
    namespace = runpy.run_path(str(SCRIPT))
    config = EdgeConfig.model_validate(
        {
            "cameraId": observation(0).cameraId,
            "source": {
                "kind": "FILE",
                "path": str(synthetic_video),
                "videoId": "synthetic",
                "authorized": True,
            },
        }
    )
    spec = get_model_spec(config.model.variant)
    root = tmp_path / ".local"
    root.mkdir()
    report = {
        "mode": "REPLAY",
        "status": "ok",
        "source": {"sha256": file_hash(synthetic_video)},
        "model": {"id": spec.model_id, "sha256": spec.sha256},
    }
    value = observation(0, modelId=spec.model_id).to_dict()
    if mismatch == "video":
        report["source"]["sha256"] = "0" * 64
    elif mismatch == "model":
        report["model"]["sha256"] = "0" * 64
    elif mismatch == "camera":
        value["cameraId"] = "another-camera"
    lines = [json.dumps(value)] * (2 if mismatch == "duplicate" else 1)
    (root / "report.json").write_text(json.dumps(report), encoding="utf-8")
    (root / "observations.jsonl").write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(ValueError):
        namespace["load_observations"](root / "report.json", config)


def test_comparison_rejects_camera_before_any_source_or_report_is_opened(tmp_path, monkeypatch):
    import yaml

    monkeypatch.chdir(tmp_path)
    namespace = runpy.run_path(str(SCRIPT))
    root = tmp_path / ".local"
    root.mkdir()
    config = {
        "cameraId": observation(0).cameraId,
        "purpose": "RADAR_LIVE_POSE",
        "source": {"kind": "WEBCAM", "index": 0, "authorized": True},
        "model": {"variant": "full", "path": ".local/not-opened.task"},
    }
    path = root / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="never opens a camera"):
        namespace["compare"](str(path), ".local/not-opened.json", ".local/not-created")
    assert not (root / "not-created").exists()
