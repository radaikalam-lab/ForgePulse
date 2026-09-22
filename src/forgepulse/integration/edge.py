"""Edge Integration Boundary for ForgePulse."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from forgepulse.common import IntegrationFailure, InvalidTransition
from forgepulse.experiment import Experiment, ExperimentStatus
from forgepulse.measurement import RawMeasurement, SourceType


@dataclass
class EdgeIntegrationBoundary:
    """Manages the edge integration boundary for experiment data flow.

    This boundary enforces authority separation between ForgePulse domain
    and external systems (including optional Cognitia integration).
    """

    experiment: Experiment
    cognitia_adapter: Optional[Any] = None
    _measurement_count: int = field(default=0, repr=False)

    def record_observation(self, observation: Any) -> None:
        """Record an observation from the edge.

        Args:
            observation: Raw observation data from the edge.

        Raises:
            InvalidTransition: If the experiment is not in RUNNING state.
            IntegrationFailure: If recording fails.
        """
        if self.experiment.status != ExperimentStatus.RUNNING:
            raise InvalidTransition(
                f"Cannot record observation when experiment is in {self.experiment.status}. "
                "Expected RUNNING."
            )
        if self.cognitia_adapter is not None:
            try:
                self.cognitia_adapter.record_experiment_observation(observation)
            except Exception as exc:
                raise IntegrationFailure(f"Failed to record observation: {exc}") from exc

    def record_measurement(self, measurement: RawMeasurement) -> None:
        """Record a normalized measurement from the edge.

        Args:
            measurement: Normalized RawMeasurement object.

        Raises:
            InvalidTransition: If the experiment is not in RUNNING or COMPLETED state.
            IntegrationFailure: If recording fails.
        """
        if self.experiment.status not in (ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED):
            raise InvalidTransition(
                f"Cannot record measurement when experiment is in {self.experiment.status}. "
                "Expected RUNNING or COMPLETED."
            )
        self._measurement_count += 1
        if self.cognitia_adapter is not None:
            try:
                self.cognitia_adapter.record_measurement(measurement)
            except Exception as exc:
                raise IntegrationFailure(f"Failed to record measurement: {exc}") from exc

    def record_experience(self, execution: Any) -> None:
        """Record execution experience to external systems.

        Args:
            execution: Execution data to record.

        Raises:
            InvalidTransition: If the experiment is not in COMPLETED or FAILED state.
            IntegrationFailure: If recording fails.
        """
        if self.experiment.status not in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED):
            raise InvalidTransition(
                f"Cannot record experience when experiment is in {self.experiment.status}. "
                "Expected COMPLETED or FAILED."
            )
        if self.cognitia_adapter is not None:
            try:
                self.cognitia_adapter.record_experience(execution)
            except Exception as exc:
                raise IntegrationFailure(f"Failed to record experience: {exc}") from exc

    def record_evidence(self, evidence: Any) -> None:
        """Record evidence to external systems.

        Args:
            evidence: Evidence data to record.

        Raises:
            IntegrationFailure: If recording fails.
        """
        if self.cognitia_adapter is not None:
            try:
                self.cognitia_adapter.record_evidence(evidence)
            except Exception as exc:
                raise IntegrationFailure(f"Failed to record evidence: {exc}") from exc

    def request_advisory(self, request: Any) -> Any:
        """Request advisory from external systems.

        Args:
            request: Advisory request data.

        Returns:
            Advisory response or None if Cognitia is not enabled.

        Raises:
            InvalidTransition: If the experiment is not in RUNNING state.
            IntegrationFailure: If the request fails.
        """
        if self.experiment.status != ExperimentStatus.RUNNING:
            raise InvalidTransition(
                f"Cannot request advisory when experiment is in {self.experiment.status}. "
                "Expected RUNNING."
            )
        if self.cognitia_adapter is None:
            return None
        try:
            return self.cognitia_adapter.request_advisory(request)
        except Exception as exc:
            raise IntegrationFailure(f"Failed to request advisory: {exc}") from exc

    @property
    def measurement_count(self) -> int:
        """Number of measurements recorded through this boundary."""
        return self._measurement_count
