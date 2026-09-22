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
    ValidatedExperimentSnapshot,
)
from forgepulse.execution import ActualProcess, TargetProcess
from forgepulse.measurement import (
    ElectricalObservation,
    MeasurementSeries,
    RawMeasurement,
    SourceType,
    ThermalObservation,
)
from forgepulse.provenance import LineageReference, ProvenanceRecord
from forgepulse.simulation import Simulator, SimulatorResult, SimulationMetadata
from forgepulse.validation import SnapshotValidator, ValidationResult, validate_experiment


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


def _make_snapshot(spec: ExperimentSpecification) -> ValidatedExperimentSnapshot:
    validator = SnapshotValidator()
    return validator.create_snapshot(spec)


class TestSimulator:
    def test_simulated_source_explicitly_identified(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        for m in result.measurements:
            assert m.source_type == SourceType.SIMULATED

    def test_simulator_cannot_masquerade_as_hardware(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert result.measurements[0].instrument_reference == "simulator"
        for m in result.measurements:
            assert m.source_type == SourceType.SIMULATED

    def test_simulator_deterministic_values(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result1 = simulator.simulate(snapshot)
        result2 = simulator.simulate(snapshot)
        assert result1.measurements[0].values == result2.measurements[0].values
        assert result1.target_process == result2.target_process
        assert result1.actual_process == result2.actual_process

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
        from forgepulse.validation import validate_experiment
        validation_result = validate_experiment(spec)
        assert not validation_result.valid
        snapshot = ValidatedExperimentSnapshot(
            snapshot_id="snap-empty",
            experiment_id=spec.experiment_id,
            experiment_version=spec.experiment_version,
            schema_version=spec.schema_version,
            specification=spec,
            validation_result=validation_result,
            validator_id="test-validator",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            checksum="abc123",
        )
        simulator = Simulator()
        with pytest.raises(ValueError):
            simulator.simulate(snapshot)

    def test_simulator_returns_correct_structure(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert isinstance(result, SimulatorResult)
        assert result.snapshot_id == snapshot.snapshot_id
        assert result.experiment_id == snapshot.experiment_id
        assert result.experiment_version == snapshot.experiment_version
        assert len(result.measurements) == 4
        assert isinstance(result.simulation_metadata, SimulationMetadata)

    def test_simulator_metadata_is_correct(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert result.simulation_metadata.simulator_id == "forgepulse-simulator-v1"
        assert result.simulation_metadata.simulator_version == "1.0.0"
        assert result.simulation_metadata.model_version == "baseline-v1"
        assert result.simulation_metadata.sampling_rate_hz == 1000.0
        assert result.simulation_metadata.seed >= 0

    def test_simulator_provenance_tracks_snapshot(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert isinstance(result.provenance, ProvenanceRecord)
        assert result.provenance.artifact_id.startswith("sim-")
        assert result.provenance.transformation == "deterministic_baseline_simulation"

    def test_simulator_to_raw_measurements(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        raw = simulator.to_raw_measurements(result)
        assert len(raw) == 4
        for r in raw:
            assert isinstance(r, RawMeasurement)
            assert r.source_type == SourceType.SIMULATED
            assert r.values

    def test_simulator_observations_present(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert hasattr(result, "electrical_observation")
        assert hasattr(result, "thermal_observation")
        assert result.electrical_observation.source_type == SourceType.SIMULATED
        assert result.thermal_observation.source_type == SourceType.SIMULATED

    def test_simulator_actual_process_derived(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), target_current=Quantity(value=10.0, unit="A"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert isinstance(result.actual_process, ActualProcess)
        assert result.actual_process.measured_voltage.value > 0
        assert result.actual_process.measured_current.value > 0

    def test_simulator_target_process_matches_spec(self):
        spec = _make_spec()
        snapshot = _make_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert isinstance(result.target_process, TargetProcess)
        assert result.target_process.voltage.value == 120.0
        assert result.target_process.pulse_duration.value == 0.05

    def test_simulator_seed_deterministic_from_snapshot(self):
        spec1 = _make_spec()
        snapshot1 = _make_snapshot(spec1)
        spec2 = _make_spec()
        snapshot2 = _make_snapshot(spec2)
        assert snapshot1.snapshot_id == snapshot2.snapshot_id
        simulator = Simulator()
        result1 = simulator.simulate(snapshot1)
        result2 = simulator.simulate(snapshot2)
        assert result1.simulation_metadata.seed == result2.simulation_metadata.seed
