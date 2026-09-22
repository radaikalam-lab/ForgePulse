"""Tests for immutable validated experiment snapshots."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from forgepulse.common import Quantity, SnapshotViolation
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
from forgepulse.validation import SnapshotValidator, ValidationResult, validate_experiment


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


class TestSnapshotCreation:
    def test_valid_experiment_creates_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        assert snapshot.snapshot_id == "snap-exp-001-1.0.0"
        assert snapshot.experiment_id == "exp-001"
        assert snapshot.experiment_version == "1.0.0"
        assert snapshot.schema_version == "1.0.0"
        assert snapshot.validation_result.valid is True
        assert snapshot.validator_id == "forgepulse-validator-v1"
        assert snapshot.checksum != ""
        assert isinstance(snapshot.created_at, datetime)
        assert snapshot.created_at.tzinfo is not None

    def test_invalid_experiment_cannot_create_snapshot(self):
        spec = ExperimentSpecification(
            experiment_id="",
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
        validator = SnapshotValidator()
        with pytest.raises(Exception):
            validator.create_snapshot(spec)


class TestSnapshotImmutability:
    def test_snapshot_is_frozen(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        with pytest.raises(FrozenInstanceError):
            snapshot.checksum = "new-checksum"

    def test_snapshot_specification_metadata_is_immutable(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        with pytest.raises(TypeError):
            snapshot.specification.metadata["key"] = "value"

    def test_snapshot_does_not_share_mutable_state_with_source(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        assert isinstance(snapshot.specification.metadata, MappingProxyType)

    def test_modifying_source_does_not_affect_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        spec.metadata["new_key"] = "new_value"
        assert "new_key" not in dict(snapshot.specification.metadata)


class TestSnapshotIndependence:
    def test_snapshot_survives_source_discard(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        del spec
        assert snapshot.snapshot_id == "snap-exp-001-1.0.0"
        assert snapshot.experiment_id == "exp-001"


class TestDeterministicSerialization:
    def test_snapshot_serialization_is_deterministic(self):
        from forgepulse.common import to_canonical_json
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        json1 = to_canonical_json(snapshot)
        json2 = to_canonical_json(snapshot)
        assert json1 == json2

    def test_snapshot_serialization_has_no_nan_or_inf(self):
        from forgepulse.common import to_canonical_json
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        json_str = to_canonical_json(snapshot)
        assert "NaN" not in json_str
        assert "Infinity" not in json_str
        assert "-Infinity" not in json_str


class TestChecksumStability:
    def test_identical_snapshots_have_same_checksum(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot1 = validator.create_snapshot(spec)
        snapshot2 = validator.create_snapshot(spec)
        assert snapshot1.checksum == snapshot2.checksum

    def test_checksum_changes_when_specification_changes(self):
        spec1 = _make_valid_spec()
        spec2 = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Modified experiment"),
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
        validator = SnapshotValidator()
        snapshot1 = validator.create_snapshot(spec1)
        snapshot2 = validator.create_snapshot(spec2)
        assert snapshot1.checksum != snapshot2.checksum

    def test_verify_checksum_returns_true_for_valid_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        assert validator.verify_checksum(snapshot) is True


class TestSnapshotIdentity:
    def test_snapshot_id_is_deterministic(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot1 = validator.create_snapshot(spec)
        snapshot2 = validator.create_snapshot(spec)
        assert snapshot1.snapshot_id == snapshot2.snapshot_id

    def test_snapshot_id_differs_by_version(self):
        spec_v1 = _make_valid_spec()
        spec_v2 = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="2.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(
                maximum_target_voltage=Quantity(value=150.0, unit="V"),
                maximum_pulse_duration=Quantity(value=0.1, unit="s"),
            ),
        )
        validator = SnapshotValidator()
        snapshot_v1 = validator.create_snapshot(spec_v1)
        snapshot_v2 = validator.create_snapshot(spec_v2)
        assert snapshot_v1.snapshot_id == "snap-exp-001-1.0.0"
        assert snapshot_v2.snapshot_id == "snap-exp-001-2.0.0"
        assert snapshot_v1.snapshot_id != snapshot_v2.snapshot_id

    def test_snapshot_id_differs_by_experiment_id(self):
        spec_a = _make_valid_spec()
        spec_b = ExperimentSpecification(
            experiment_id="exp-002",
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
            process_constraints=ProcessConstraint(
                maximum_target_voltage=Quantity(value=150.0, unit="V"),
                maximum_pulse_duration=Quantity(value=0.1, unit="s"),
            ),
        )
        validator = SnapshotValidator()
        snapshot_a = validator.create_snapshot(spec_a)
        snapshot_b = validator.create_snapshot(spec_b)
        assert snapshot_a.snapshot_id == "snap-exp-001-1.0.0"
        assert snapshot_b.snapshot_id == "snap-exp-002-1.0.0"
        assert snapshot_a.snapshot_id != snapshot_b.snapshot_id


class TestSnapshotProvenance:
    def test_snapshot_contains_experiment_identity(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        assert snapshot.experiment_id == spec.experiment_id
        assert snapshot.experiment_version == spec.experiment_version
        assert snapshot.schema_version == spec.schema_version

    def test_snapshot_contains_validation_result(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        assert snapshot.validation_result.valid is True
        assert snapshot.validation_result.errors == ()
        assert snapshot.validation_result.warnings == ()
        assert snapshot.validation_result.validator_id == "forgepulse-validator-v1"

    def test_snapshot_contains_validator_metadata(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator(validator_id="custom-validator", validator_version="2.0.0")
        snapshot = validator.create_snapshot(spec)
        assert snapshot.validator_id == "custom-validator"
        assert snapshot.created_at.tzinfo is not None


class TestValidationSideEffects:
    def test_validation_does_not_mutate_specification(self):
        spec = _make_valid_spec()
        original_id = spec.experiment_id
        validate_experiment(spec)
        assert spec.experiment_id == original_id

    def test_validation_does_not_mutate_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        original_checksum = snapshot.checksum
        validate_experiment(spec)
        assert snapshot.checksum == original_checksum
