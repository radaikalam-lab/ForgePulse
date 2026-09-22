"""Deterministic FJH simulator boundary."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from forgepulse.common import Quantity, _utc_now
from forgepulse.execution import ActualProcess, TargetProcess
from forgepulse.experiment import ExperimentSpecification, ValidatedExperimentSnapshot
from forgepulse.measurement import (
    DerivedMeasurement,
    ElectricalObservation,
    MeasurementSeries,
    ProvenanceReference,
    RawMeasurement,
    SourceType,
    ThermalObservation,
)
from forgepulse.provenance import LineageReference, ProvenanceRecord


@dataclass(frozen=True)
class SimulationMetadata:
    """Metadata identifying the simulator implementation and model."""

    simulator_id: str = "forgepulse-simulator-v1"
    simulator_version: str = "1.0.0"
    model_version: str = "baseline-v1"
    seed: int = 0
    sampling_rate_hz: float = 1000.0
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if self.sampling_rate_hz <= 0:
            raise ValueError("sampling_rate_hz must be positive")


@dataclass(frozen=True)
class SimulatorResult:
    """Deterministic result of a FJH simulation.

    All measurements and observations are explicitly marked as simulated.
    The simulator does not claim physical accuracy or experimental truth.
    """

    simulation_id: str
    snapshot_id: str
    experiment_id: str
    experiment_version: str
    target_process: TargetProcess
    actual_process: ActualProcess
    measurements: tuple[MeasurementSeries, ...]
    electrical_observation: ElectricalObservation
    thermal_observation: ThermalObservation
    simulation_metadata: SimulationMetadata
    provenance: ProvenanceRecord


def _seed_from_snapshot(snapshot: ValidatedExperimentSnapshot) -> int:
    """Derive a deterministic integer seed from a validated snapshot."""
    h = hashlib.sha256(snapshot.snapshot_id.encode("utf-8")).hexdigest()
    return int(h[:12], 16)


def _simulation_start_time(snapshot: ValidatedExperimentSnapshot) -> datetime:
    """Derive a deterministic simulation start time from snapshot identity."""
    h = hashlib.sha256(snapshot.snapshot_id.encode("utf-8")).hexdigest()
    offset_seconds = int(h[:8], 16) % 1_000_000
    return datetime.fromtimestamp(1_700_000_000 + offset_seconds, tz=timezone.utc)


def _build_target_process(spec: ExperimentSpecification) -> TargetProcess:
    """Extract target process from experiment specification."""
    pulses = spec.pulse_sequence.pulses
    if not pulses:
        return TargetProcess()
    first_pulse = pulses[0]
    voltage = first_pulse.target_voltage
    current = first_pulse.target_current
    duration = first_pulse.duration
    interval = spec.pulse_sequence.inter_pulse_interval
    return TargetProcess(
        voltage=voltage,
        current=current,
        pulse_duration=duration,
        inter_pulse_interval=interval,
    )


class Simulator:
    """Deterministic simulator for FJH experiments.

    Scientific model assumptions:
    - Current remains constant over each pulse duration.
    - Voltage deviates deterministically within ±5% of target.
    - Temperature = 300K + 2K per volt of actual voltage.
    - Power = V × I (derived).
    - Energy = integral of power over pulse duration (derived).
    - No material-specific physics, plasma modeling, or thermal FEM.
    - Baseline process model only; not a validated physical model.
    """

    def to_raw_measurements(self, result: SimulatorResult) -> tuple[RawMeasurement, ...]:
        """Convert simulated measurements to normalized RawMeasurement objects.

        This allows simulated data to flow through the edge integration boundary
        as if it were raw edge data.

        Args:
            result: SimulatorResult from simulate().

        Returns:
            Tuple of RawMeasurement objects with source_type=SIMULATED.
        """
        raw_measurements = []
        for series in result.measurements:
            raw = RawMeasurement(
                measurement_id=series.measurement_id,
                quantity=series.quantity,
                values=series.values,
                unit=series.unit,
                sampling_rate=series.sampling_rate,
                start_time=series.start_time,
                instrument_reference=series.instrument_reference,
                source_type=SourceType.SIMULATED,
                provenance=series.provenance,
            )
            raw_measurements.append(raw)
        return tuple(raw_measurements)

    def simulate(self, snapshot: ValidatedExperimentSnapshot) -> SimulatorResult:
        """Run a deterministic simulation from a validated experiment snapshot.

        The simulator does not modify the snapshot. All outputs are explicitly
        marked as simulated. The simulator does not claim physical accuracy.

        Args:
            snapshot: A validated immutable experiment snapshot.

        Returns:
            A deterministic SimulatorResult.

        Raises:
            ValueError: If the snapshot contains an empty pulse sequence.
        """
        spec = snapshot.specification
        sequence = spec.pulse_sequence
        if not sequence.pulses:
            raise ValueError("Cannot simulate empty pulse sequence")

        seed = _seed_from_snapshot(snapshot)
        rng = random.Random(seed)
        start_time = _simulation_start_time(snapshot)
        sampling_rate_hz = 1000.0
        dt = 1.0 / sampling_rate_hz

        voltage_values: list[float] = []
        current_values: list[float] = []
        temperature_values: list[float] = []
        power_values: list[float] = []
        timestamps: list[datetime] = []

        current_time = start_time
        for pulse in sequence.pulses:
            target_v = pulse.target_voltage.value
            target_c = pulse.target_current.value if pulse.target_current is not None else 0.0
            duration_s = pulse.duration.value
            num_samples = max(1, int(duration_s * sampling_rate_hz))

            for _ in range(num_samples):
                actual_v = target_v * (1.0 + rng.uniform(-0.05, 0.05))
                actual_c = target_c * (1.0 + rng.uniform(-0.05, 0.05))
                temp = 300.0 + actual_v * 2.0
                power = actual_v * actual_c
                voltage_values.append(actual_v)
                current_values.append(actual_c)
                temperature_values.append(temp)
                power_values.append(power)
                timestamps.append(current_time)
                current_time = current_time.replace(
                    microsecond=current_time.microsecond + int(dt * 1_000_000)
                )
                # Handle microsecond overflow
                if current_time.microsecond >= 1_000_000:
                    current_time = current_time.replace(microsecond=current_time.microsecond % 1_000_000)
                    current_time = datetime.fromtimestamp(
                        current_time.timestamp() + 1, tz=timezone.utc
                    )

            # Add inter-pulse interval gap
            interval_s = sequence.inter_pulse_interval.value
            if interval_s > 0 and pulse != sequence.pulses[-1]:
                current_time = datetime.fromtimestamp(
                    current_time.timestamp() + interval_s, tz=timezone.utc
                )

        total_duration = sum(p.duration.value for p in sequence.pulses) + (
            sequence.inter_pulse_interval.value * max(0, len(sequence.pulses) - 1)
        )
        energy_joules = sum(p * dt for p in power_values)

        actual = ActualProcess(
            measured_voltage=Quantity(value=sum(voltage_values) / len(voltage_values), unit="V"),
            measured_current=Quantity(value=sum(current_values) / len(current_values), unit="A"),
            measured_duration=Quantity(value=total_duration, unit="s"),
            measured_interval=Quantity(value=sequence.inter_pulse_interval.value, unit="s"),
        )

        target_process = _build_target_process(spec)

        voltage_series = MeasurementSeries(
            measurement_id=f"sim-voltage-{snapshot.snapshot_id}",
            quantity="voltage",
            values=voltage_values,
            unit="V",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            timestamps=tuple(timestamps),
            instrument_reference="simulator",
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        current_series = MeasurementSeries(
            measurement_id=f"sim-current-{snapshot.snapshot_id}",
            quantity="current",
            values=current_values,
            unit="A",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            timestamps=tuple(timestamps),
            instrument_reference="simulator",
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        temperature_series = MeasurementSeries(
            measurement_id=f"sim-temperature-{snapshot.snapshot_id}",
            quantity="temperature",
            values=temperature_values,
            unit="K",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            timestamps=tuple(timestamps),
            instrument_reference="simulator",
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        power_series = MeasurementSeries(
            measurement_id=f"sim-power-{snapshot.snapshot_id}",
            quantity="power",
            values=power_values,
            unit="W",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            timestamps=tuple(timestamps),
            instrument_reference="simulator",
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        energy_measurement = DerivedMeasurement(
            measurement_id=f"sim-energy-{snapshot.snapshot_id}",
            quantity="energy",
            value=Quantity(value=energy_joules, unit="J"),
            source_ids=(voltage_series.measurement_id, current_series.measurement_id),
            transformation="integral_power_over_time",
            source_type=SourceType.DERIVED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        electrical_obs = ElectricalObservation(
            measurement_id=f"sim-elec-{snapshot.snapshot_id}",
            voltage=Quantity(value=actual.measured_voltage.value, unit="V"),
            current=Quantity(value=actual.measured_current.value, unit="A"),
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        thermal_obs = ThermalObservation(
            measurement_id=f"sim-therm-{snapshot.snapshot_id}",
            temperature=Quantity(value=sum(temperature_values) / len(temperature_values), unit="K"),
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(artifact_id=snapshot.snapshot_id),
        )

        simulation_metadata = SimulationMetadata(
            simulator_id="forgepulse-simulator-v1",
            simulator_version="1.0.0",
            model_version="baseline-v1",
            seed=seed,
            sampling_rate_hz=sampling_rate_hz,
            assumptions=(
                "current remains constant over each pulse duration",
                "voltage deviates deterministically within +/-5% of target",
                "temperature = 300K + 2K per volt of actual voltage",
                "power = V * I (derived)",
                "energy = integral of power over pulse duration (derived)",
                "no material-specific physics, plasma modeling, or thermal FEM",
                "baseline process model only; not a validated physical model",
            ),
        )

        provenance = ProvenanceRecord(
            artifact_id=f"sim-{snapshot.snapshot_id}",
            artifact_type="simulation",
            source_ids=(
                LineageReference(artifact_id=snapshot.snapshot_id, artifact_type="validated_snapshot"),
                LineageReference(artifact_id=snapshot.experiment_id, artifact_type="experiment"),
            ),
            transformation="deterministic_baseline_simulation",
            created_by="forgepulse-simulator-v1",
        )

        return SimulatorResult(
            simulation_id=f"sim-{snapshot.snapshot_id}",
            snapshot_id=snapshot.snapshot_id,
            experiment_id=snapshot.experiment_id,
            experiment_version=snapshot.experiment_version,
            target_process=target_process,
            actual_process=actual,
            measurements=(
                voltage_series,
                current_series,
                temperature_series,
                power_series,
            ),
            electrical_observation=electrical_obs,
            thermal_observation=thermal_obs,
            simulation_metadata=simulation_metadata,
            provenance=provenance,
        )