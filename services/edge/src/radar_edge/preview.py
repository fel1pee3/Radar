"""Optional native window, body-only skeleton and explicit REPLAY labelling."""

from time import perf_counter

import cv2
import numpy as np

from radar_edge.calibration import validate_polygon
from radar_edge.errors import EdgeError
from radar_edge.observations import Observation, point_usable, pose_quality
from radar_edge.source import Frame

CONNECTIONS = (
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
    (27, 29),
    (29, 31),
    (28, 30),
    (30, 32),
)


def fit_display(image):
    """Fit portrait phone videos on a notebook; inference geometry stays unchanged."""
    height, width = image.shape[:2]
    scale = min(1.0, 960 / width, 720 / height)
    if scale < 1:
        return cv2.resize(
            image,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return image.copy()


def draw_floor(image, points, closed=True):
    if not points:
        return
    height, width = image.shape[:2]
    pixels = np.array(
        [(round(x * (width - 1)), round(y * (height - 1))) for x, y in points], dtype=np.int32
    )
    cv2.polylines(image, [pixels], closed, (80, 210, 240), 2)
    for x, y in pixels:
        cv2.circle(image, (int(x), int(y)), 4, (80, 210, 240), -1)


def usable_point(point, visibility, quality_source="MEDIAPIPE"):
    """Only draw current, finite points with the same two confidence gates as analysis."""
    return (
        11 <= point.index <= 32
        and point_usable(point, visibility, quality_source)
        and 0 <= point.x <= 1
        and 0 <= point.y <= 1
    )


def diagnostic_lines(observation, visibility, paused=False):
    """Explain pose quality without implying that visible points satisfy the floor policy."""
    state, reasons = pose_quality(observation.poses, visibility)
    score_mode = observation.modelId.startswith("rtmo-") or any(
        p.qualitySource == "RTMO_KEYPOINT_SCORE" for p in observation.poses
    )
    state_label = {
        "NO_POSE": "Sem pose",
        "MULTIPLE_POSES": "Multiplas poses: classificacao indisponivel",
        "LOW_CONFIDENCE": "Pose insuficiente para classificacao",
        "ONE_VALID_POSE": "Uma pose com pontos essenciais suficientes",
    }[state]
    reason_labels = {
        "NO_POSE": "sem pose",
        "MULTIPLE_POSES": "multiplas poses",
        "MISSING_LANDMARK": "pontos essenciais ausentes",
        "BODY_OUT_OF_FRAME": "pontos essenciais fora do quadro",
        "LOW_LANDMARK_QUALITY": "score articular insuficiente"
        if score_mode
        else "visibilidade/presenca insuficiente",
        "DARK_FRAME": "frame escuro",
    }
    details = tuple(
        reason_labels.get(reason, reason)
        for reason in sorted(set(reasons) | set(observation.qualityReasons))
    )
    return (
        f"{observation.mode} | t={observation.timestampMs} ms | poses={observation.poseCount}",
        f"{state_label} | inferencia={observation.inferenceMs:.1f} ms",
        *(f"Motivo: {detail}" for detail in details),
        (
            "RTMO EXPERIMENTAL | score articular; nao comprova visibilidade."
            if score_mode
            else "Verde: pontos observados validos; nao confirma pessoa no piso."
        ),
        "Sem preencher pontos ausentes",
        "PAUSADO | SPACE: continuar | Q/Esc: sair" if paused else "SPACE: pausar | Q/Esc: sair",
    )


def render(
    frame: Frame,
    observation: Observation,
    floor,
    visibility: float,
    paused=False,
    visual_points=None,
):
    image = fit_display(frame.bgr)
    draw_floor(image, floor)
    height, width = image.shape[:2]
    groups = []
    if visual_points is not None:
        groups.append(
            {
                key: (
                    round(x * (width - 1) / max(1, observation.width - 1)),
                    round(y * (height - 1) / max(1, observation.height - 1)),
                )
                for key, (x, y) in visual_points.items()
            }
        )
    for pose in observation.poses if visual_points is None else ():
        points = {
            point.index: (round(point.x * (width - 1)), round(point.y * (height - 1)))
            for point in pose.landmarks
            if usable_point(point, visibility, pose.qualitySource)
        }
        groups.append(points)
    color = (90, 220, 100) if visual_points is None else (255, 210, 40)
    for points in groups:
        for start, end in CONNECTIONS:
            if start in points and end in points:
                cv2.line(image, points[start], points[end], color, 2)
        for point in points.values():
            cv2.circle(image, point, 3, color, -1)
    # Keep text outside the source pixels: no implied fall classification.
    canvas_width = max(640, width)
    image = cv2.copyMakeBorder(image, 0, 0, 0, canvas_width - width, cv2.BORDER_CONSTANT)
    lines = diagnostic_lines(observation, visibility, paused)
    if visual_points is not None:
        lines = (
            *lines,
            "Ciano: estabilizacao visual experimental; evidencia/alertas usam pose bruta.",
        )
    footer = np.zeros((8 + len(lines) * 26, canvas_width, 3), dtype=np.uint8)
    for index, line in enumerate(lines):
        cv2.putText(
            footer, line, (6, 21 + index * 26), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (240, 240, 240), 1
        )
    return np.concatenate((image, footer), axis=0)


class LocalPreview:
    def __init__(self, enabled: bool, start_paused: bool = False):
        self.enabled = enabled
        self.opened = False
        self.name = "Radar - poses locais REPLAY"
        self.paused = bool(enabled and start_paused)
        self._initial_topmost = self.paused
        self._pause_started = None
        self._paused_seconds = 0.0
        self.on_pause = None
        self.blocking_pause = True
        self._last_view = None
        self._smoother = None
        self._visual_points = None

    def enable_stabilization(self):
        from radar_edge.visual_smoothing import VisualSmoother

        self._smoother = VisualSmoother() if self.enabled else None
        self._visual_points = None

    def _render(self, frame, observation, floor, visibility, paused=False):
        return render(
            frame,
            observation,
            floor,
            visibility,
            paused,
            visual_points=self._visual_points,
        )

    @property
    def paused_seconds(self):
        return self._paused_seconds + (
            perf_counter() - self._pause_started if self._pause_started is not None else 0
        )

    def set_topmost(self, enabled):
        try:
            cv2.setWindowProperty(self.name, cv2.WND_PROP_TOPMOST, int(enabled))
        except cv2.error:
            pass  # Some GUI backends cannot raise a window; playback remains available.

    def finish_pause(self):
        if self._pause_started is not None:
            self._paused_seconds += perf_counter() - self._pause_started
            self._pause_started = None
        self.paused = False
        if self._initial_topmost:
            self.set_topmost(False)
            self._initial_topmost = False

    def __enter__(self):
        if self.enabled:
            try:
                cv2.namedWindow(self.name, cv2.WINDOW_AUTOSIZE)
                self.opened = True
                if self._initial_topmost:
                    self.set_topmost(True)
            except cv2.error:
                raise EdgeError(
                    "PREVIEW_UNAVAILABLE",
                    "Prévia indisponível. Use --no-preview em terminal sem GUI.",
                ) from None
        return self

    def set_paused(self, value):
        if value == self.paused and (not value or self._pause_started is not None):
            return
        if value:
            self.paused = True
            self._pause_started = perf_counter()
        else:
            self.finish_pause()
        if self.on_pause:
            self.on_pause(value)
        if self.opened and not self.blocking_pause and self._last_view is not None:
            frame, observation, floor, visibility = self._last_view
            cv2.imshow(self.name, self._render(frame, observation, floor, visibility, self.paused))

    def poll(self):
        """Pump native events while LIVE capture is paused or waiting for a frame."""
        if not self.enabled or not self.opened:
            return True
        try:
            key = cv2.waitKey(1) & 0xFF
            if (
                key in (ord("q"), ord("Q"), 27)
                or cv2.getWindowProperty(self.name, cv2.WND_PROP_VISIBLE) < 1
            ):
                return False
            if key == ord(" "):
                self.set_paused(not self.paused)
            return True
        except cv2.error:
            raise EdgeError(
                "PREVIEW_UNAVAILABLE", "Falha na janela local; encerre e tente novamente."
            ) from None

    def show(self, frame: Frame, observation: Observation, floor, visibility: float) -> bool:
        if not self.enabled:
            return True
        if self._smoother is not None:
            if (
                observation.frameIndex != frame.index
                or observation.timestampMs != frame.timestamp_ms
                or observation.width != frame.geometry.width
                or observation.height != frame.geometry.height
            ):
                raise EdgeError(
                    "PREVIEW_FRAME_MISMATCH", "Pose e imagem da prévia não correspondem."
                )
            self._visual_points = self._smoother.update(observation, visibility)
        try:
            if not self.blocking_pause:
                self._last_view = (frame, observation, floor, visibility)
                if self.paused and self._pause_started is None:
                    self.set_paused(True)
                cv2.imshow(
                    self.name, self._render(frame, observation, floor, visibility, self.paused)
                )
                return self.poll()
            cv2.imshow(self.name, self._render(frame, observation, floor, visibility, self.paused))
            if self.paused:
                self._pause_started = perf_counter()
                if self.on_pause:
                    self.on_pause(True)
            while True:
                key = cv2.waitKey(30 if self.paused else 1) & 0xFF
                if (
                    key in (ord("q"), ord("Q"), 27)
                    or cv2.getWindowProperty(self.name, cv2.WND_PROP_VISIBLE) < 1
                ):
                    self.finish_pause()
                    return False
                if key == ord(" "):
                    if self.paused:
                        self.finish_pause()
                        if self.on_pause:
                            self.on_pause(False)
                        cv2.imshow(self.name, self._render(frame, observation, floor, visibility))
                        return True
                    self.paused = True
                    self._pause_started = perf_counter()
                    if self.on_pause:
                        self.on_pause(True)
                    cv2.imshow(self.name, self._render(frame, observation, floor, visibility, True))
                elif not self.paused:
                    return True
        except cv2.error:
            self.finish_pause()
            raise EdgeError(
                "PREVIEW_UNAVAILABLE",
                "A janela local falhou. Use --no-preview para execução sem GUI.",
            ) from None

    def close(self):
        if self.opened:
            try:
                self.finish_pause()
                cv2.destroyWindow(self.name)
                cv2.waitKey(1)
            except cv2.error:
                pass  # A window already closed by its owner needs no further destruction.
            finally:
                self.opened = False
                self._last_view = None
                self._visual_points = None
                if self._smoother is not None:
                    self._smoother.reset()

    def __exit__(self, *_):
        self.close()


def select_floor(frame: Frame):
    name = "Radar - IMAGEM PARADA para marcar o piso - Q cancela"
    points = []
    displayed = fit_display(frame.bgr)

    def click(event, x, y, _flags, _parameter):
        height, width = displayed.shape[:2]
        if event == cv2.EVENT_LBUTTONDOWN and 0 <= x < width and 0 <= y < height:
            points.append((x / max(1, width - 1), y / max(1, height - 1)))
        if event == cv2.EVENT_RBUTTONDOWN and points:
            points.pop()

    opened = False
    try:
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        opened = True
        cv2.setMouseCallback(name, click)
        print(
            "CALIBRAÇÃO: esta imagem fica parada para marcar o piso. "
            "Posicione a câmera antes de executar este comando. "
            "Se o chão não aparece, Q/Esc cancela; reposicione e execute calibrate novamente.\n"
            "Clique no contorno do piso, excluindo cama/sofá. "
            "Botão direito desfaz; C limpa; Enter confirma; Q/Esc cancela.",
            flush=True,
        )
        while True:
            image = displayed.copy()
            draw_floor(image, points)
            cv2.imshow(name, image)
            key = cv2.waitKey(30) & 0xFF
            if (
                key in (ord("q"), ord("Q"), 27)
                or cv2.getWindowProperty(name, cv2.WND_PROP_VISIBLE) < 1
            ):
                raise EdgeError(
                    "CALIBRATION_CANCELLED",
                    "Calibração cancelada; configuração anterior preservada.",
                )
            if key in (ord("c"), ord("C")):
                points.clear()
            if key in (10, 13):
                try:
                    return validate_polygon(points)
                except EdgeError as error:
                    print(error.message, flush=True)
    except cv2.error:
        raise EdgeError(
            "PREVIEW_UNAVAILABLE",
            "GUI indisponível. Use pontos normalizados escolhidos manualmente.",
        ) from None
    finally:
        if opened:
            try:
                cv2.destroyWindow(name)
                cv2.waitKey(1)
            except cv2.error:
                pass
