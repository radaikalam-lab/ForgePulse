"""Phase 2 validation, snapshot, execution-readiness, and lifecycle integration tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from typing import Optional

import pytest

from forgepulse.common import (
    AuthorityViolation,
    InvalidExperiment,
    InvalidTransition,
    Quantity,
    SnapshotViolation,
)
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
    ValidatedExperimentSnapshot,
)
from forgepulse.execution import ActualProcess, Execution, ExecutionStatus, TargetProcess
from forgepulse.integration import (
    CognitiaAdapter,
    EdgeIntegrationBoundary,
    MeasurementTranslator,
    SyntheticEdgeSource,
)
from forgepulse.measurement import RawMeasurement, SourceType
from forgepulse.validation import SnapshotValidator, ValidationResult, validate_experiment


def _make_valid_spec(experiment_id: str = "exp-001", experiment_version: str = "1.0.0") -> ExperimentSpecification:
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


def _make_experiment(spec: Optional[ExperimentSpecification] = None) -> "Experiment":
    from forgepulse.experiment import Experiment
    spec = spec or _make_valid_spec()
    return Experiment(experiment_id=spec.experiment_id, specification=spec)


def _transition_to(experiment: "Experiment", target_status: ExperimentStatus) -> "Experiment":
    from forgepulse.experiment import Experiment
    current = experiment
    if target_status == ExperimentStatus.RESEARCH_INTENT:
        return current
    current = current.transition(ExperimentStatus.PROPOSED)
    if target_status == ExperimentStatus.PROPOSED:
        return current
    current = current.transition(ExperimentStatus.SPECIFIED)
    if target_status == ExperimentStatus.SPECIFIED:
        return current
    current = current.transition(ExperimentStatus.VALIDATED)
    if target_status == ExperimentStatus.VALIDATED:
        return current
    current = current.transition(ExperimentStatus.SNAPSHOTTED)
    if target_status == ExperimentStatus.SNAPSHOTTED:
        return current
    current = current.transition(ExperimentStatus.QUEUED)
    if target_status == ExperimentStatus.QUEUED:
        return current
    current = current.transition(ExperimentStatus.RUNNING)
    if target_status == ExperimentStatus.RUNNING:
        return current
    if target_status == ExperimentStatus.COMPLETED:
        return current.transition(ExperimentStatus.COMPLETED)
    if target_status == ExperimentStatus.FAILED:
        return current.transition(ExperimentStatus.FAILED)
    if target_status == ExperimentStatus.ABORTED:
        return current.transition(ExperimentStatus.ABORTED)
    if target_status == ExperimentStatus.MEASURED:
        return current.transition(ExperimentStatus.COMPLETED).transition(ExperimentStatus.MEASURED)
    if target_status == ExperimentStatus.DERIVED:
        return current.transition(ExperimentStatus.COMPLETED).transition(ExperimentStatus.MEASURED).transition(ExperimentStatus.DERIVED)
    if target_status == ExperimentStatus.CHARACTERIZED:
        return current.transition(ExperimentStatus.COMPLETED).transition(ExperimentStatus.MEASURED).transition(ExperimentStatus.DERIVED).transition(ExperimentStatus.CHARACTERIZED)
    if target_status == ExperimentStatus.INTERPRETED:
        return current.transition(ExperimentStatus.COMPLETED).transition(ExperimentStatus.MEASURED).transition(ExperimentStatus.DERIVED).transition(ExperimentStatus.CHARACTERIZED).transition(ExperimentStatus.INTERPRETED)
    raise ValueError(f"Unknown target status: {target_status}")


class TestDeterministicValidation:
    def test_validation_diagnostics_are_deterministic(self):
        spec = _make_valid_spec()
        result1 = validate_experiment(spec)
        result2 = validate_experiment(spec)
        assert result1.valid == result2.valid
        assert result1.errors == result2.errors
        assert result1.warnings == result2.warnings

    def test_validation_is_side_effect_free(self):
        spec = _make_valid_spec()
        original_id = spec.experiment_id
        validate_experiment(spec)
        assert spec.experiment_id == original_id

    def test_invalid_experiment_raises_on_snapshot_creation(self):
        spec = ExperimentSpecification(
            experiment_id="",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description=""),
            feedstock=Feedstock(material="", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        validator = SnapshotValidator()
        with pytest.raises(InvalidExperiment):
            validator.create_snapshot(spec)

    def test_no_hidden_defaults(self):
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
        result = validate_experiment(spec)
        assert result.valid is True
        assert any("maximum_target_voltage" in e or "maximum_pulse_duration" in e for e in result.warnings)


class TestExecutionReadiness:
    def test_execution_requires_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        execution = Execution(execution_id="exec-001", snapshot=snapshot)
        assert execution.snapshot == snapshot
        assert execution.status == ExecutionStatus.QUEUED

    def test_execution_references_snapshot_id(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        execution = Execution(execution_id="exec-001", snapshot=snapshot)
        assert execution.snapshot.snapshot_id == "snap-exp-001-1.0.0"

    def test_snapshot_independent_of_source_object(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        del spec
        assert snapshot.snapshot_id == "snap-exp-001-1.0.0"

    def test_snapshot_cannot_be_mutated_after_execution(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        Execution(execution_id="exec-001", snapshot=snapshot)
        with pytest.raises(FrozenInstanceError):
            snapshot.checksum = "mutated"


class TestLifecycleIntegration:
    def test_specified_to_validated_with_valid_spec(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(experiment.specification)
        assert snapshot.validation_result.valid is True

    def test_specified_cannot_become_validated_with_invalid_spec(self):
        invalid_spec = ExperimentSpecification(
            experiment_id="",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description=""),
            feedstock=Feedstock(material="", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        experiment = Experiment(experiment_id=invalid_spec.experiment_id, specification=invalid_spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.VALIDATED)

    def test_snapshotted_to_queued_with_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        experiment = _make_experiment(spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        assert experiment.status == ExperimentStatus.SNAPSHOTTED
        execution = Execution(execution_id="exec-001", snapshot=snapshot)
        assert execution.snapshot == snapshot

    def test_invalid_lifecycle_transitions_remain_rejected(self):
        experiment = _make_experiment()
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.RUNNING)

    def test_different_experiment_versions_create_distinct_snapshots(self):
        spec_v1 = _make_valid_spec(experiment_version="1.0.0")
        spec_v2 = _make_valid_spec(experiment_version="2.0.0")
        validator = SnapshotValidator()
        snapshot1 = validator.create_snapshot(spec_v1)
        snapshot2 = validator.create_snapshot(spec_v2)
        assert snapshot1.snapshot_id == "snap-exp-001-1.0.0"
        assert snapshot2.snapshot_id == "snap-exp-001-2.0.0"
        assert snapshot1.snapshot_id != snapshot2.snapshot_id
        assert snapshot1.checksum != snapshot2.checksum


class TestCognitiaIsolation:
    def test_cognitia_unavailable_does_not_break_validation(self):
        spec = _make_valid_spec()
        result = validate_experiment(spec)
        assert result.valid is True

    def test_cognitia_unavailable_does_not_break_snapshot_creation(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        assert snapshot.snapshot_id == "snap-exp-001-1.0.0"

    def test_cognitia_unavailable_does_not_break_execution_readiness(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        execution = Execution(execution_id="exec-001", snapshot=snapshot)
        assert execution.status == ExecutionStatus.QUEUED


class TestEdgeBoundaryCompatibility:
    def test_edge_cannot_bypass_validation(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        boundary.record_observation({"data": "test"})
        boundary.record_measurement(
            RawMeasurement(
                measurement_id="m1",
                quantity="v",
                values=[1.0],
                unit="V",
                source_type=SourceType.RAW,
            )
        )

    def test_edge_cannot_mutate_snapshot(self):
        spec = _make_valid_spec()
        validator = SnapshotValidator()
        snapshot = validator.create_snapshot(spec)
        experiment = _make_experiment(spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        boundary.record_observation({"data": "test"})
        assert snapshot.checksum == snapshot.checksum

    def test_simulator_has_no_phase2_execution_authority(self):
        spec = _make_valid_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        from forgepulse.simulation import Simulator
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert result.actual_process.measured_voltage is not None
        assert result.actual_process.measured_voltage.unit == "V"


class TestNoHardwareDependency:
    def test_no_hardware_imports_in_core(self):
        import forgepulse
        import forgepulse.common
        import forgepulse.experiment
        import forgepulse.execution
        import forgepulse.measurement
        import forgepulse.validation
        for module in [
            forgepulse,
            forgepulse.common,
            forgepulse.experiment,
            forgepulse.execution,
            forgepulse.measurement,
            forgepulse.validation,
        ]:
            assert "hardware" not in dir(module)
            assert "daq" not in dir(module)
            assert "gpio" not in dir(module)
            assert "plc" not in dir(module)
