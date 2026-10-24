"""Prepare private stage 08 files; never opens camera, media or credentials."""

import json
import shutil
from pathlib import Path

import yaml
from radar_edge.config import load_config


def main():
    root = Path(".local/etapa08")
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "webcam.yaml"
    original = Path(".local/edge-webcam.yaml")
    if original.exists() and not destination.exists():
        config = load_config(original)
        calibration = root / "calibration-webcam.json"
        if Path(config.calibrationPath).is_file() and not calibration.exists():
            shutil.copyfile(config.calibrationPath, calibration)
        config.calibrationPath = str(calibration)
        config.processing.maxRunSeconds = 1830.0
        config.processing.maxObservations = None
        config.processing.preview = True
        config.processing.previewStartPaused = False
        config.events.outboxPath = str(root / "webcam.sqlite")
        config.events.evidenceMode = "skeleton"
        config.events.snapshotAuthorized = False
        config.diagnostics.outputDirectory = str(root / "live-results")
        config.diagnostics.exportObservations = False
        destination.write_text(
            yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8"
        )
    scenarios = [
        "pessoa já deitada de lado",
        "pessoa já deitada de costas",
        "outra sessão de pessoa já no chão",
        "outra sessão segura de pessoa já no chão",
        "sentar em cadeira",
        "agachar",
        "ajoelhar",
        "pegar objeto",
        "alongar",
        "deitar voluntariamente",
        "oclusão parcial",
        "sair do quadro",
    ]
    plan = root / "collection-plan.json"
    if not plan.exists():
        plan.write_text(
            json.dumps(
                {
                    "status": "PLANNED_NOT_COLLECTED",
                    "matchingToleranceMs": 2000,
                    "instructions": "Filmagens autorizadas, câmera fixa, 10–20 s, sem queda. Anotar sessões reais, corpo/piso, períodos sem visibilidade e início/fim antes de executar o detector. Deitar voluntariamente pode ser alvo de postura e confundidor de ajuda.",
                    "scenes": [
                        {
                            "id": f"evaluation-{i + 1:02}",
                            "scenario": scene,
                            "collected": False,
                            "authorized": False,
                            "source": None,
                            "sessionId": None,
                            "personPseudonym": None,
                            "intervals": [],
                        }
                        for i, scene in enumerate(scenarios)
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "status": "ok",
                "webcamConfigPrepared": destination.is_file(),
                "originalPreserved": True,
                "cameraOpened": False,
                "credentialsRead": False,
                "collectionPlan": str(plan),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
