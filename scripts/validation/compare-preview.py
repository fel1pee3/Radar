"""Private FILE comparison from saved observations; no inference, camera or HTTP.

Left: the existing analyzed-frame preview. Right: every decoded image with
short-lived, cyan, visual-only optical flow. This is not a LIVE benchmark.
"""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, sleep

import cv2
import numpy as np
from radar_edge.calibration import load_calibration
from radar_edge.config import load_config, private_path, quality_threshold
from radar_edge.model import file_hash, get_model_spec
from radar_edge.observations import Landmark, Observation, Pose
from radar_edge.preview import CONNECTIONS, draw_floor, fit_display, usable_point
from radar_edge.source import FileSource
from radar_edge.visual_tracking import VisualTracker


def load_observations(report_path, config):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("mode") != "REPLAY" or report.get("status") != "ok":
        raise ValueError("Use a successful private FILE report")
    if report["source"]["sha256"] != file_hash(Path(config.source.path)):
        raise ValueError("Video hash differs from the original analysis")
    spec = get_model_spec(config.model.variant)
    if (
        report["model"]["id"] != spec.model_id
        or report["model"]["sha256"] != spec.sha256
    ):
        raise ValueError("Model differs from the saved analysis")
    path = report_path.parent / "observations.jsonl"
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Observation file exceeds the private comparison limit")
    observations = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = json.loads(line)
        raw["poses"] = tuple(
            Pose(tuple(Landmark(**p) for p in pose["landmarks"]), pose["qualitySource"])
            for pose in raw["poses"]
        )
        value = Observation(**raw)
        if (
            value.cameraId != config.cameraId
            or value.mode != "REPLAY"
            or value.modelId != spec.model_id
        ):
            raise ValueError("Saved observation belongs to another source")
        if value.frameIndex in observations:
            raise ValueError("Repeated saved frame")
        observations[value.frameIndex] = value
    if not observations:
        raise ValueError("No saved observations to compare")
    return observations


def draw_points(image, points, kinds):
    for a, b in CONNECTIONS:
        if a in points and b in points:
            color = (255, 210, 40) if "FLOW" in (kinds[a], kinds[b]) else (90, 220, 100)
            cv2.line(
                image,
                tuple(map(round, points[a])),
                tuple(map(round, points[b])),
                color,
                2,
            )
    for key, point in points.items():
        color = (255, 210, 40) if kinds[key] == "FLOW" else (90, 220, 100)
        cv2.circle(image, tuple(map(round, point)), 3, color, -1)


def compose(frame, anchor_frame, anchor, visual, floor, threshold):
    left = anchor_frame.bgr.copy() if anchor_frame else np.zeros_like(frame.bgr)
    right = frame.bgr.copy()
    draw_floor(left, floor)
    draw_floor(right, floor)
    if anchor:
        h, w = left.shape[:2]
        points = {
            p.index: (p.x * (w - 1), p.y * (h - 1))
            for pose in anchor.poses
            for p in pose.landmarks
            if usable_point(p, threshold, pose.qualitySource)
        }
        draw_points(left, points, {key: "MODEL" for key in points})
    draw_points(right, visual.points, visual.kinds)
    image = np.concatenate((fit_display(left), fit_display(right)), axis=1)
    footer = np.zeros((110, image.shape[1], 3), dtype=np.uint8)
    lines = (
        "ESQUERDA: previa atual, quadros analisados | DIREITA: acompanhamento visual experimental",
        "Verde: ponto atual do modelo. Ciano: estimativa visual, NAO usada pelo detector.",
        f"REPLAY CALIBRATION | t={frame.timestamp_ms} ms | idade da ancora={visual.age_ms} ms",
        "Analises gravadas. Nao mede desempenho LIVE nem comprova melhora de deteccao.",
    )
    for n, line in enumerate(lines):
        cv2.putText(
            footer,
            line,
            (8, 22 + 25 * n),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (240, 240, 240),
            1,
        )
    return np.concatenate((image, footer), axis=0)


