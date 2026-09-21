"""Tests for simulation."""

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
from forgepulse.measurement import SourceType
from forgepulse.simulation import Simulator, SimulatorResult


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


class TestSimulator:
    def test_simulated_source_explicitly_identified(self):
        simulator = Simulator()
        result = simulator.simulate(_make_spec(), "exec-001")
        for m in result.measurements:
            assert m.source_type == SourceType.SIMULATED
        for o in result.observations:
            assert o.source_type == SourceType.SIMULATED

    def test_simulator_cannot_masquerade_as_hardware(self):
        simulator = Simulator()
        result = simulator.simulate(_make_spec(), "exec-002")
        assert result.measurements[0].instrument_reference == "simulator"
        assert result.observations[0].source_type == SourceType.SIMULATED

    def test_simulator_deterministic_values(self):
        simulator = Simulator()
        result1 = simulator.simulate(_make_spec(), "exec-003")
        result2 = simulator.simulate(_make_spec(), "exec-003")
        assert result1.actual_process.measured_voltage == result2.actual_process.measured_voltage
        assert result1.measurements[0].values == result2.measurements[0].values
        assert result1.observations[0].voltage == result2.observations[0].voltage

    def test_simulator_rejects_empty_sequence(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        simulator = Simulator()
        with pytest.raises(ValueError):
            simulator.simulate(spec, "exec-004")
