"""Scientific experiment workflow and validation for ForgePulse.

This module provides:

1. WorkflowStage - enum for experiment workflow stages
2. StageResult - validation result for a single workflow stage
3. ScientificValidationResult - aggregate validation result
4. ExperimentWorkflow - immutable workflow state container
5. Validation functions for each workflow stage

The workflow stages are:
proposal → validation → snapshot → execution → measurement → derivation → characterization → interpretation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Optional

from forgepulse.common import _utc_now
from forgepulse.experiment import ExperimentSpecification, ValidatedExperimentSnapshot
from forgepulse.execution import Execution, ExecutionStatus
from forgepulse.interpretation import InterpretationResult
from forgepulse.measurement.models import (
    DerivedMeasurement,
    MeasurementSeries,
    ProvenanceReference,
    SourceType,
)
from forgepulse.provenance import LineageReference, ProvenanceRecord


class WorkflowStage(StrEnum):
    """Stages of the scientific experiment workflow."""

    PROPOSAL = "PROPOSAL"
    VALIDATED = "VALIDATED"
    SNAPSHOT = "SNAPSHOT"
    EXECUTED = "EXECUTED"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    CHARACTERIZED = "CHARACTERIZED"
    INTERPRETED = "INTERPRETED"


@dataclass(frozen=True)
class StageResult:
    """Validation result for a single workflow stage."""

    stage: WorkflowStage
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    completed_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware UTC")


@dataclass(frozen=True)
class ScientificValidationResult:
    """Aggregate validation result for the scientific workflow."""

    overall_valid: bool
    stage_results: tuple[StageResult, ...] = ()
    overall_errors: tuple[str, ...] = ()
    overall_warnings: tuple[str, ...] = ()
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    validated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.validated_at.tzinfo is None:
            raise ValueError("validated_at must be timezone-aware UTC")


@dataclass(frozen=True)
class ExperimentWorkflow:
    """Immutable container for the end-to-end experiment workflow.

    The workflow tracks the experiment through all stages:
    proposal → validation → snapshot → execution → measurement → derivation → characterization → interpretation
    """

    experiment_id: str
    specification: ExperimentSpecification
    snapshot: Optional[ValidatedExperimentSnapshot] = None
    execution: Optional[Execution] = None
    measurement_series: Optional[MeasurementSeries] = None
    derived_measurements: tuple[DerivedMeasurement, ...] = ()
    characterizations: tuple[object, ...] = ()
    interpretation: Optional[InterpretationResult] = None
    status: WorkflowStage = WorkflowStage.PROPOSAL
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.experiment_id or not self.experiment_id.strip():
            raise ValueError("experiment_id must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


def _validate_proposal(spec: ExperimentSpecification) -> StageResult:
    """Validate the proposal stage (structural checks only)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not spec.experiment_id.strip():
        errors.append("experiment_id must not be empty")
    if not spec.experiment_version.strip():
        errors.append("experiment_version must not be empty")
    if not spec.objective.description.strip():
        errors.append("objective.description must not be empty")
    if not spec.feedstock.material.strip():
        errors.append("feedstock.material must not be empty")
    if spec.feedstock.mass.value <= 0:
        errors.append("feedstock.mass must be positive")

    return StageResult(
        stage=WorkflowStage.PROPOSAL,
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_snapshot(snapshot: ValidatedExperimentSnapshot) -> StageResult:
    """Validate the snapshot stage."""
    errors: list[str] = []
    warnings: list[str] = []

    if not snapshot.experiment_id.strip():
        errors.append("snapshot.experiment_id must not be empty")
    if not snapshot.snapshot_id.strip():
        errors.append("snapshot.snapshot_id must not be empty")
    if not snapshot.validation_result.valid:
        errors.append("snapshot validation_result must be valid")

    return StageResult(
        stage=WorkflowStage.SNAPSHOT,
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_execution(execution: Execution) -> StageResult:
    """Validate the execution stage."""
    errors: list[str] = []
    warnings: list[str] = []

    if not execution.execution_id.strip():
        errors.append("execution.execution_id must not be empty")
    if execution.status == ExecutionStatus.QUEUED:
        warnings.append("execution is still queued")
    if execution.started_at is None:
        warnings.append("execution has not started")

    return StageResult(
        stage=WorkflowStage.EXECUTED,
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_measurement(series: MeasurementSeries) -> StageResult:
    """Validate the measurement stage."""
    errors: list[str] = []
    warnings: list[str] = []

    if not series.values:
        errors.append("measurement_series.values must not be empty")
    if not series.quantity.strip():
        errors.append("measurement_series.quantity must not be empty")
    if not series.unit.strip():
        errors.append("measurement_series.unit must not be empty")
    if series.source_type not in (SourceType.RAW, SourceType.MEASURED, SourceType.SIMULATED):
        errors.append(
            f"measurement_series.source_type must be RAW, MEASURED, or SIMULATED, got {series.source_type}"
        )

    return StageResult(
        stage=WorkflowStage.MEASURED,
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_derived(derived: DerivedMeasurement) -> StageResult:
    """Validate the derivation stage."""
    errors: list[str] = []
    warnings: list[str] = []

    if not derived.source_ids:
        errors.append("derived_measurement.source_ids must not be empty")
    if derived.source_type != SourceType.DERIVED:
        errors.append(
            f"derived_measurement.source_type must be DERIVED, got {derived.source_type}"
        )

    return StageResult(
        stage=WorkflowStage.DERIVED,
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _validate_interpretation(interp: InterpretationResult) -> StageResult:
    """Validate the interpretation stage."""
    errors: list[str] = []
    warnings: list[str] = []

    if not interp.proposition.strip():
        errors.append("interpretation.proposition must not be empty")
    if not interp.assumptions:
        warnings.append("interpretation has no explicit assumptions")
    if not interp.residuals and not interp.unknowns:
        warnings.append("interpretation has no residuals or unknowns documented")

    return StageResult(
        stage=WorkflowStage.INTERPRETED,
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_workflow(workflow: ExperimentWorkflow) -> ScientificValidationResult:
    """Validate an experiment workflow across all stages.

    This function performs deterministic validation of each workflow stage.
    It does not execute any experiments or claim scientific truth.

    Args:
        workflow: The experiment workflow to validate.

    Returns:
        A ScientificValidationResult with stage-by-stage results.
    """
    stage_results: list[StageResult] = []
    all_errors: list[str] = []
    all_warnings: list[str] = []

    proposal_result = _validate_proposal(workflow.specification)
    stage_results.append(proposal_result)
    all_errors.extend(proposal_result.errors)
    all_warnings.extend(proposal_result.warnings)

    if workflow.snapshot is not None:
        snapshot_result = _validate_snapshot(workflow.snapshot)
        stage_results.append(snapshot_result)
        all_errors.extend(snapshot_result.errors)
        all_warnings.extend(snapshot_result.warnings)

    if workflow.execution is not None:
        execution_result = _validate_execution(workflow.execution)
        stage_results.append(execution_result)
        all_errors.extend(execution_result.errors)
        all_warnings.extend(execution_result.warnings)

    if workflow.measurement_series is not None:
        measurement_result = _validate_measurement(workflow.measurement_series)
        stage_results.append(measurement_result)
        all_errors.extend(measurement_result.errors)
        all_warnings.extend(measurement_result.warnings)

    for derived in workflow.derived_measurements:
        derived_result = _validate_derived(derived)
        stage_results.append(derived_result)
        all_errors.extend(derived_result.errors)
        all_warnings.extend(derived_result.warnings)

    if workflow.interpretation is not None:
        interp_result = _validate_interpretation(workflow.interpretation)
        stage_results.append(interp_result)
        all_errors.extend(interp_result.errors)
        all_warnings.extend(interp_result.warnings)

    return ScientificValidationResult(
        overall_valid=len(all_errors) == 0,
        stage_results=tuple(stage_results),
        overall_errors=tuple(all_errors),
        overall_warnings=tuple(all_warnings),
    )
