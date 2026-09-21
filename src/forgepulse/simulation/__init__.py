"""Deterministic FJH simulator boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from forgepulse.common import Quantity, _utc_now
from forgepulse.experiment import ExperimentSpecification, PulseSequence
from forgepulse.execution import ActualProcess
from forgepulse.measurement import (
    ElectricalObservation,
    MeasurementSeries,
    ProvenanceReference,
    SourceType,
    ThermalObservation,
)
from forgepulse.provenance import LineageReference, ProvenanceRecord


@dataclass(frozen=True)
class SimulatorResult:
    execution_id: str
    actual_process: ActualProcess
    measurements: tuple[MeasurementSeries, ...]
    observations: tuple[ElectricalObservation, ...]
    provenance: ProvenanceRecord


class Simulator:
    """Deterministic simulator for FJH experiments.

    All observations produced by this simulator are explicitly marked as simulated.
    The simulator does not pretend to be a validated physical model.
    """

    def simulate(self, spec: ExperimentSpecification, execution_id: str) -> SimulatorResult:
        sequence = spec.pulse_sequence
        if not sequence.pulses:
            raise ValueError("Cannot simulate empty pulse sequence")

        voltage_values = []
        current_values = []
        temperature_values = []
        start_time = _utc_now()

        for pulse in sequence.pulses:
            v = pulse.target_voltage.value if pulse.target_voltage is not None else 0.0
            c = pulse.target_current.value if pulse.target_current is not None else 0.0
            voltage_values.append(v)
            current_values.append(c)
            temperature_values.append(300.0 + v * 2.0)

        actual = ActualProcess(
            measured_voltage=Quantity(value=sum(voltage_values) / len(voltage_values), unit="V"),
            measured_current=Quantity(value=sum(current_values) / len(current_values), unit="A"),
            measured_duration=Quantity(value=sum(p.duration.value for p in sequence.pulses), unit="s"),
            measured_interval=Quantity(value=sequence.inter_pulse_interval.value, unit="s"),
        )

        measurement = MeasurementSeries(
            measurement_id=f"sim-meas-{execution_id}",
            quantity="voltage",
            values=voltage_values,
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=start_time,
            instrument_reference="simulator",
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(execution_id=execution_id),
        )

        electrical_obs = ElectricalObservation(
            measurement_id=f"sim-elec-{execution_id}",
            voltage=Quantity(value=actual.measured_voltage.value, unit="V"),
            current=Quantity(value=actual.measured_current.value, unit="A"),
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(execution_id=execution_id),
        )

        thermal_obs = ThermalObservation(
            measurement_id=f"sim-therm-{execution_id}",
            temperature=Quantity(value=sum(temperature_values) / len(temperature_values), unit="K"),
            source_type=SourceType.SIMULATED,
            provenance=ProvenanceReference(execution_id=execution_id),
        )

        provenance = ProvenanceRecord(
            artifact_id=execution_id,
            artifact_type="simulation",
            source_ids=(LineageReference(artifact_id=spec.experiment_id, artifact_type="experiment"),),
            transformation="deterministic_simulation",
        )

        return SimulatorResult(
            execution_id=execution_id,
            actual_process=actual,
            measurements=(measurement,),
            observations=(electrical_obs, thermal_obs),
            provenance=provenance,
        )
