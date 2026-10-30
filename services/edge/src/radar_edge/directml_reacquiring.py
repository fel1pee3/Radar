"""One normal DirectML session with the existing V2 reacquisition controller.

The controller owns only processing preference/state. Its inherited CPU session
loader is never entered. DirectMlEstimator remains the sole session/profiling
owner, retaining the existing hardware, runtime and no-fallback checks.
"""

from radar_edge.directml import DirectMlEstimator
from radar_edge.errors import EdgeError
from radar_edge.reacquiring_rtmo import ReacquiringRtmoEstimator


class DirectMlReacquiringEstimator:
    def __init__(
        self,
        model_path,
        runtime_profile="REFERENCE_4_SPIN",
        device_id=0,
        operator_profile_prefix=None,
    ):
        if runtime_profile != "REFERENCE_4_SPIN":
            raise EdgeError(
                "DIRECTML_CONFIG_INVALID",
                "DirectML exige REFERENCE_4_SPIN explicito.",
            )
        # Both constructors initialize Python state only. Only _directml's
        # __enter__ may create a session; the controller's CPU loader is unused.
        self._processing = ReacquiringRtmoEstimator(model_path, runtime_profile=runtime_profile)
        self._directml = DirectMlEstimator(
            model_path,
            "RTMO_ADAPTIVE_V3",
            runtime_profile,
            device_id,
            operator_profile_prefix,
        )

    @property
    def executor_metadata(self):
        return self._directml.executor_metadata

    def __getattr__(self, name):
        # Expose unchanged current-frame attempts, paths, proposals, counters
        # and preference diagnostics from the real V2 controller.
        processing = object.__getattribute__(self, "_processing")
        return getattr(processing, name)

    def __enter__(self):
        try:
            self._directml.__enter__()
            self._processing.session = self._directml.session
            self._processing.executor_metadata = self._directml.executor_metadata
            return self
        except BaseException:
            self.close()
            raise

    def estimate(self, frame):
        return self._processing.estimate(frame)

    def reset_preference(self, reason):
        return self._processing.reset_preference(reason)

    def strategy_summary(self):
        return self._processing.strategy_summary()

    def close(self):
        try:
            # The owner finalizes operator profiling before releasing its
            # session. Metadata remains available to the final worker report.
            self._directml.close()
        finally:
            self._processing.session = None

    def __exit__(self, *_):
        self.close()
