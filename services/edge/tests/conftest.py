import cv2
import numpy as np
import pytest


@pytest.fixture
def synthetic_video(tmp_path):
    path = tmp_path / "synthetic.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (320, 240))
    assert writer.isOpened()
    try:
        for index in range(20):
            image = np.full((240, 320, 3), (100 + index, 140, 180), dtype=np.uint8)
            image[:40, :40] = (0, 0, 255)
            writer.write(image)
    finally:
        writer.release()
    return path
