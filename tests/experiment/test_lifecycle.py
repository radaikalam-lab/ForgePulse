"""Tests for experiment lifecycle transitions."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import InvalidTransition
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
    Quantity,
)
from forgepulse.validation import validate_experiment


def _make_spec() -> ExperimentSpecification:
    return ExperimentSpecification(
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


class TestExperimentLifecycle:
    def test_initial_status_is_research_intent(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        assert experiment.status == ExperimentStatus.RESEARCH_INTENT

    def test_valid_transition_chain(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        assert experiment.status == ExperimentStatus.PROPOSED
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        assert experiment.status == ExperimentStatus.SPECIFIED
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        assert experiment.status == ExperimentStatus.VALIDATED
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        assert experiment.status == ExperimentStatus.SNAPSHOTTED
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        assert experiment.status == ExperimentStatus.QUEUED
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        assert experiment.status == ExperimentStatus.RUNNING
        experiment = experiment.transition(ExperimentStatus.COMPLETED)
        assert experiment.status == ExperimentStatus.COMPLETED
        experiment = experiment.transition(ExperimentStatus.MEASURED)
        assert experiment.status == ExperimentStatus.MEASURED

    def test_transition_records_history(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED, note="initial proposal")
        assert len(experiment.history) == 1
        assert experiment.history[0].from_status == ExperimentStatus.RESEARCH_INTENT
        assert experiment.history[0].to_status == ExperimentStatus.PROPOSED
        assert experiment.history[0].note == "initial proposal"

    def test_invalid_transition_raises(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.RUNNING)

    def test_cannot_transition_from_completed_to_proposed(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.COMPLETED)
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.PROPOSED)

    def test_aborted_has_no_outgoing_transitions(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.ABORTED)
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.COMPLETED)

    def test_failed_can_transition_to_measured(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.FAILED)
        experiment = experiment.transition(ExperimentStatus.MEASURED)
        assert experiment.status == ExperimentStatus.MEASURED

    def test_immutable_experiment(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        with pytest.raises(AttributeError):
            experiment.status = ExperimentStatus.RUNNING
