"""Cognitia integration boundary — optional adapter stubs."""

from __future__ import annotations

from typing import Any

from forgepulse.common import IntegrationFailure, UnsupportedOperation


class CognitiaAdapter:
    """Optional adapter for translating ForgePulse artifacts to Cognitia.

    This adapter is optional. ForgePulse remains fully functional without Cognitia.
    The adapter never executes pulses, bypasses safety, or declares scientific truth.
    """

    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def record_experiment_observation(self, experiment: Any) -> None:
        if not self._enabled:
            return
        raise UnsupportedOperation("Cognitia integration not yet implemented")

    def record_measurement(self, measurement: Any) -> None:
        if not self._enabled:
            return
        raise UnsupportedOperation("Cognitia integration not yet implemented")

    def record_experience(self, execution: Any) -> None:
        if not self._enabled:
            return
        raise UnsupportedOperation("Cognitia integration not yet implemented")

    def record_evidence(self, evidence: Any) -> None:
        if not self._enabled:
            return
        raise UnsupportedOperation("Cognitia integration not yet implemented")

    def request_advisory(self, request: Any) -> Any:
        if not self._enabled:
            return None
        raise UnsupportedOperation("Cognitia integration not yet implemented")
