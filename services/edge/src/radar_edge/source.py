"""Sequential local decoding, explicit orientation and media-clock sampling."""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from radar_edge.config import SourceConfig
from radar_edge.errors import EdgeError


@dataclass(frozen=True)
class Geometry:
    rawWidth: int
    rawHeight: int
    orientedWidth: int
    orientedHeight: int
    width: int
    height: int
    rotation: int


@dataclass(frozen=True)
class Frame:
    index: int
    timestamp_ms: int
    timestamp_source: str
    bgr: np.ndarray
    geometry: Geometry


class FrameSource(Protocol):
    def read(self) -> Frame | None: ...
    def close(self) -> None: ...


class MediaClock:
    def __init__(self, fps: float | None, allow_fallback: bool):
        self.fps = fps
        self.allow_fallback = allow_fallback
        self.fallback = False
        self.origin = None
        self.previous = -1

    def timestamp(self, index: int, pts_ms: float) -> tuple[int, str]:
        valid = math.isfinite(pts_ms) and pts_ms >= 0
        if index == 0 and valid:
            self.origin = pts_ms
        relative = pts_ms - self.origin if valid and self.origin is not None else float("nan")
        value = round(relative) if math.isfinite(relative) else -1
        if not self.fallback and value > self.previous and value >= 0:
            self.previous = value
            return value, "MEDIA_PTS"
        if not self.allow_fallback or self.fps is None:
            raise EdgeError(
                "TIMESTAMP_UNUSABLE",
                "Timestamps inválidos e sem fallback permitido com FPS válido.",
            )
        self.fallback = True
        value = round(index * 1000 / self.fps)
        if value <= self.previous:
            raise EdgeError(
                "TIMESTAMP_DISCONTINUITY",
                "O relógio índice/FPS não mantém a continuidade. Converta o vídeo para CFR válido.",
            )
        self.previous = value
        return value, "INDEX_FPS"


class MediaSampler:
    def __init__(self, target_fps: float):
        self.interval_ms = 1000 / target_fps
        self.next_ms = 0.0

    def accepts(self, timestamp_ms: int) -> bool:
        if timestamp_ms + 0.000001 < self.next_ms:
            return False
        self.next_ms = (math.floor(timestamp_ms / self.interval_ms) + 1) * self.interval_ms
        return True


def orient_frame(image: np.ndarray, rotation: int, max_width: int) -> tuple[np.ndarray, Geometry]:
    raw_height, raw_width = image.shape[:2]
    if rotation:
        image = cv2.rotate(
            image,
            {
                90: cv2.ROTATE_90_CLOCKWISE,
                180: cv2.ROTATE_180,
                270: cv2.ROTATE_90_COUNTERCLOCKWISE,
            }[rotation],
        )
    oriented_height, oriented_width = image.shape[:2]
    if oriented_width > max_width:
        height = max(1, round(oriented_height * max_width / oriented_width))
        image = cv2.resize(image, (max_width, height), interpolation=cv2.INTER_AREA)
    height, width = image.shape[:2]
    return np.ascontiguousarray(image), Geometry(
        raw_width, raw_height, oriented_width, oriented_height, width, height, rotation
    )


class FileSource:
    def __init__(self, config: SourceConfig, max_width: int = 640):
        self.config = config
        self.max_width = max_width
        self.capture = None
        self.frames_read = 0
        self.geometry = None
        self.ended = False
        self.fps = None
        self.expected_frames = None
        self.rotation = 0
        self.clock = None

    def __enter__(self):
        path = Path(self.config.path)
        if not path.is_file():
            raise EdgeError(
                "FILE_MISSING", "Vídeo não encontrado. Confira source.path no arquivo privado."
            )
        try:
            self.capture = cv2.VideoCapture(str(path.resolve()), cv2.CAP_FFMPEG)
            if not self.capture.isOpened():
                raise EdgeError(
                    "FILE_INVALID", "Não foi possível abrir o arquivo como vídeo FFmpeg."
                )
            self.capture.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)
            if self.capture.get(cv2.CAP_PROP_ORIENTATION_AUTO):
                raise EdgeError(
                    "ORIENTATION_UNSUPPORTED", "Backend não permite desativar rotação dupla."
                )
            angle = self.capture.get(cv2.CAP_PROP_ORIENTATION_META)
            if not math.isfinite(angle) or angle % 90 != 0:
                raise EdgeError("ORIENTATION_INVALID", "Rotação não suportada. Normalize o vídeo.")
            self.rotation = (
                int(angle) % 360 if self.config.rotation == "AUTO" else self.config.rotation
            )
            sar_num = self.capture.get(cv2.CAP_PROP_SAR_NUM)
            sar_den = self.capture.get(cv2.CAP_PROP_SAR_DEN)
            if sar_num > 0 and sar_den > 0 and abs(sar_num / sar_den - 1) > 0.001:
                raise EdgeError(
                    "PIXEL_ASPECT_UNSUPPORTED", "Converta o vídeo para pixels quadrados."
                )
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            if math.isfinite(fps) and 0 < fps <= 1000:
                self.fps = fps
            count = self.capture.get(cv2.CAP_PROP_FRAME_COUNT)
            if math.isfinite(count) and count >= 1 and abs(count - round(count)) < 0.01:
                self.expected_frames = round(count)
            self.clock = MediaClock(self.fps, self.config.allowTimestampFallback)
            return self
        except Exception:
            self.close()
            raise

    def read(self) -> Frame | None:
        try:
            ok, image = self.capture.read()
        except cv2.error:
            raise EdgeError(
                "DECODE_ERROR", "O decoder falhou durante a leitura do arquivo."
            ) from None
        if not ok:
            if self.frames_read == 0:
                raise EdgeError(
                    "DECODE_ERROR", "O arquivo abriu, mas nenhum frame pôde ser decodificado."
                )
            if self.expected_frames is None:
                raise EdgeError(
                    "END_UNVERIFIED",
                    "Leitura terminou sem contagem confiável para distinguir EOF de erro.",
                )
            if self.frames_read < self.expected_frames:
                raise EdgeError(
                    "DECODE_ERROR", "Leitura interrompida antes do fim esperado do arquivo."
                )
            self.ended = True
            return None
        if image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise EdgeError(
                "FRAME_INVALID", "O decoder não produziu um frame BGR uint8 utilizável."
            )
        pts = self.capture.get(cv2.CAP_PROP_POS_MSEC)
        timestamp, timestamp_source = self.clock.timestamp(self.frames_read, pts)
        image, geometry = orient_frame(image, self.rotation, self.max_width)
        if self.geometry is not None and geometry != self.geometry:
            raise EdgeError(
                "SOURCE_GEOMETRY_CHANGED", "Dimensões mudaram. Pare e recalibre a fonte."
            )
        self.geometry = geometry
        frame = Frame(self.frames_read, timestamp, timestamp_source, image, geometry)
        self.frames_read += 1
        return frame

    def metadata(self) -> dict:
        from dataclasses import asdict

        return {
            "kind": "FILE",
            "mode": "REPLAY",
            "videoId": self.config.videoId,
            "backend": "FFMPEG",
            "fpsMetadata": self.fps,
            "frameCountMetadata": self.expected_frames,
            "durationMsEstimate": (
                self.expected_frames * 1000 / self.fps
                if self.expected_frames and self.fps
                else None
            ),
            "geometry": asdict(self.geometry) if self.geometry else None,
            "timestampFallbackUsed": bool(self.clock and self.clock.fallback),
            "endVerification": "FRAME_COUNT_METADATA",
        }

    def close(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def __exit__(self, *_):
        self.close()
