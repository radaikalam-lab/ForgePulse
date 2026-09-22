"""Tests for scientific workflow validation."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.execution import Execution, ExecutionStatus
from forgepulse.experiment import (
    Atmosphere,
    Chamber,
    ExperimentObjective,
    ExperimentSpecification,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
    ValidatedExperimentSnapshot,
)
from forgepulse.interpretation import (
    Evidence,
    Hypothesis,
    InterpretationResult,
    InterpretationStatus,
    ProvenanceReference,
)
from forgepulse.measurement.models import (
    DerivedMeasurement,
    MeasurementSeries,
    SourceType,
)
from forgepulse.validation import (
    ValidationResult,
    validate_experiment,
)
from forgepulse.validation.snapshot import SnapshotValidator
from forgepulse.validation.workflow import (
    ExperimentWorkflow,
    ScientificValidationResult,
    StageResult,
    WorkflowStage,
    _validate_derived,
    _validate_execution,
    _validate_interpretation,
    _validate_measurement,
    _validate_proposal,
    _validate_snapshot,
    validate_workflow,
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


def _make_valid_series() -> MeasurementSeries:
    return MeasurementSeries(
        measurement_id="meas-001",
        quantity="voltage",
        values=[120.0, 115.0, 110.0],
        unit="V",
        start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        source_type=SourceType.RAW,
    )


def _make_valid_derived() -> DerivedMeasurement:
    return DerivedMeasurement(
        measurement_id="derived-001",
        quantity="power",
        value=Quantity(value=120.0, unit="W"),
        source_ids=("meas-001",),
        transformation="multiply_voltage_current",
        source_type=SourceType.DERIVED,
    )


def _make_valid_interpretation() -> InterpretationResult:
    return InterpretationResult(
        interpretation_id="int-001",
        subject_reference="mat-001",
        proposition="Test interpretation",
        assumptions=("assumption-1",),
        residuals=("residual-1",),
        unknowns=("unknown-1",),
    )


class TestWorkflowStage:
    def test_workflow_stage_values(self):
        expected = {
            "PROPOSAL",
            "VALIDATED",
            "SNAPSHOT",
            "EXECUTED",
            "MEASURED",
            "DERIVED",
            "CHARACTERIZED",
            "INTERPRETED",
        }
        actual = {s.value for s in WorkflowStage}
        assert actual == expected


class TestStageResult:
    def test_stage_result_creation(self):
        result = StageResult(
            stage=WorkflowStage.PROPOSAL,
            valid=True,
        )
        assert result.stage == WorkflowStage.PROPOSAL
        assert result.valid is True
        assert result.errors == ()
        assert result.warnings == ()

    def test_stage_result_with_errors(self):
        result = StageResult(
            stage=WorkflowStage.PROPOSAL,
            valid=False,
            errors=("error-1", "error-2"),
        )
        assert result.valid is False
        assert len(result.errors) == 2

    def test_stage_result_requires_utc(self):
        with pytest.raises(ValueError, match="completed_at must be timezone-aware UTC"):
            StageResult(
                stage=WorkflowStage.PROPOSAL,
                valid=True,
                completed_at=datetime(2026, 1, 1),
            )


class TestScientificValidationResult:
    def test_scientific_validation_result_creation(self):
        result = ScientificValidationResult(
            overall_valid=True,
        )
        assert result.overall_valid is True
        assert result.stage_results == ()
        assert result.overall_errors == ()
        assert result.overall_warnings == ()

    def test_scientific_validation_result_requires_utc(self):
        with pytest.raises(ValueError, match="validated_at must be timezone-aware UTC"):
            ScientificValidationResult(
                overall_valid=True,
                validated_at=datetime(2026, 1, 1),
            )


class TestExperimentWorkflow:
    def test_workflow_creation(self):
        spec = _make_valid_spec()
        workflow = ExperimentWorkflow(
            experiment_id="exp-001",
            specification=spec,
        )
        assert workflow.experiment_id == "exp-001"
        assert workflow.status == WorkflowStage.PROPOSAL
        assert workflow.derived_measurements == ()
        assert workflow.characterizations == ()
        assert workflow.interpretation is None

    def test_workflow_requires_non_empty_experiment_id(self):
        spec = _make_valid_spec()
        with pytest.raises(ValueError, match="experiment_id must be a non-empty string"):
            ExperimentWorkflow(
                experiment_id="",
                specification=spec,
            )

    def test_workflow_requires_utc_created_at(self):
        spec = _make_valid_spec()
        with pytest.raises(ValueError, match="created_at must be timezone-aware UTC"):
            ExperimentWorkflow(
                experiment_id="exp-001",
                specification=spec,
                created_at=datetime(2026, 1, 1),
            )


class TestValidateProposal:
    def test_valid_proposal(self):
        spec = _make_valid_spec()
        result = _validate_proposal(spec)
        assert result.stage == WorkflowStage.PROPOSAL
        assert result.valid is True

    def test_empty_experiment_id(self):
        spec = _make_valid_spec()
        spec = replace(spec, experiment_id="")
        result = _validate_proposal(spec)
        assert result.valid is False
        assert any("experiment_id" in e for e in result.errors)

    def test_empty_objective_description(self):
        spec = _make_valid_spec()
        spec = replace(spec, objective=ExperimentObjective(description=""))
        result = _validate_proposal(spec)
        assert result.valid is False
        assert any("objective" in e for e in result.errors)


class TestValidateSnapshot:
    def test_valid_snapshot(self):
        spec = _make_valid_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        result = _validate_snapshot(snapshot)
        assert result.stage == WorkflowStage.SNAPSHOT
        assert result.valid is True

    def test_invalid_snapshot(self):
        spec = _make_valid_spec()
        snapshot = ValidatedExperimentSnapshot(
            experiment_id="",
            snapshot_id="snap-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            specification=spec,
            validation_result=ValidationResult(valid=False),
            validator_id="forgepulse-validator-v1",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            checksum="abc123",
        )
        result = _validate_snapshot(snapshot)
        assert result.valid is False
        assert any("experiment_id" in e for e in result.errors)


class TestValidateExecution:
    def test_valid_execution(self):
        spec = _make_valid_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        execution = Execution(
            execution_id="exec-001",
            snapshot=snapshot,
            status=ExecutionStatus.COMPLETED,
            started_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 15, 10, 35, 0, tzinfo=timezone.utc),
        )
        result = _validate_execution(execution)
        assert result.stage == WorkflowStage.EXECUTED
        assert result.valid is True

    def test_queued_execution_warns(self):
        spec = _make_valid_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        execution = Execution(
            execution_id="exec-001",
            snapshot=snapshot,
            status=ExecutionStatus.QUEUED,
        )
        result = _validate_execution(execution)
        assert result.valid is True
        assert any("queued" in w for w in result.warnings)


class TestValidateMeasurement:
    def test_valid_measurement(self):
        series = _make_valid_series()
        result = _validate_measurement(series)
        assert result.stage == WorkflowStage.MEASURED
        assert result.valid is True

    def test_empty_values(self):
        series = MeasurementSeries(
            measurement_id="meas-001",
            quantity="voltage",
            values=[],
            unit="V",
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.RAW,
        )
        result = _validate_measurement(series)
        assert result.valid is False
        assert any("values must not be empty" in e for e in result.errors)

    def test_invalid_source_type(self):
        series = MeasurementSeries(
            measurement_id="meas-001",
            quantity="voltage",
            values=[120.0],
            unit="V",
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.INTERPRETED,
        )
        result = _validate_measurement(series)
        assert result.valid is False
        assert any("source_type" in e for e in result.errors)


class TestValidateDerived:
    def test_valid_derived(self):
        derived = _make_valid_derived()
        result = _validate_derived(derived)
        assert result.stage == WorkflowStage.DERIVED
        assert result.valid is True

    def test_empty_source_ids(self):
        derived = DerivedMeasurement(
            measurement_id="derived-001",
            quantity="power",
            value=Quantity(value=120.0, unit="W"),
            source_ids=(),
            source_type=SourceType.DERIVED,
        )
        result = _validate_derived(derived)
        assert result.valid is False
        assert any("source_ids" in e for e in result.errors)

    def test_wrong_source_type(self):
        derived = DerivedMeasurement(
            measurement_id="derived-001",
            quantity="power",
            value=Quantity(value=120.0, unit="W"),
            source_ids=("meas-001",),
            source_type=SourceType.RAW,
        )
        result = _validate_derived(derived)
        assert result.valid is False
        assert any("source_type" in e for e in result.errors)


class TestValidateInterpretation:
    def test_valid_interpretation(self):
        interp = _make_valid_interpretation()
        result = _validate_interpretation(interp)
        assert result.stage == WorkflowStage.INTERPRETED
        assert result.valid is True

    def test_no_assumptions_warns(self):
        interp = InterpretationResult(
            interpretation_id="int-001",
            subject_reference="mat-001",
            proposition="Test interpretation",
        )
        result = _validate_interpretation(interp)
        assert result.valid is True
        assert any("assumptions" in w for w in result.warnings)

    def test_no_residuals_or_unknowns_warns(self):
        interp = InterpretationResult(
            interpretation_id="int-001",
            subject_reference="mat-001",
            proposition="Test interpretation",
            assumptions=("assumption-1",),
        )
        result = _validate_interpretation(interp)
        assert result.valid is True
        assert any("residuals or unknowns" in w for w in result.warnings)


class TestValidateWorkflow:
    def test_valid_workflow(self):
        spec = _make_valid_spec()
        workflow = ExperimentWorkflow(
            experiment_id="exp-001",
            specification=spec,
            measurement_series=_make_valid_series(),
            derived_measurements=(_make_valid_derived(),),
            interpretation=_make_valid_interpretation(),
        )
        result = validate_workflow(workflow)
        assert result.overall_valid is True
        assert len(result.overall_errors) == 0

    def test_workflow_with_invalid_spec(self):
        spec = _make_valid_spec()
        spec = replace(spec, experiment_id="")
        workflow = ExperimentWorkflow(
            experiment_id="exp-001",
            specification=spec,
        )
        result = validate_workflow(workflow)
        assert result.overall_valid is False
        assert any("experiment_id" in e for e in result.overall_errors)

    def test_workflow_with_invalid_measurement(self):
        spec = _make_valid_spec()
        series = MeasurementSeries(
            measurement_id="meas-001",
            quantity="voltage",
            values=[],
            unit="V",
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.RAW,
        )
        workflow = ExperimentWorkflow(
            experiment_id="exp-001",
            specification=spec,
            measurement_series=series,
        )
        result = validate_workflow(workflow)
        assert result.overall_valid is False
        assert any("values must not be empty" in e for e in result.overall_errors)

    def test_workflow_with_multiple_stage_errors(self):
        spec = _make_valid_spec()
        spec = replace(spec, experiment_id="")
        series = MeasurementSeries(
            measurement_id="meas-001",
            quantity="voltage",
            values=[],
            unit="V",
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.RAW,
        )
        workflow = ExperimentWorkflow(
            experiment_id="exp-001",
            specification=spec,
            measurement_series=series,
        )
        result = validate_workflow(workflow)
        assert result.overall_valid is False
        assert len(result.overall_errors) >= 2
