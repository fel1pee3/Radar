"""Model selection must preserve artifact integrity and the legacy Lite default."""

import hashlib
import json
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from pydantic import ValidationError

from radar_edge import cli, model
from radar_edge.config import ModelConfig
from radar_edge.errors import EdgeError
from radar_edge.estimator import MediaPipeEstimator
from radar_edge.source import Frame, Geometry

REPOSITORY = Path(__file__).resolve().parents[3]


def test_registry_keeps_lite_default_and_versioned_full_artifact():
    lite = model.get_model_spec()
    full = model.get_model_spec("full")
    assert (lite.model_id, lite.sha256, lite.url) == (
        model.MODEL_ID,
        model.MODEL_SHA256,
        model.MODEL_URL,
    )
    assert full.sha256 == "5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1"
    assert full.url == (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/1/pose_landmarker_full.task"
    )
    assert lite.sha256 != full.sha256
    assert lite.default_path != full.default_path
    assert model.MAX_MODEL_BYTES == 20 * 1024 * 1024
    with pytest.raises(EdgeError) as caught:
        model.get_model_spec("unknown")
    assert caught.value.code == "INVALID_MODEL_VARIANT"


def test_full_configuration_requires_explicit_path_and_legacy_remains_lite():
    assert ModelConfig().variant == "lite"
    assert ModelConfig().path == model.get_model_spec("lite").default_path
    assert ModelConfig(path=".local/custom.task").variant == "lite"
    full = ModelConfig(variant="full", path=".local/custom-full.task")
    assert full.variant == "full" and full.path == ".local/custom-full.task"
    for values in ({"variant": "full"}, {"variant": "heavy"}, {"variant": True}):
        with pytest.raises(ValidationError):
            ModelConfig.model_validate(values)


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    contents = {variant: f"test-{variant}-model".encode() for variant in model.MODEL_SPECS}
    specs = {
        variant: replace(spec, sha256=hashlib.sha256(contents[variant]).hexdigest())
        for variant, spec in model.MODEL_SPECS.items()
    }
    monkeypatch.setattr(model, "MODEL_SPECS", specs)
    return contents, specs


@pytest.mark.parametrize("variant", ["lite", "full"])
def test_verification_rejects_other_variant_and_preserves_existing_file(artifacts, variant):
    contents, specs = artifacts
    path = Path(specs[variant].default_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(contents[variant])
    assert model.verify_model(path, variant) == path.resolve()
    wrong_variant = "full" if variant == "lite" else "lite"
    with pytest.raises(EdgeError) as caught:
        model.verify_model(path, wrong_variant)
    assert caught.value.code == "MODEL_HASH_MISMATCH"
    assert path.read_bytes() == contents[variant]


@pytest.mark.parametrize("variant", ["lite", "full"])
def test_fetch_uses_selected_url_destination_and_reuses_valid_artifact(
    artifacts, monkeypatch, variant
):
    contents, specs = artifacts
    requested = []

    @contextmanager
    def response(method, url, **options):
        requested.append((method, url, options))
        result = Mock()
        result.iter_bytes.return_value = [contents[variant]]
        yield result

    monkeypatch.setattr(model.httpx, "stream", response)
    result = model.fetch_model(variant=variant)
    path = Path(specs[variant].default_path)
    assert path.read_bytes() == contents[variant]
    assert result == {
        "status": "ok",
        "modelId": specs[variant].model_id,
        "sha256": specs[variant].sha256,
        "bytes": len(contents[variant]),
    }
    assert requested[0][:2] == ("GET", specs[variant].url)
    assert requested[0][2]["follow_redirects"] is False
    assert model.fetch_model(variant=variant) == result
    assert len(requested) == 1


@pytest.mark.parametrize("oversized", [False, True])
def test_failed_download_keeps_no_model_or_partial_file(artifacts, monkeypatch, oversized):
    _, specs = artifacts
    if oversized:
        specs["full"] = replace(specs["full"], max_bytes=4)

    @contextmanager
    def response(*_args, **_options):
        result = Mock()
        result.iter_bytes.return_value = [b"corrupt-or-oversized"]
        yield result

    monkeypatch.setattr(model.httpx, "stream", response)
    with pytest.raises(EdgeError) as caught:
        model.fetch_model(variant="full")
    assert caught.value.code == ("MODEL_TOO_LARGE" if oversized else "MODEL_HASH_MISMATCH")
    assert not Path(specs["full"].default_path).exists()
    assert not list(Path(".local").rglob("*.part"))


@pytest.mark.parametrize("variant", ["lite", "full"])
def test_existing_wrong_model_cannot_be_overwritten_or_trigger_network(
    artifacts, monkeypatch, variant
):
    _, specs = artifacts
    path = Path(specs[variant].default_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"unrecognized-existing-artifact")
    request = Mock(side_effect=AssertionError("Network must not be used"))
    monkeypatch.setattr(model.httpx, "stream", request)
    with pytest.raises(EdgeError) as caught:
        model.fetch_model(variant=variant)
    assert caught.value.code == "MODEL_HASH_MISMATCH"
    assert path.read_bytes() == b"unrecognized-existing-artifact"
    request.assert_not_called()


@pytest.mark.parametrize(
    ("arguments", "variant", "output"),
    [
        ([], "lite", None),
        (["--variant", "full"], "full", None),
        (["--variant", "full", "--output", ".local/custom.task"], "full", ".local/custom.task"),
    ],
)
def test_cli_selects_variant_without_implicit_lite_output(
    monkeypatch, capsys, arguments, variant, output
):
    fetch = Mock(return_value={"status": "ok"})
    monkeypatch.setattr(model, "fetch_model", fetch)
    monkeypatch.setattr(sys, "argv", ["radar-edge", "model-fetch", *arguments])
    cli.main()
    fetch.assert_called_once_with(output, variant=variant)
    assert json.loads(capsys.readouterr().out)["status"] == "ok"


@pytest.mark.parametrize("variant", ["lite", "full"])
def test_real_selected_artifact_rejects_cross_variant_before_native_load(monkeypatch, variant):
    monkeypatch.chdir(REPOSITORY)
    spec = model.get_model_spec(variant)
    path = Path(spec.default_path)
    if not path.is_file():
        pytest.skip(f"Official {variant} model unavailable; no automatic download")
    wrong_variant = "full" if variant == "lite" else "lite"
    estimator = MediaPipeEstimator(str(path), variant=wrong_variant)
    with pytest.raises(EdgeError) as caught:
        estimator.__enter__()
    assert caught.value.code == "MODEL_HASH_MISMATCH"
    assert estimator.landmarker is None


@pytest.mark.parametrize("variant", ["lite", "full"])
def test_real_selected_model_loads_in_cpu_video_and_reports_its_identity(monkeypatch, variant):
    monkeypatch.chdir(REPOSITORY)
    spec = model.get_model_spec(variant)
    if not Path(spec.default_path).is_file():
        pytest.skip(f"Official {variant} model unavailable; no automatic download")
    frame = Frame(
        0,
        0,
        "MEDIA_PTS",
        np.full((240, 320, 3), 100, dtype=np.uint8),
        Geometry(320, 240, 320, 240, 320, 240, 0),
    )
    with MediaPipeEstimator(spec.default_path, variant=variant) as estimator:
        assert estimator.model_id == spec.model_id
        assert estimator.model_sha256 == spec.sha256
        poses, elapsed = estimator.estimate(frame)
        assert poses == ()
        assert elapsed > 0
    assert estimator.landmarker is None
