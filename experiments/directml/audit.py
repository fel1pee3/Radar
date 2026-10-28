"""Read-only Windows/DXGI/ONNX inventory. Available providers are not execution proof."""

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from importlib import metadata
from pathlib import Path

import onnx
from hardware import adapters


def inventory(model, output):
    if output.exists():
        raise ValueError("Refusing to replace an existing inventory")
    command = """
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$gpu = Get-CimInstance Win32_VideoController
$version = Get-Item experiments/directml/.venv/Lib/site-packages/onnxruntime/capi/DirectML.dll
[pscustomobject]@{
    os = $os | Select-Object Caption,Version,BuildNumber,OSArchitecture,TotalVisibleMemorySize
    cpu = $cpu | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors
    gpu = $gpu | Select-Object Name,PNPDeviceID,DriverVersion,DriverDate,AdapterRAM
    directmlDll = $version.VersionInfo.FileVersion
} | ConvertTo-Json -Depth 5
"""
    machine = json.loads(
        subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command], encoding="utf-8-sig"
        )
    )
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    graph = onnx.load(str(model), load_external_data=False)
    onnx.checker.check_model(graph)
    if hashlib.sha256(model.read_bytes()).hexdigest() != digest:
        raise RuntimeError("Model bytes changed during inventory")
    result = {
        "machine": machine,
        "dxgi": adapters(),
        "packages": {
            name: metadata.version(name)
            for name in ("onnxruntime-directml", "onnx", "numpy", "opencv-contrib-python")
        },
        "model": {
            "sha256": digest,
            "ir": graph.ir_version,
            "opsets": [
                {"domain": o.domain or "ai.onnx", "version": o.version} for o in graph.opset_import
            ],
            "nodeCount": len(graph.graph.node),
            "operators": dict(Counter(n.op_type for n in graph.graph.node)),
            "initializerDtypes": dict(
                Counter(
                    onnx.TensorProto.DataType.Name(t.data_type) for t in graph.graph.initializer
                )
            ),
            "input": [
                {
                    "name": i.name,
                    "dtype": i.type.tensor_type.elem_type,
                    "shape": [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim],
                }
                for i in graph.graph.input
            ],
        },
        "cameraOpened": False,
        "modelExecuted": False,
        "executionProof": "Use a separate ORT profile; inventory does not prove GPU execution.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"inventory": str(output), "modelSha256": digest, "cameraOpened": False}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inventory(args.model, args.output)
