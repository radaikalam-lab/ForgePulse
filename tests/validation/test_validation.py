"""Tests for validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.experiment import (
    Atmosphere,
    Chamber,
    ExperimentObjective,
    ExperimentSpecification,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
)
from forgepulse.validation import (
    ConstraintViolation,
    InvalidExperiment,
    InvalidPulseSequence,
    ValidationResult,
    validate_experiment,
)


def _make_valid_spec() -> ExperimentSpecification:
    return ExperimentSpecification(
        experiment_id="exp-001",
        experiment_version="1.0.0",
        schema_version="1.0.0",
        created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        objective=ExperimentObjective(description="Test experiment"),
        feedstock=Feedstock(
            material="carbon black",
            mass=Quantity(value=0.5, unit="g"),
        ),
        chamber=Chamber(
            geometry="tubular",
            atmosphere=Atmosphere(gas="argon"),
        ),
        pulse_sequence=PulseSequence(
            pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
            inter_pulse_interval=Quantity(value=1.0, unit="s"),
        ),
        process_constraints=ProcessConstraint(
            maximum_target_voltage=Quantity(value=150.0, unit="V"),
            maximum_pulse_duration=Quantity(value=0.1, unit="s"),
        ),
    )


class TestValidExperiment:
    def test_valid_experiment(self):
        spec = _make_valid_spec()
        result = validate_experiment(spec)
        assert result.valid is True
        assert len(result.errors) == 0


class TestInvalidExperiment:
    def test_empty_experiment_id(self):
        spec = ExperimentSpecification(
            experiment_id="",
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
        result = validate_experiment(spec)
        assert result.valid is False
        assert any("experiment_id" in e for e in result.errors)

    def test_empty_objective_description(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description=""),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        result = validate_experiment(spec)
        assert result.valid is False
        assert any("objective" in e for e in result.errors)

    def test_negative_pulse_voltage(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=-10.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        result = validate_experiment(spec)
        assert result.valid is False
        assert any("positive" in e for e in result.errors)

    def test_negative_pulse_duration(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=-0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        result = validate_experiment(spec)
        assert result.valid is False
        assert any("positive" in e for e in result.errors)


class TestDeterministicValidation:
    def test_validation_is_deterministic(self):
        spec = _make_valid_spec()
        result1 = validate_experiment(spec)
        result2 = validate_experiment(spec)
        assert result1.valid == result2.valid
        assert result1.errors == result2.errors
        assert result1.warnings == result2.warnings

    def test_validation_does_not_execute(self):
        spec = _make_valid_spec()
        result = validate_experiment(spec)
        assert isinstance(result, ValidationResult)
        assert result.valid is True


class TestConstraintViolation:
    def test_voltage_exceeds_maximum(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=200.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(
                maximum_target_voltage=Quantity(value=150.0, unit="V"),
            ),
        )
        result = validate_experiment(spec)
        assert result.valid is False
        assert any("maximum_target_voltage" in e for e in result.errors)

    def test_duration_exceeds_maximum(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.2, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(
                maximum_pulse_duration=Quantity(value=0.1, unit="s"),
            ),
        )
        result = validate_experiment(spec)
        assert result.valid is False
        assert any("maximum_pulse_duration" in e for e in result.errors)
