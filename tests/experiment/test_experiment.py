"""Tests for experiment domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.experiment import (
    Additive,
    Atmosphere,
    Chamber,
    ExperimentObjective,
    ExperimentSpecification,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
    MeasurementRequirement,
    CharacterizationRequirement,
    ExperimentStatus,
    ValidatedExperimentSnapshot,
)
from forgepulse.provenance import ProvenanceRecord
from forgepulse.validation import ValidationResult, validate_experiment


def _make_base_spec(experiment_id="exp-001", experiment_version="1.0.0") -> ExperimentSpecification:
    return ExperimentSpecification(
        experiment_id=experiment_id,
        experiment_version=experiment_version,
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


class TestExperimentIdentity:
    def test_experiment_id_and_version_are_set(self):
        spec = _make_base_spec()
        assert spec.experiment_id == "exp-001"
        assert spec.experiment_version == "1.0.0"
        assert spec.schema_version == "1.0.0"

    def test_created_at_is_utc(self):
        spec = _make_base_spec()
        assert spec.created_at.tzinfo is not None

    def test_different_versions_are_distinct(self):
        spec_v1 = _make_base_spec(experiment_version="1.0.0")
        spec_v2 = _make_base_spec(experiment_version="2.0.0")
        assert spec_v1.experiment_version != spec_v2.experiment_version


class TestPulseSequence:
    def test_pulse_sequence_is_deterministic(self):
        spec1 = _make_base_spec()
        spec2 = _make_base_spec()
        assert spec1.pulse_sequence == spec2.pulse_sequence
        assert spec1.pulse_sequence.pulses[0].target_voltage == spec2.pulse_sequence.pulses[0].target_voltage

    def test_pulse_sequence_metadata(self):
        spec = _make_base_spec()
        seq = PulseSequence(
            pulses=spec.pulse_sequence.pulses,
            inter_pulse_interval=spec.pulse_sequence.inter_pulse_interval,
            metadata={"mode": "single"},
        )
        assert seq.metadata["mode"] == "single"


class TestFeedstock:
    def test_feedstock_with_additives(self):
        feedstock = Feedstock(
            material="carbon black",
            mass=Quantity(value=0.5, unit="g"),
            additives=(Additive(material="catalyst", mass=Quantity(value=0.01, unit="g")),),
        )
        assert len(feedstock.additives) == 1
        assert feedstock.additives[0].material == "catalyst"


class TestImmutability:
    def test_experiment_spec_is_frozen(self):
        spec = _make_base_spec()
        with pytest.raises(AttributeError):
            spec.experiment_id = "new-id"

    def test_pulse_is_frozen(self):
        pulse = Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s"))
        with pytest.raises(AttributeError):
            pulse.target_voltage = Quantity(value=130.0, unit="V")


class TestValidatedSnapshot:
    def test_snapshot_creation(self):
        spec = _make_base_spec()
        result = validate_experiment(spec)
        snapshot = ValidatedExperimentSnapshot(
            experiment_id=spec.experiment_id,
            experiment_version=spec.experiment_version,
            schema_version=spec.schema_version,
            specification=spec,
            validation_result=result,
            validator_id="forgepulse-validator-v1",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            checksum="abc123",
        )
        assert snapshot.experiment_id == "exp-001"
        assert snapshot.checksum == "abc123"

    def test_snapshot_is_frozen(self):
        spec = _make_base_spec()
        result = validate_experiment(spec)
        snapshot = ValidatedExperimentSnapshot(
            experiment_id=spec.experiment_id,
            experiment_version=spec.experiment_version,
            schema_version=spec.schema_version,
            specification=spec,
            validation_result=result,
            validator_id="forgepulse-validator-v1",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            checksum="abc123",
        )
        with pytest.raises(AttributeError):
            snapshot.checksum = "def456"
