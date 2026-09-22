"""Tests for execution domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.execution import ActualProcess, Execution, ExecutionStatus, TargetProcess
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
from forgepulse.validation import SnapshotValidator


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


def _make_snapshot() -> "ValidatedExperimentSnapshot":
    spec = _make_spec()
    validator = SnapshotValidator()
    return validator.create_snapshot(spec)


class TestTargetVsActual:
    def test_target_and_actual_are_distinct(self):
        snapshot = _make_snapshot()
        target = TargetProcess(voltage=Quantity(value=120.0, unit="V"))
        actual = ActualProcess(measured_voltage=Quantity(value=118.7, unit="V"))
        execution = Execution(
            execution_id="exec-001",
            snapshot=snapshot,
            target_process=target,
            actual_process=actual,
        )
        assert execution.target_process.voltage.value == 120.0
        assert execution.actual_process.measured_voltage.value == 118.7

    def test_target_not_overwritten_by_actual(self):
        snapshot = _make_snapshot()
        target = TargetProcess(voltage=Quantity(value=120.0, unit="V"))
        actual = ActualProcess(measured_voltage=Quantity(value=100.0, unit="V"))
        execution = Execution(
            execution_id="exec-002",
            snapshot=snapshot,
            target_process=target,
            actual_process=actual,
        )
        assert execution.target_process.voltage.value == 120.0
        assert execution.actual_process.measured_voltage.value == 100.0


class TestExecutionStatus:
    def test_default_status_is_queued(self):
        snapshot = _make_snapshot()
        execution = Execution(execution_id="exec-003", snapshot=snapshot)
        assert execution.status == ExecutionStatus.QUEUED

    def test_status_transitions(self):
        snapshot = _make_snapshot()
        execution = Execution(execution_id="exec-004", snapshot=snapshot, status=ExecutionStatus.COMPLETED)
        assert execution.status == ExecutionStatus.COMPLETED
