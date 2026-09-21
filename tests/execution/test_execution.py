"""Tests for execution domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.execution import ActualProcess, Execution, ExecutionStatus, TargetProcess
from forgepulse.experiment import ExperimentSpecification, ExperimentObjective, Feedstock, Pulse, PulseSequence, ProcessConstraint, Atmosphere, Chamber
from forgepulse.experiment import ExperimentObjective


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


class TestTargetVsActual:
    def test_target_and_actual_are_distinct(self):
        spec = _make_spec()
        target = TargetProcess(voltage=Quantity(value=120.0, unit="V"))
        actual = ActualProcess(measured_voltage=Quantity(value=118.7, unit="V"))
        execution = Execution(
            execution_id="exec-001",
            snapshot=spec,
            target_process=target,
            actual_process=actual,
        )
        assert execution.target_process.voltage.value == 120.0
        assert execution.actual_process.measured_voltage.value == 118.7

    def test_target_not_overwritten_by_actual(self):
        spec = _make_spec()
        target = TargetProcess(voltage=Quantity(value=120.0, unit="V"))
        actual = ActualProcess(measured_voltage=Quantity(value=100.0, unit="V"))
        execution = Execution(
            execution_id="exec-002",
            snapshot=spec,
            target_process=target,
            actual_process=actual,
        )
        assert execution.target_process.voltage.value == 120.0
        assert execution.actual_process.measured_voltage.value == 100.0


class TestExecutionStatus:
    def test_default_status_is_queued(self):
        spec = _make_spec()
        execution = Execution(execution_id="exec-003", snapshot=spec)
        assert execution.status == ExecutionStatus.QUEUED

    def test_status_transitions(self):
        spec = _make_spec()
        execution = Execution(execution_id="exec-004", snapshot=spec, status=ExecutionStatus.COMPLETED)
        assert execution.status == ExecutionStatus.COMPLETED
