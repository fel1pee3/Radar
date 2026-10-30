"""Effective runtime identity for private reports; no installation or native loading."""

import platform
import sys
from importlib import metadata


def runtime_identity():
    packages = {}
    for name in (
        "numpy",
        "opencv-contrib-python",
        "mediapipe",
        "onnxruntime",
        "onnxruntime-directml",
    ):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return {
        "pythonVersion": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "basePrefix": sys.base_prefix,
        "packages": packages,
        "scope": (
            "Effective process identity; Authenticode attestation is in runtime preparation proof."
        ),
    }
