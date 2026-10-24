"""Local CLI. env preserves its original import-only diagnostic."""

import argparse
import json
import platform
import sys
from importlib.metadata import distributions, version


def inspect_environment() -> dict[str, object]:
    providers = sorted(
        package.metadata["Name"]
        for package in distributions()
        if package.metadata["Name"].lower().startswith("opencv-")
    )
    if providers != ["opencv-contrib-python"]:
        raise RuntimeError(
            "Instale somente opencv-contrib-python; há fornecedores cv2 incompatíveis."
        )

    import cv2
    import mediapipe
    import onnxruntime
    from mediapipe.tasks.python import vision

    if not hasattr(vision, "PoseLandmarker"):
        raise RuntimeError("MediaPipe Tasks PoseLandmarker indisponível nesta instalação.")
    build = cv2.getBuildInformation()
    backends = [
        line.strip()
        for line in build.splitlines()
        if any(key in line for key in ("GUI:", "FFMPEG:", "Media Foundation:", "DirectShow:"))
    ]
    return {
        "status": "ok",
        "command": "env",
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "packages": {
            name: version(name)
            for name in ("mediapipe", "opencv-contrib-python", "pydantic", "httpx", "onnxruntime")
        },
        "mediapipe_import": mediapipe.__version__,
        "opencv_import": cv2.__version__,
        "onnxruntime_import": onnxruntime.__version__,
        "opencv_providers": providers,
        "opencv_build": backends,
        "pose_landmarker_import": "ok",
        "model_loaded": False,
        "camera_opened": False,
        "inference_executed": False,
    }


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Radar Edge — replay local, poses e suspeitas temporais experimentais."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("env", help="Importa bibliotecas sem abrir arquivo/modelo.")
    backup = commands.add_parser("backup-outbox", help="Copia fila parada, excluindo JPEG.")
    backup.add_argument("--config", required=True)
    backup.add_argument("--output", required=True)
    restore = commands.add_parser(
        "restore-outbox", help="Restaura fila em destino novo, sem envio."
    )
    restore.add_argument("--input", required=True)
    restore.add_argument("--output", required=True)
    probe = commands.add_parser("probe", help="Abre somente a webcam explicitamente configurada.")
    probe.add_argument("--config", required=True)
    probe.add_argument("--seconds", type=float, default=5.0)
    probe.add_argument("--preview", action="store_true")
    evidence_status = commands.add_parser(
        "evidence-status", help="Confere modo sem abrir fonte ou banco."
    )
    evidence_status.add_argument("--config", required=True)
    control = commands.add_parser("control", help="Pausa, retoma ou encerra o worker local.")
    control.add_argument("--config", required=True)
    control.add_argument(
        "--action", required=True, choices=["pause", "resume", "reconnect", "stop"]
    )
    fetch = commands.add_parser(
        "model-fetch", help="Obtém explicitamente o bundle oficial com hash fixado."
    )
    fetch.add_argument("--variant", choices=("lite", "full", "rtmo-s"), default="lite")
    fetch.add_argument(
        "--output", help="Arquivo privado de destino; padrão específico da variante."
    )
    evaluate = commands.add_parser(
        "evaluate", help="Avalia episódios com manifesto privado; sem entrega HTTP."
    )
    evaluate.add_argument("--manifest", required=True)
    evaluate.add_argument("--replay-speed", type=float, default=0.0)
    for name in ("reset-episode", "deliver", "outbox-status", "cleanup"):
        command = commands.add_parser(name)
        command.add_argument("--config", default=".local/edge.yaml")
        if name == "reset-episode":
            command.add_argument("--reason", required=True)
        if name == "deliver":
            command.add_argument("--resume-auth", action="store_true")
    for name in ("doctor", "calibrate", "run"):
        command = commands.add_parser(name)
        command.add_argument("--config", default=".local/edge.yaml")
        if name == "calibrate":
            command.add_argument("--frame-ms", type=int, default=0)
            command.add_argument(
                "--points", help="JSON privado com pontos selecionados manualmente."
            )
            command.add_argument("--confirm-floor", action="store_true")
        if name == "run":
            preview = command.add_mutually_exclusive_group()
            preview.add_argument("--preview", action="store_true", dest="preview", default=None)
            preview.add_argument("--no-preview", action="store_false", dest="preview")
            preview.add_argument(
                "--preview-paused",
                action="store_true",
                help="Abre a previa pausada; SPACE inicia ou pausa, Q/Esc encerra.",
            )
            command.add_argument("--replay-speed", type=float)
            command.add_argument("--max-observations", type=int)
            command.add_argument("--export-observations", action="store_true")
            command.add_argument("--poses-only", action="store_true")
    args = parser.parse_args()
    from radar_edge.errors import EdgeError

    code = 0
    try:
        if args.command == "env":
            result = inspect_environment()
        elif args.command == "restore-outbox":
            from radar_edge.backup import copy_outbox

            result = copy_outbox(args.input, args.output)
        elif args.command == "backup-outbox":
            from radar_edge.backup import backup_outbox
            from radar_edge.config import load_config

            result = backup_outbox(load_config(args.config), args.output)
        elif args.command == "model-fetch":
            from radar_edge.model import fetch_model

            result = fetch_model(args.output, variant=args.variant)
        elif args.command == "evaluate":
            from radar_edge.evaluation import evaluate_manifest

            result, code = evaluate_manifest(args.manifest, args.replay_speed)
        elif args.command == "probe":
            from radar_edge.config import load_config
            from radar_edge.webcam import probe

            config = load_config(args.config)
            if config.source.kind != "WEBCAM" or not 1 <= args.seconds <= 60:
                raise EdgeError("INVALID_ARGUMENT", "Probe exige WEBCAM e 1–60 segundos.")
            result = probe(config, args.seconds, args.preview)
        elif args.command == "evidence-status":
            import os

            from radar_edge.config import load_config

            config = load_config(args.config)
            mode = os.environ.get("EVIDENCE_MODE", config.events.evidenceMode)
            if mode not in {"none", "skeleton", "snapshot"}:
                raise EdgeError("INVALID_EVIDENCE_MODE", "Modo de evidencia invalido.")
            result = {
                "status": "ok",
                "mode": mode,
                "jpegEnabled": mode == "snapshot",
                "snapshotAuthorized": config.events.snapshotAuthorized,
                "sourceOpened": False,
                "databaseOpened": False,
            }
        elif args.command == "control":
            from radar_edge.config import load_config
            from radar_edge.live import send_control

            result = send_control(load_config(args.config), args.action)
        else:
            from radar_edge.config import DiagnosticsConfig, ProcessingConfig, load_config
            from radar_edge.pipeline import doctor, run_pipeline

            config = load_config(args.config)
            if args.command in {"reset-episode", "deliver", "outbox-status", "cleanup"}:
                from radar_edge.event_runtime import manage_outbox

                result = manage_outbox(
                    config,
                    args.command,
                    getattr(args, "reason", None),
                    getattr(args, "resume_auth", False),
                )
            elif args.command == "doctor":
                result = doctor(config)
            elif args.command == "calibrate":
                from radar_edge.calibration import calibrate

                if args.frame_ms < 0:
                    raise EdgeError(
                        "INVALID_ARGUMENT", "--frame-ms deve ser maior ou igual a zero."
                    )
                result = calibrate(config, args.frame_ms, args.points, args.confirm_floor)
            else:
                overrides = {
                    key: value
                    for key, value in {
                        "preview": args.preview,
                        "replaySpeed": args.replay_speed,
                        "maxObservations": args.max_observations,
                    }.items()
                    if value is not None
                }
                if args.preview_paused:
                    overrides.update(preview=True, previewStartPaused=True)
                elif args.preview is False:
                    overrides["previewStartPaused"] = False
                config.processing = ProcessingConfig.model_validate(
                    {**config.processing.model_dump(), **overrides}
                )
                if args.export_observations:
                    config.diagnostics = DiagnosticsConfig.model_validate(
                        {**config.diagnostics.model_dump(), "exportObservations": True}
                    )
                if args.poses_only:
                    config.events.enabled = False
                result, code = run_pipeline(config)
    except EdgeError as error:
        result = {
            "status": "error",
            "command": args.command,
            "code": error.code,
            "message": error.message,
        }
        code = 1
    except KeyboardInterrupt:
        result = {
            "status": "interrupted",
            "command": args.command,
            "message": "Interrupção solicitada; recursos liberados.",
        }
        code = 130
    except Exception as error:
        result = {
            "status": "error",
            "command": args.command,
            "error_type": type(error).__name__,
            "code": "CONFIG_OR_ENVIRONMENT_ERROR",
            "message": (
                "Confira configuração, limites dos argumentos e "
                "uv sync --project services/edge --frozen. Nenhum traceback privado foi exibido."
            ),
        }
        code = 1
    print(
        json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2),
        file=sys.stderr if code else sys.stdout,
    )
    if code:
        raise SystemExit(code)
