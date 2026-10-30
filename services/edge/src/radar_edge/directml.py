"""Explicit DirectML session over the unchanged RTMO estimator; no CPU substitution."""

import json
from collections import Counter
from importlib import metadata
from pathlib import Path
from time import perf_counter

from radar_edge.errors import EdgeError
from radar_edge.model import verify_model
from radar_edge.rtmo import RtmoEstimator


class DirectMlEstimator(RtmoEstimator):
    def __init__(self, model_path, recovery, runtime_profile, device_id=0, profile_prefix=None):
        super().__init__(model_path, recovery=recovery, runtime_profile=runtime_profile)
        self.device_id = device_id
        self.profile_prefix = profile_prefix
        self.executor_metadata = None

    def __enter__(self):
        try:
            import onnxruntime as ort

            from radar_edge.directml_hardware import adapters

            installed = [
                d.metadata["Name"].lower()
                for d in metadata.distributions()
                if d.metadata["Name"].lower()
                in {"onnxruntime", "onnxruntime-gpu", "onnxruntime-directml"}
            ]
            if installed != ["onnxruntime-directml"] or ort.__version__ != "1.23.0":
                raise RuntimeError(
                    "Use o ambiente isolado DirectML 1.23.0, sem runtimes concorrentes"
                )
            adapter = next(a for a in adapters() if a["dxgiIndex"] == self.device_id)
            if (
                adapter["softwareAdapter"]
                or adapter["vendorId"] != "0x1002"
                or adapter["deviceId"] != "0x15e7"
                or not adapter["direct3d12FeatureLevels"]["12_0"]["supported"]
                or "DmlExecutionProvider" not in ort.get_available_providers()
            ):
                raise RuntimeError("Adaptador AMD 1002:15E7/D3D12 ou provider indisponível")
            options = ort.SessionOptions()
            options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            options.enable_mem_pattern = False
            options.add_free_dimension_override_by_name("batch", 1)
            options.intra_op_num_threads = 4
            options.inter_op_num_threads = 1
            if self.profile_prefix:
                options.enable_profiling = True
                options.profile_file_prefix = str(self.profile_prefix)
            path = verify_model(self.model_path, "rtmo-s")
            start = perf_counter()
            self.session = ort.InferenceSession(
                str(path),
                sess_options=options,
                providers=[
                    ("DmlExecutionProvider", {"device_id": self.device_id}),
                    "CPUExecutionProvider",
                ],
            )
            self.session.disable_fallback()
            providers = self.session.get_providers()
            if "DmlExecutionProvider" not in providers:
                raise RuntimeError("Inicialização substituiu DirectML integralmente por CPU")
            self.executor_metadata = {
                "runtime": "onnxruntime-directml",
                "version": ort.__version__,
                "requested": "DIRECTML",
                "providers": providers,
                "adapter": adapter,
                "initializationMs": (perf_counter() - start) * 1000,
                "executionMode": "ORT_SEQUENTIAL",
                "memoryPattern": False,
                "batchSessionOverride": 1,
                "intraOpThreads": 4,
                "interOpThreads": 1,
                "automaticSessionFallbackDisabled": True,
                "outputs": "Synchronous CPU NumPy arrays consumed by unchanged RTMO decode",
            }
            return self
        except Exception as exc:
            self.session = None
            raise EdgeError(
                "DIRECTML_INITIALIZATION_FAILED",
                "DirectML obrigatório não inicializou. Use um ambiente isolado DirectML 1.23.0 "
                "e confira o adaptador AMD. Nenhuma substituição por CPU foi feita.",
            ) from exc

    def close(self):
        try:
            if self.session is not None and self.profile_prefix:
                path = self.session.end_profiling()
                rows = json.loads(Path(path).read_text(encoding="utf-8"))
                kernels = [
                    r
                    for r in rows
                    if r.get("cat") == "Node"
                    and r.get("name", "").endswith("_kernel_time")
                    and r.get("args", {}).get("provider")
                ]
                compute = [
                    r
                    for r in kernels
                    if r["args"]["provider"] == "DmlExecutionProvider"
                    and (
                        "DmlFusedNode" in r["args"].get("op_name", "")
                        or r["args"].get("op_name") in {"Conv", "MatMul", "FusedMatMul"}
                    )
                ]
                self.executor_metadata["operatorProfile"] = {
                    "path": path,
                    "nodeEventsByProvider": dict(Counter(r["args"]["provider"] for r in kernels)),
                    "gpuComputeProven": bool(compute),
                    "scope": "ORT host profiling; not exclusive GPU kernel time",
                }
        finally:
            super().close()
