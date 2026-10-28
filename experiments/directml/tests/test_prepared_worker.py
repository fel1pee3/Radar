"""Validate the future physical opt-in without constructing any capture source."""

from types import SimpleNamespace

import pytest
from worker import validate


def config(tmp_path):
    return SimpleNamespace(
        source=SimpleNamespace(kind="WEBCAM", authorized=True),
        model=SimpleNamespace(
            variant="rtmo-s", recovery="RTMO_ADAPTIVE_V3", runtimeProfile="REFERENCE_4_SPIN"
        ),
        events=SimpleNamespace(
            delivery=SimpleNamespace(enabled=False),
            snapshotAuthorized=False,
            outboxPath=str(tmp_path / "new.sqlite"),
        ),
        processing=SimpleNamespace(maxRunSeconds=60),
    )


def test_prepared_validation_only_requires_no_camera(tmp_path):
    validate(config(tmp_path))


def test_prepared_worker_rejects_unbounded_or_changed_reference(tmp_path):
    settings = config(tmp_path)
    settings.processing.maxRunSeconds = None
    with pytest.raises(ValueError, match="bounded"):
        validate(settings)
    settings.processing.maxRunSeconds = 60
    settings.model.recovery = "RTMO_PREFERRED_V1"
    with pytest.raises(ValueError, match="Preserve"):
        validate(settings)


def test_prepared_worker_rejects_http_or_episode_reuse(tmp_path):
    settings = config(tmp_path)
    settings.events.delivery.enabled = True
    with pytest.raises(ValueError, match="HTTP"):
        validate(settings)
    settings.events.delivery.enabled = False
    from pathlib import Path

    Path(settings.events.outboxPath).touch()
    with pytest.raises(ValueError, match="never resume"):
        validate(settings)
