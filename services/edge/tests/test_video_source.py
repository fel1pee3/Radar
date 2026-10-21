"""Synthetic files exercise infrastructure, not human pose accuracy."""

import struct
from dataclasses import replace

import cv2
import numpy as np
import pytest

from radar_edge.config import SourceConfig
from radar_edge.errors import EdgeError
from radar_edge.source import FileSource, MediaClock, MediaSampler, orient_frame


def source_config(path, **overrides):
    return SourceConfig(path=str(path), videoId="synthetic", authorized=True, **overrides)


def test_sequential_decoder_media_time_sampling_and_normal_end(synthetic_video):
    source = FileSource(source_config(synthetic_video))
    sampled = []
    with source:
        sampler = MediaSampler(5)
        while (frame := source.read()) is not None:
            if sampler.accepts(frame.timestamp_ms):
                sampled.append((frame.index, frame.timestamp_ms))
        assert source.ended
        assert source.frames_read == 20
        assert source.metadata()["durationMsEstimate"] == 2000
    assert source.capture is None
    assert sampled == [(index, index * 100) for index in range(0, 20, 2)]


def test_file_missing_and_invalid(tmp_path):
    with pytest.raises(EdgeError, match="Vídeo não encontrado") as caught:
        with FileSource(source_config(tmp_path / "missing.avi")):
            pass
    assert caught.value.code == "FILE_MISSING"
    path = tmp_path / "invalid.avi"
    path.write_bytes(b"not video")
    source = FileSource(source_config(path))
    with pytest.raises(EdgeError) as caught, source:
        source.read()
    assert caught.value.code == "FILE_INVALID"
    assert source.capture is None


def test_early_stop_releases_capture(synthetic_video):
    source = FileSource(source_config(synthetic_video))
    with source:
        assert source.read().index == 0
    assert source.capture is None
    assert source.frames_read == 1
    assert not source.ended


def test_failed_decode_is_not_eof_or_no_pose(synthetic_video):
    source = FileSource(source_config(synthetic_video))
    with pytest.raises(EdgeError) as caught, source:
        source.read()
        source.capture.release()  # Inject loss before expected end, only in this test capture.
        source.read()
    assert caught.value.code == "DECODE_ERROR"
    assert not source.ended
    assert source.capture is None


def test_unknown_length_cannot_claim_verified_eof(synthetic_video):
    with FileSource(source_config(synthetic_video)) as source:
        source.expected_frames = None
        with pytest.raises(EdgeError) as caught:
            while source.read() is not None:
                pass
    assert caught.value.code == "END_UNVERIFIED"


@pytest.mark.parametrize("pts", [[0, 40, 80], [500, 540, 580]])
def test_pts_clock_normalizes_origin(pts):
    clock = MediaClock(25, True)
    assert [clock.timestamp(i, value) for i, value in enumerate(pts)] == [
        (0, "MEDIA_PTS"),
        (40, "MEDIA_PTS"),
        (80, "MEDIA_PTS"),
    ]


@pytest.mark.parametrize("invalid", [0, -1, float("nan"), float("inf")])
def test_bad_pts_switches_to_cfr_fallback_permanently(invalid):
    clock = MediaClock(25, True)
    assert clock.timestamp(0, 0) == (0, "MEDIA_PTS")
    assert clock.timestamp(1, invalid) == (40, "INDEX_FPS")
    assert clock.timestamp(2, 200) == (80, "INDEX_FPS")
    assert clock.fallback


@pytest.mark.parametrize("fps,allow", [(None, True), (25, False)])
def test_bad_timing_without_valid_permitted_fallback_fails(fps, allow):
    clock = MediaClock(fps, allow)
    clock.timestamp(0, 0)
    with pytest.raises(EdgeError) as caught:
        clock.timestamp(1, 0)
    assert caught.value.code == "TIMESTAMP_UNUSABLE"


def test_cannot_jump_to_a_fallback_behind_prior_pts():
    clock = MediaClock(25, True)
    clock.timestamp(0, 0)
    clock.timestamp(1, 1000)
    with pytest.raises(EdgeError) as caught:
        clock.timestamp(2, 1000)
    assert caught.value.code == "TIMESTAMP_DISCONTINUITY"


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_orientation_color_and_proportional_resize(rotation):
    image = np.zeros((400, 800, 3), dtype=np.uint8)
    image[:100, :100] = (0, 0, 255)
    processed, geometry = orient_frame(image, rotation, 640)
    assert processed.flags.c_contiguous
    assert processed.dtype == np.uint8
    assert geometry.width <= 640
    assert geometry.rotation == rotation
    if rotation in (90, 270):
        assert processed.shape[:2] == (800, 400)
    else:
        assert processed.shape[:2] == (320, 640)
    corner = {0: (0, 0), 90: (0, -1), 180: (-1, -1), 270: (-1, 0)}[rotation]
    assert tuple(processed[corner]) == (0, 0, 255)
    assert geometry.orientedWidth / geometry.orientedHeight == pytest.approx(
        geometry.width / geometry.height
    )


def test_geometry_change_detected(synthetic_video):
    with FileSource(source_config(synthetic_video)) as source:
        source.read()
        source.geometry = replace(source.geometry, width=1)
        with pytest.raises(EdgeError) as caught:
            source.read()
    assert caught.value.code == "SOURCE_GEOMETRY_CHANGED"


def test_real_mp4_rotation_metadata_matches_decoder_auto_orientation(tmp_path):
    path = tmp_path / "rotation.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    assert writer.isOpened()
    image = np.full((240, 320, 3), 120, np.uint8)
    image[:60, :60] = (0, 0, 255)
    for _ in range(3):
        writer.write(image)
    writer.release()
    data = bytearray(path.read_bytes())
    # Controlled synthetic ISO BMFF tkhd v0 matrix; no personal video modification.
    atom = data.index(b"tkhd") - 4
    assert data[atom + 8] == 0
    matrix = (0, 65536, 0, -65536, 0, 0, 0, 0, 1 << 30)
    data[atom + 48 : atom + 84] = struct.pack(">9i", *matrix)
    path.write_bytes(data)
    reference = cv2.VideoCapture(str(path), cv2.CAP_FFMPEG)
    try:
        assert reference.get(cv2.CAP_PROP_ORIENTATION_META) in (90, 270)
        ok, auto_oriented = reference.read()
        assert ok
        assert auto_oriented.shape[:2] == (320, 240)
    finally:
        reference.release()
    with FileSource(source_config(path)) as source:
        frame = source.read()
    assert frame.geometry.rotation in (90, 270)
    assert np.array_equal(frame.bgr, auto_oriented)