def compare(config_path, report_path, output, write_video=False):
    config = load_config(config_path)
    if config.source.kind != "FILE":
        raise ValueError(
            "Comparison accepts authorized FILE only; never opens a camera"
        )
    output = private_path(str(output))
    output.mkdir(parents=True, exist_ok=False)
    observations = load_observations(private_path(str(report_path)), config)
    raw_digest = hashlib.sha256(
        json.dumps(
            {str(k): asdict(v) for k, v in observations.items()}, sort_keys=True
        ).encode()
    ).hexdigest()
    tracker = VisualTracker(quality_threshold(config))
    calibration = load_calibration(config.calibrationPath)
    left_frame = left_anchor = None
    rendered = anchors = visual_frames = 0
    timestamps = []
    writer = None
    sample_frames = {0, 1100, 3300, 5100, 6000}
    saved = set()
    started = perf_counter()
    try:
        with FileSource(config.source, config.processing.maxWidth) as source:
            frame = source.read()
            while frame is not None:
                anchor = observations.get(frame.index)
                if anchor is not None:
                    digest = hashlib.sha256(frame.bgr.tobytes()).hexdigest()
                    if (
                        anchor.timestampMs != frame.timestamp_ms
                        or anchor.frameFingerprint != digest
                        or anchor.calibrationId != calibration["calibrationId"]
                        or anchor.calibrationVersion != calibration["version"]
                    ):
                        raise ValueError(
                            "Source pixels/time/calibration differ from saved analysis"
                        )
                    left_frame, left_anchor = frame, anchor
                    anchors += 1
                visual = tracker.update(frame, anchor)
                visual_frames += bool(visual.points)
                timestamps.append(frame.timestamp_ms)
                image = compose(
                    frame,
                    left_frame,
                    left_anchor,
                    visual,
                    calibration["floorPolygon"],
                    quality_threshold(config),
                )
                if write_video:
                    if writer is None:
                        writer = cv2.VideoWriter(
                            str(output / "comparison.mp4"),
                            cv2.VideoWriter_fourcc(*"mp4v"),
                            source.fps,
                            (image.shape[1], image.shape[0]),
                        )
                        if not writer.isOpened():
                            raise ValueError("Private comparison encoder unavailable")
                    writer.write(image)
                for mark in sample_frames - saved:
                    if frame.timestamp_ms >= mark:
                        if not cv2.imwrite(str(output / f"frame-{mark}.jpg"), image):
                            raise OSError("Private comparison frame could not be saved")
                        saved.add(mark)
                rendered += 1
                frame = source.read()
    finally:
        if writer is not None:
            writer.release()
    if anchors != len(observations):
        raise ValueError("Not all original observations were matched")
    unchanged = (
        raw_digest
        == hashlib.sha256(
            json.dumps(
                {str(k): asdict(v) for k, v in observations.items()}, sort_keys=True
            ).encode()
        ).hexdigest()
    )
    duration = (timestamps[-1] - timestamps[0]) / 1000 if len(timestamps) > 1 else 0
    report = {
        "scope": "EXPERIMENTAL_VISUAL_ONLY_REPLAY_CALIBRATION",
        "cameraOpened": False,
        "inferenceExecuted": False,
        "httpEnabled": False,
        "detectorInputUnchanged": unchanged,
        "rawObservationSha256": raw_digest,
        "decodedFrames": rendered,
        "originalAnalyzedFrames": anchors,
        "framesWithVisualPoints": visual_frames,
        "mediaDurationSeconds": duration,
        "sourceFrameCadence": (rendered - 1) / duration if duration else None,
        "analysisCadence": (anchors - 1) / duration if duration else None,
        "processingWallSeconds": perf_counter() - started,
        "tracker": tracker.summary(),
        "videoEncoding": "mp4v at source FPS metadata; CFR comparison, not a LIVE recording",
        "limits": "No real ground truth for point accuracy; tracked points can drift to furniture. "
        "No additional people detector between model frames. Not adopted in worker.",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def show_video(path):
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Private comparison video unavailable")
    name = "Radar - comparacao fluidez - REPLAY experimental"
    fps = capture.get(cv2.CAP_PROP_FPS) or 30
    paused, image = True, None
    try:
        while True:
            started = perf_counter()
            if image is None or not paused:
                ok, next_image = capture.read()
                if ok:
                    image = next_image
                else:
                    paused = True
            if image is None:
                break
            cv2.imshow(name, fit_display(image))
            key = cv2.waitKey(10) & 0xFF
            if (
                key in (ord("q"), 27)
                or cv2.getWindowProperty(name, cv2.WND_PROP_VISIBLE) < 1
            ):
                break
            if key == ord(" "):
                paused = not paused
            if key in (ord("r"), ord("R")):
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                image, paused = None, False
            if not paused:
                sleep(max(0, 1 / fps - (perf_counter() - started)))
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--report")
    parser.add_argument("--output")
    parser.add_argument("--video", action="store_true")
    parser.add_argument(
        "--show", help="Show a previously generated private comparison video"
    )
    args = parser.parse_args()
    if args.show:
        show_video(private_path(args.show))
    else:
        if not all((args.config, args.report, args.output)):
            parser.error("Use --config, --report and --output, or --show")
        print(json.dumps(compare(args.config, args.report, args.output, args.video)))
