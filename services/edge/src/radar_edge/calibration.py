"""A normalized operator-selected polygon, never an automatically inferred floor."""

import json
import math
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from radar_edge.config import EdgeConfig, private_path
from radar_edge.errors import EdgeError
from radar_edge.source import FileSource, Geometry


def validate_polygon(points) -> list[tuple[float, float]]:
    def invalid():
        raise EdgeError(
            "INVALID_FLOOR_POLYGON",
            "Marque 3–32 pontos distintos dentro da imagem, "
            "sem cruzar arestas e com área utilizável.",
        )

    if not isinstance(points, (list, tuple)) or not 3 <= len(points) <= 32:
        invalid()
    converted = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            invalid()
        if any(
            isinstance(v, bool)
            or not isinstance(v, (float, int))
            or not math.isfinite(v)
            or not 0 <= v <= 1
            for v in point
        ):
            invalid()
        converted.append(tuple(float(value) for value in point))
    if len(set(converted)) != len(converted):
        invalid()
    area = (
        abs(
            sum(
                x * converted[(i + 1) % len(converted)][1]
                - converted[(i + 1) % len(converted)][0] * y
                for i, (x, y) in enumerate(converted)
            )
        )
        / 2
    )
    if area < 0.0001:
        invalid()

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a, b, p):
        return abs(cross(a, b, p)) < 1e-12 and all(
            min(a[i], b[i]) - 1e-12 <= p[i] <= max(a[i], b[i]) + 1e-12 for i in (0, 1)
        )

    n = len(converted)
    for i in range(n):
        a, b = converted[i], converted[(i + 1) % n]
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            c, d = converted[j], converted[(j + 1) % n]
            if (cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0) or any(
                (on_segment(a, b, c), on_segment(a, b, d), on_segment(c, d, a), on_segment(c, d, b))
            ):
                invalid()
    return converted


def load_calibration(filename: str | Path) -> dict:
    try:
        path = private_path(filename)
        if path.stat().st_size > 65536:
            raise ValueError()
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if (
            type(value["schemaVersion"]) is not int
            or value["schemaVersion"] != 1
            or value["operatorConfirmed"] is not True
        ):
            raise ValueError()
        if (
            not isinstance(value["version"], int)
            or isinstance(value["version"], bool)
            or value["version"] < 1
        ):
            raise ValueError()
        validate_polygon(value["floorPolygon"])
        UUID(value["calibrationId"])
        UUID(value["cameraId"])
        geometry = Geometry(**value["geometry"])
        if any(
            type(size) is not int or not 1 <= size <= 65536
            for key, size in asdict(geometry).items()
            if key != "rotation"
        ):
            raise ValueError()
        if type(geometry.rotation) is not int or geometry.rotation not in (0, 90, 180, 270):
            raise ValueError()
        return value
    except EdgeError:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        raise EdgeError(
            "CALIBRATION_REQUIRED", "Calibração ausente ou inválida. Execute radar-edge calibrate."
        ) from None


def check_compatibility(calibration: dict, geometry: Geometry, camera_id: str):
    old = Geometry(**calibration["geometry"])
    if (
        calibration["cameraId"] != camera_id
        or old.rotation != geometry.rotation
        or old.orientedHeight <= 0
        or old.orientedWidth <= 0
        or abs(
            (old.orientedWidth / old.orientedHeight)
            / (geometry.orientedWidth / geometry.orientedHeight)
            - 1
        )
        > 0.001
    ):
        raise EdgeError(
            "CALIBRATION_INCOMPATIBLE", "Câmera, orientação ou proporção mudou. Recalibre o piso."
        )


def calibrate(
    config: EdgeConfig, frame_ms: int, points_path: str | None, confirm_floor: bool
) -> dict:
    from radar_edge.preview import select_floor

    if config.source.kind == "WEBCAM":
        from radar_edge.webcam import WebcamSource

        source_type = WebcamSource
    else:
        source_type = FileSource
    with source_type(config.source, config.processing.maxWidth) as source:
        while True:
            frame = source.read()
            if frame is None:
                raise EdgeError(
                    "CALIBRATION_FRAME_MISSING", "O instante escolhido ultrapassa o vídeo."
                )
            if frame.timestamp_ms >= frame_ms:
                break
        if points_path:
            if not confirm_floor:
                raise EdgeError(
                    "FLOOR_CONFIRMATION_REQUIRED",
                    "Use --confirm-floor somente para pontos escolhidos por você sobre esse frame.",
                )
            try:
                points = json.loads(private_path(points_path).read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                raise EdgeError(
                    "INVALID_FLOOR_POLYGON", "Confira o JSON privado de pontos normalizados."
                ) from None
        else:
            points = select_floor(frame)
        points = validate_polygon(points)
        path = private_path(config.calibrationPath)
        previous = load_calibration(path) if path.exists() else None
        result = {
            "schemaVersion": 1,
            "calibrationId": previous["calibrationId"] if previous else str(uuid4()),
            "version": previous["version"] + 1 if previous else 1,
            "cameraId": config.cameraId,
            "createdAt": datetime.now(UTC).isoformat(),
            "geometry": asdict(frame.geometry),
            "floorPolygon": points,
            "operatorConfirmed": True,
            "selectionMethod": "MANUAL_POINTS" if points_path else "LOCAL_GUI",
            "frameIndex": frame.index,
            "timestampMs": frame.timestamp_ms,
            "timestampSource": frame.timestamp_source,
            "videoId": getattr(config.source, "videoId", None),
            "sourceKind": config.source.kind,
            "deviceIndex": getattr(config.source, "index", None),
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve previous revisions as private metadata, never the source frame.
    if previous:
        archive = path.with_name(
            f"{path.stem}.{previous['calibrationId']}.v{previous['version']}.json"
        )
        if not archive.exists():
            archive.write_text(json.dumps(previous, indent=2), encoding="utf-8")
    temporary = path.with_name(f"{path.name}.{uuid4()}.tmp")
    try:
        temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "status": "ok",
        "command": "calibrate",
        "calibrationId": result["calibrationId"],
        "version": result["version"],
        "frameSaved": False,
    }
