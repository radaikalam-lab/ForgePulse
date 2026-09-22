"""Tests for EdgeIntegrationBoundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from forgepulse.common import IntegrationFailure, InvalidTransition, Quantity
from forgepulse.experiment import (
    Atmosphere,
    Chamber,
    Experiment,
    ExperimentObjective,
    ExperimentSpecification,
    ExperimentStatus,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
)
from forgepulse.integration import CognitiaAdapter, EdgeIntegrationBoundary
from forgepulse.measurement import RawMeasurement, SourceType


def _make_experiment() -> Experiment:
    spec = ExperimentSpecification(
        experiment_id="exp-001",
        experiment_version="1.0.0",
        schema_version="1.0.0",
        created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        objective=ExperimentObjective(description="Test"),
        feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
        chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
        pulse_sequence=PulseSequence(
            pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
            inter_pulse_interval=Quantity(value=1.0, unit="s"),
        ),
        process_constraints=ProcessConstraint(),
    )
    return Experiment(experiment_id=spec.experiment_id, specification=spec)


class MockCognitiaAdapter:
    """Mock CognitiaAdapter for testing."""

    def __init__(self):
        self.recorded_observations = []
        self.recorded_measurements = []
        self.recorded_experiences = []
        self.recorded_evidence = []
        self.advisory_requests = []

    def record_experiment_observation(self, observation):
        self.recorded_observations.append(observation)

    def record_measurement(self, measurement):
        self.recorded_measurements.append(measurement)

    def record_experience(self, execution):
        self.recorded_experiences.append(execution)

    def record_evidence(self, evidence):
        self.recorded_evidence.append(evidence)

    def request_advisory(self, request):
        self.advisory_requests.append(request)
        return {"advisory": "test"}


class TestEdgeIntegrationBoundary:
    def test_record_observation_requires_running(self):
        experiment = _make_experiment()
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        with pytest.raises(InvalidTransition):
            boundary.record_observation({"data": "test"})

    def test_record_observation_succeeds_when_running(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        boundary.record_observation({"data": "test"})
        assert True

    def test_record_measurement_forwards_to_cognitia(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        mock_adapter = MockCognitiaAdapter()
        boundary = EdgeIntegrationBoundary(experiment=experiment, cognitia_adapter=mock_adapter)
        measurement = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[1.0, 2.0, 3.0],
            unit="V",
            source_type=SourceType.RAW,
        )
        boundary.record_measurement(measurement)
        assert len(mock_adapter.recorded_measurements) == 1
        assert mock_adapter.recorded_measurements[0] == measurement

    def test_record_measurement_increments_count(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        measurement = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[1.0],
            unit="V",
            source_type=SourceType.RAW,
        )
        assert boundary.measurement_count == 0
        boundary.record_measurement(measurement)
        assert boundary.measurement_count == 1
        boundary.record_measurement(measurement)
        assert boundary.measurement_count == 2

    def test_record_experience_requires_completed_or_failed(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.COMPLETED)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        boundary.record_experience({"execution": "data"})
        assert True

    def test_record_evidence_without_adapter_is_noop(self):
        experiment = _make_experiment()
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        boundary.record_evidence({"evidence": "data"})
        assert boundary.measurement_count == 0

    def test_request_advisory_returns_none_without_adapter(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        result = boundary.request_advisory({"request": "test"})
        assert result is None

    def test_request_advisory_forwards_to_cognitia(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        mock_adapter = MockCognitiaAdapter()
        boundary = EdgeIntegrationBoundary(experiment=experiment, cognitia_adapter=mock_adapter)
        result = boundary.request_advisory({"request": "test"})
        assert result == {"advisory": "test"}
        assert len(mock_adapter.advisory_requests) == 1
