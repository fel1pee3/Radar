"""Human markers independent of predictions. --check never opens a source/window.

Run with uv from the repository root. The operator must see the actual scene;
scheduled prompts are never substituted for ground truth. No video is recorded.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from uuid import uuid4

from radar_edge.config import load_config, private_path
from radar_edge.delivery import credentials
from radar_edge.posture import check_posture

SCENES = (
    ("lateral-1", True),
    ("lateral-2", True),
    ("feet-to-camera-1", True),
    ("feet-to-camera-2", True),
    ("head-to-camera-1", True),
    ("head-to-camera-2", True),
    ("chair", False),
    ("kneeling", False),
    ("pick-up-object", False),
    ("walking", False),
    ("empty-room", False),
    ("return-walking", False),
)
SCENE_LABELS = {
    "lateral-1": "Deitado de lado — tentativa 1",
    "lateral-2": "Deitado de lado — tentativa 2",
    "feet-to-camera-1": "Deitado com os pés para a câmera — tentativa 1",
    "feet-to-camera-2": "Deitado com os pés para a câmera — tentativa 2",
    "head-to-camera-1": "Deitado com a cabeça para a câmera — tentativa 1",
    "head-to-camera-2": "Deitado com a cabeça para a câmera — tentativa 2",
    "chair": "Sentar em cadeira",
    "kneeling": "Ajoelhar",
    "pick-up-object": "Abaixar para pegar objeto",
    "walking": "Caminhar",
    "empty-room": "Cômodo vazio",
    "return-walking": "Voltar ao cômodo e caminhar",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--start", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    check_posture(config)
    api_url, _token = credentials(config.events.delivery, config.cameraId)
    if (
        config.source.kind != "WEBCAM"
        or config.events.evidenceMode != "skeleton"
        or config.events.snapshotAuthorized
        or not config.diagnostics.exportDecisions
        or not config.events.delivery.enabled
        or config.processing.maxRunSeconds != 720
    ):
        raise ValueError(
            "Use a configuração preparada do ensaio de 12 minutos, sem imagem."
        )
    protocol = {
        "scenes": [
            {"id": name, "expectedPersonOnFloor": positive} for name, positive in SCENES
        ],
        "floorHoldSeconds": 10,
        "standingIntervalSeconds": 20,
        "deadlineMs": 5000,
        "minimumCoverage": 0.8,
        "sessionLimitSeconds": 720,
        "videoRecorded": False,
        "humanMarkersRequired": True,
        "plannedTimeIsNotGroundTruth": True,
    }
    if args.check:
        print(json.dumps({"status": "ok", "sourceOpened": False, **protocol}))
        return

    import httpx

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=5) as client:
        response = client.get(api_url + "/health/ready")
        if response.status_code != 200:
            raise ValueError(
                "Inicie PostgreSQL e API antes da sessão; câmera não foi aberta."
            )

    import tkinter as tk

    # The explicit --start command authorizes this one foreground session.
    root = private_path(".local/detector-evolution/physical-sessions") / str(uuid4())
    root.mkdir(parents=True)
    config.events.outboxPath = str(root / "outbox.sqlite")
    config.diagnostics.outputDirectory = str(root / "results")
    import yaml

    path = root / "config.yaml"
    path.write_text(
        yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8"
    )
    (root / "protocol.json").write_text(
        json.dumps(protocol, indent=2), encoding="utf-8"
    )
    markers = (root / "human-markers.jsonl").open("x", encoding="utf-8", buffering=1)
    window = tk.Tk()
    window.title("Radar — marcar cenas reais (sem previsão)")
    window.geometry("760x480")
    label = tk.Label(window, font=("Segoe UI", 15), wraplength=730, justify="left")
    label.pack(padx=15, pady=15)
    stdout = (root / "worker.json").open("x", encoding="utf-8")
    stderr = (root / "worker-errors.log").open("x", encoding="utf-8")
    worker = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from radar_edge.cli import main; main()",
            "run",
            "--config",
            str(path),
            "--preview",
        ],
        stdout=stdout,
        stderr=stderr,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    state = {"index": 0, "start": None, "ready": time.monotonic_ns(), "finished": False}

    def write(kind, **values):
        markers.write(
            json.dumps(
                {
                    "kind": kind,
                    "hostMonotonicNs": time.monotonic_ns(),
                    "utc": datetime.now(UTC).isoformat(),
                    **values,
                }
            )
            + "\n"
        )

    write("SESSION_OPEN", cameraId=config.cameraId)

    def mark():
        if state["index"] >= len(SCENES) or worker.poll() is not None:
            return
        now = time.monotonic_ns()
        name, positive = SCENES[state["index"]]
        if state["start"] is None:
            if now < state["ready"]:
                return
            state["start"] = now
            write("HUMAN_SCENE_START", scene=name, expectedPersonOnFloor=positive)
        else:
            if now - state["start"] < (10 if positive else 15) * 1_000_000_000:
                return
            write("HUMAN_SCENE_END", scene=name)
            state["start"] = None
            state["index"] += 1
            state["ready"] = now + 20_000_000_000

    button = tk.Button(
        window,
        text="Marcar início/fim REAL da cena",
        command=mark,
        font=("Segoe UI", 16),
    )
    button.pack(pady=10)
    tk.Button(
        window,
        text="Vi um novo incidente no painel",
        command=lambda: (
            None
            if state["finished"]
            else write(
                "HUMAN_PANEL_VISIBLE",
                scene=SCENES[min(state["index"], len(SCENES) - 1)][0],
            )
        ),
    ).pack()
    tk.Label(
        window,
        text="Operador: só marque quando a postura estiver realmente estabelecida.\nOutra pessoa ou teclado ao alcance permite marcar sem mover o notebook.\nSem operador/tempo confiável, o resultado será inconclusivo.\nEntre tentativas: levantar com calma e permanecer em pé por 20 s.\nQ/Esc na janela da câmera encerra. Não provoque queda.",
        font=("Segoe UI", 11),
    ).pack(padx=10, pady=10)
    window.bind("<Return>", lambda _: mark())

    def update():
        if worker.poll() is not None:
            if not state["finished"]:
                write(
                    "SESSION_CLOSED",
                    exitCode=worker.returncode,
                    completedScenes=state["index"],
                    openScene=state["start"] is not None,
                )
                state["finished"] = True
                markers.close()
                stdout.close()
                stderr.close()
            label.config(
                text=f"Worker encerrado. {state['index']}/12 cenas marcadas.\nRegistros privados: {root}\nA análise e a revisão no painel ainda precisam ser conferidas."
            )
            button.config(state="disabled")
            return
        if state["index"] >= len(SCENES):
            label.config(
                text="Cenas marcadas. Confira a janela da câmera e pressione Q para encerrar;\no limite fixo de 12 minutos permanece. Nenhuma repetição automática."
            )
            button.config(state="disabled")
        else:
            name, _positive = SCENES[state["index"]]
            elapsed = (time.monotonic_ns() - (state["start"] or state["ready"])) / 1e9
            label.config(
                text=f"{state['index'] + 1}/12: {SCENE_LABELS[name]}\n"
                + (
                    f"Cena em curso: {elapsed:.1f} s. Marque o fim antes de sair da postura."
                    if state["start"]
                    else f"Prepare a cena com calma. Intervalo restante: {max(0, -elapsed):.0f} s.\nMarque início somente ao observar a postura estabelecida."
                )
            )
            button.config(
                state="normal" if state["start"] or elapsed >= 0 else "disabled"
            )
        window.after(100, update)

    def close():
        if worker.poll() is None:
            label.config(
                text="Encerre primeiro a câmera com Q/Esc; assim a fila e o estado final são preservados."
            )
        else:
            window.destroy()

    window.protocol("WM_DELETE_WINDOW", close)
    update()
    print(
        json.dumps({"sessionDirectory": str(root), "videoRecorded": False}), flush=True
    )
    window.mainloop()


if __name__ == "__main__":
    main()
