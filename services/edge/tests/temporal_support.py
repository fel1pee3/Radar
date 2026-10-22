"""Deterministic synthetic observations, never evidence of real perception."""

from dataclasses import replace
from uuid import uuid4

from radar_edge.config import EdgeConfig
from radar_edge.model import MODEL_ID
from radar_edge.observations import Landmark, Observation, Pose
from radar_edge.source import Geometry

CAMERA = "11111111-1111-4111-8111-111111111111"
CALIBRATION = "22222222-2222-4222-8222-222222222222"
POLYGON = [[0.05, 0.6], [0.95, 0.6], [0.95, 0.98], [0.05, 0.98]]
GEOMETRY = Geometry(640, 360, 640, 360, 640, 360, 0)


def observation(t, floor=True, **changes):
    if floor:
        coordinates = {
            11: (0.2, 0.7),
            12: (0.22, 0.74),
            23: (0.5, 0.7),
            24: (0.52, 0.74),
            25: (0.7, 0.7),
            26: (0.72, 0.74),
            27: (0.9, 0.7),
            28: (0.92, 0.74),
        }
    else:
        coordinates = {
            11: (0.45, 0.2),
            12: (0.55, 0.2),
            23: (0.45, 0.45),
            24: (0.55, 0.45),
            25: (0.45, 0.65),
            26: (0.55, 0.65),
            27: (0.45, 0.9),
            28: (0.55, 0.9),
        }
    points = tuple(
        Landmark(i, *coordinates.get(i, (0.5, 0.7 if floor else 0.5)), None, 0.99, 0.99)
        for i in range(11, 33)
    )
    base = Observation(
        1,
        str(uuid4()),
        CAMERA,
        "REPLAY",
        t // 200,
        t,
        "MEDIA_PTS",
        640,
        360,
        0,
        (Pose(points),),
        1,
        "ONE_VALID_POSE",
        (),
        100.0,
        1.0,
        MODEL_ID,
        CALIBRATION,
        1,
        str(t),
    )
    return replace(base, **changes)


def config():
    return EdgeConfig.model_validate(
        {
            "cameraId": CAMERA,
            "source": {
                "path": ".local/fake.avi",
                "videoId": "synthetic-temporal",
                "authorized": True,
            },
            "events": {"enabled": True, "outboxPath": ".local/test.sqlite"},
        }
    )


def calibration():
    return {"floorPolygon": POLYGON, "calibrationId": CALIBRATION, "version": 1}
