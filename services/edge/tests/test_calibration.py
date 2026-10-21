import json
from dataclasses import asdict, replace
from uuid import uuid4

import pytest

from radar_edge.calibration import check_compatibility, load_calibration, validate_polygon
from radar_edge.errors import EdgeError
from radar_edge.source import Geometry


@pytest.mark.parametrize(
    "points",
    [
        [],
        [[0, 0], [1, 1]],
        [[0, 0], [1, 1], [0.5, 0.5]],
        [[0, 0], [1, 1], [1, 0], [0, 1]],
        [[0, 0], [1, 0], [1, 1], [0, 0]],
        [[0, 0], [1.1, 0], [0, 1]],
        [[0, 0], [True, 0], [0, 1]],
        [[0, 0], [float("nan"), 0], [0, 1]],
        [[0, 0], [0.001, 0], [0, 0.001]],
        [[0, 0], [1, 0], [1, 1], [0.5, 0], [0, 1]],
    ],
)
def test_rejects_unusable_polygons(points):
    with pytest.raises(EdgeError) as caught:
        validate_polygon(points)
    assert caught.value.code == "INVALID_FLOOR_POLYGON"


def test_accepts_simple_concave_polygon_both_directions():
    points = [[0, 0], [1, 0], [0.4, 0.5], [1, 1], [0, 1]]
    assert validate_polygon(points)
    assert validate_polygon(list(reversed(points)))


def calibration_document():
    return {
        "schemaVersion": 1,
        "operatorConfirmed": True,
        "calibrationId": str(uuid4()),
        "cameraId": str(uuid4()),
        "version": 1,
        "geometry": asdict(Geometry(1280, 720, 1280, 720, 640, 360, 0)),
        "floorPolygon": [[0, 0.5], [1, 0.5], [1, 1], [0, 1]],
    }


def test_matching_aspect_can_reuse_scale_but_not_camera_rotation_or_aspect():
    calibration = calibration_document()
    geometry = Geometry(1920, 1080, 1920, 1080, 640, 360, 0)
    check_compatibility(calibration, geometry, calibration["cameraId"])
    for changed in (replace(geometry, rotation=90), replace(geometry, orientedHeight=1200)):
        with pytest.raises(EdgeError) as caught:
            check_compatibility(calibration, changed, calibration["cameraId"])
        assert caught.value.code == "CALIBRATION_INCOMPATIBLE"
    with pytest.raises(EdgeError):
        check_compatibility(calibration, geometry, str(uuid4()))


@pytest.mark.parametrize(
    "field,value",
    [
        ("schemaVersion", True),
        ("operatorConfirmed", False),
        ("version", True),
        ("calibrationId", "../../private"),
        ("geometry", {"width": 0}),
    ],
)
def test_invalid_calibration_metadata_cannot_bypass_validation(tmp_path, monkeypatch, field, value):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / ".local"
    directory.mkdir()
    path = directory / "calibration.json"
    document = calibration_document()
    document[field] = value
    path.write_text(json.dumps(document))
    with pytest.raises(EdgeError):
        load_calibration(path)
