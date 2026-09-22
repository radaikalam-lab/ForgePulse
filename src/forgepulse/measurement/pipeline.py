"""Measurement ingestion boundary and pipeline for ForgePulse.

This module provides:

1. MeasurementIngestionBoundary - a provider-neutral interface for
   ingesting normalized measurement representations into ForgePulse.
   It does not control instruments, start/stop experiments, issue
   hardware commands, or infer material properties.

2. MeasurementPipeline - stages for processing measurements from
   raw through derived to characterization.

The boundary is the canonical interface that future physical edge
adapters will target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from forgepulse.common import MeasurementValidationError, Quantity
from forgepulse.measurement.characterization import (
    ElectricalCharacterization,
    ThermalCharacterization,
)
from forgepulse.measurement.models import (
    DerivedMeasurement,
    MeasurementSeries,
    ProvenanceReference,
    RawMeasurement,
    SourceType,
)
from forgepulse.measurement.derivation import (
    _validate_finite_values,
    _validate_non_empty,
    compute_average,
    compute_energy,
    compute_power,
    compute_pulse_statistics,
)
from forgepulse.measurement.validation import validate_measurement


class IngestionError(MeasurementValidationError):
    """Raised when measurement ingestion fails validation."""


@dataclass
class MeasurementIngestionBoundary:
    """Provider-neutral boundary for ingesting measurements into ForgePulse.

    This boundary accepts normalized measurement representations from
    any source (simulator, future edge adapters, external data).
    It validates incoming measurements and records them as ingested.

    The boundary does NOT:
    - Control instruments
    - Start or stop experiments
    - Issue hardware commands
    - Infer material properties automatically
    - Claim scientific truth
    """

    source_type: SourceType
    _ingested: list[RawMeasurement] = field(default_factory=list, repr=False)

    def ingest_raw(self, measurement: RawMeasurement) -> RawMeasurement:
        """Ingest a raw measurement into ForgePulse.

        Validates the measurement and records it as ingested.

        Args:
            measurement: A normalized RawMeasurement object.

        Returns:
            The validated RawMeasurement.

        Raises:
            IngestionError: If the measurement fails validation.
        """
        errors = validate_measurement(measurement)
        if errors:
            raise IngestionError(
                f"Invalid measurement {measurement.measurement_id}: {'; '.join(errors)}"
            )
        self._ingested.append(measurement)
        return measurement

    def ingest_series(self, series: MeasurementSeries) -> MeasurementSeries:
        """Ingest a measurement series into ForgePulse.

        Validates the series and records it as ingested.

        Args:
            series: A MeasurementSeries object.

        Returns:
            The validated MeasurementSeries.

        Raises:
            IngestionError: If the series fails validation.
        """
        errors = validate_measurement(series)
        if errors:
            raise IngestionError(
                f"Invalid series {series.measurement_id}: {'; '.join(errors)}"
            )
        return series

    def ingest_derived(self, measurement: DerivedMeasurement) -> DerivedMeasurement:
        """Ingest a derived measurement into ForgePulse.

        Validates the measurement and records it as ingested.

        Args:
            measurement: A DerivedMeasurement object.

        Returns:
            The validated DerivedMeasurement.

        Raises:
            IngestionError: If the measurement fails validation.
        """
        errors = validate_measurement(measurement)
        if errors:
            raise IngestionError(
                f"Invalid derived measurement {measurement.measurement_id}: {'; '.join(errors)}"
            )
        return measurement

    @property
    def ingested_count(self) -> int:
        """Number of raw measurements ingested through this boundary."""
        return len(self._ingested)

    @property
    def ingested_measurements(self) -> tuple[RawMeasurement, ...]:
        """Tuple of ingested raw measurements."""
        return tuple(self._ingested)


@dataclass
class MeasurementPipeline:
    """Pipeline for processing measurements from raw to characterization.

    The pipeline stages are:
    Raw Measurement → Validated Measurement → Derived Measurement →
    Characterization → Material State

    The pipeline does not claim scientific truth. It performs
    deterministic transformations only.
    """

    ingestion_boundary: MeasurementIngestionBoundary
    _derived: list[DerivedMeasurement] = field(default_factory=list, repr=False)
    _characterizations: list[Any] = field(default_factory=list, repr=False)

    def process_raw(self, measurement: RawMeasurement) -> RawMeasurement:
        """Process a raw measurement through the pipeline.

        Validates and ingests the measurement.

        Args:
            measurement: A RawMeasurement to process.

        Returns:
            The validated RawMeasurement.

        Raises:
            IngestionError: If the measurement fails validation.
        """
        return self.ingestion_boundary.ingest_raw(measurement)

    def derive_power(
        self,
        voltage_series: MeasurementSeries,
        current_series: MeasurementSeries,
        measurement_id: Optional[str] = None,
    ) -> MeasurementSeries:
        """Derive instantaneous power from voltage and current series.

        Args:
            voltage_series: Time-series voltage measurement.
            current_series: Time-series current measurement.
            measurement_id: Optional identifier for the derived measurement.

        Returns:
            A derived MeasurementSeries with power values.

        Raises:
            MeasurementValidationError: If series are invalid or misaligned.
        """
        power_series = compute_power(voltage_series, current_series, measurement_id)
        self._derived.append(
            DerivedMeasurement(
                measurement_id=power_series.measurement_id,
                quantity="power",
                value=Quantity(value=power_series.values[0], unit="W"),
                source_ids=(voltage_series.measurement_id, current_series.measurement_id),
                transformation="multiply_voltage_current",
                source_type=SourceType.DERIVED,
                provenance=power_series.provenance,
            )
        )
        return power_series

    def derive_energy(
        self,
        power_series: MeasurementSeries,
        measurement_id: Optional[str] = None,
    ) -> DerivedMeasurement:
        """Derive total energy from a power time series.

        Args:
            power_series: Time-series power measurement.
            measurement_id: Optional identifier for the derived measurement.

        Returns:
            A DerivedMeasurement with energy value.

        Raises:
            MeasurementValidationError: If power series is invalid.
        """
        energy = compute_energy(power_series, measurement_id)
        self._derived.append(energy)
        return energy

    def derive_pulse_statistics(
        self,
        voltage_series: MeasurementSeries,
        current_series: MeasurementSeries,
        inter_pulse_interval_s: float = 0.0,
    ) -> dict[str, DerivedMeasurement]:
        """Derive pulse-level statistics from voltage and current series.

        Computes deterministic pulse quantities with clear definitions.
        No speculative scientific metrics are introduced.

        Args:
            voltage_series: Time-series voltage measurement.
            current_series: Time-series current measurement.
            inter_pulse_interval_s: Interval between pulses in seconds.

        Returns:
            Dictionary of DerivedMeasurements for each pulse statistic.

        Raises:
            MeasurementValidationError: If series are invalid or misaligned.
        """
        stats = compute_pulse_statistics(
            voltage_series, current_series, inter_pulse_interval_s
        )

        results = {}
        base_sources = (voltage_series.measurement_id, current_series.measurement_id)

        peak_v = DerivedMeasurement(
            measurement_id=f"derived-peak-v-{voltage_series.measurement_id}",
            quantity="peak_voltage",
            value=Quantity(value=stats.peak_voltage_v, unit="V"),
            source_ids=base_sources,
            transformation="peak",
            source_type=SourceType.DERIVED,
            provenance=ProvenanceReference(artifact_id=voltage_series.measurement_id),
        )
        results["peak_voltage"] = peak_v
        self._derived.append(peak_v)

        peak_i = DerivedMeasurement(
            measurement_id=f"derived-peak-i-{current_series.measurement_id}",
            quantity="peak_current",
            value=Quantity(value=stats.peak_current_a, unit="A"),
            source_ids=base_sources,
            transformation="peak",
            source_type=SourceType.DERIVED,
            provenance=ProvenanceReference(artifact_id=current_series.measurement_id),
        )
        results["peak_current"] = peak_i
        self._derived.append(peak_i)

        avg_v = DerivedMeasurement(
            measurement_id=f"derived-avg-v-{voltage_series.measurement_id}",
            quantity="average_voltage",
            value=Quantity(value=stats.avg_voltage_v, unit="V"),
            source_ids=base_sources,
            transformation="average",
            source_type=SourceType.DERIVED,
            provenance=ProvenanceReference(artifact_id=voltage_series.measurement_id),
        )
        results["average_voltage"] = avg_v
        self._derived.append(avg_v)

        avg_i = DerivedMeasurement(
            measurement_id=f"derived-avg-i-{current_series.measurement_id}",
            quantity="average_current",
            value=Quantity(value=stats.avg_current_a, unit="A"),
            source_ids=base_sources,
            transformation="average",
            source_type=SourceType.DERIVED,
            provenance=ProvenanceReference(artifact_id=current_series.measurement_id),
        )
        results["average_current"] = avg_i
        self._derived.append(avg_i)

        energy = DerivedMeasurement(
            measurement_id=f"derived-pulse-energy-{voltage_series.measurement_id}",
            quantity="pulse_energy",
            value=Quantity(value=stats.pulse_energy_j, unit="J"),
            source_ids=base_sources,
            transformation="integral_power_over_time",
            source_type=SourceType.DERIVED,
            provenance=ProvenanceReference(artifact_id=voltage_series.measurement_id),
        )
        results["pulse_energy"] = energy
        self._derived.append(energy)

        return results

    def characterize_electrical(
        self,
        voltage_series: MeasurementSeries,
        current_series: MeasurementSeries,
        characterization_id: str,
    ) -> ElectricalCharacterization:
        """Create an electrical characterization from voltage and current series.

        Args:
            voltage_series: Time-series voltage measurement.
            current_series: Time-series current measurement.
            characterization_id: Unique identifier for this characterization.

        Returns:
            An ElectricalCharacterization with derived electrical properties.

        Raises:
            MeasurementValidationError: If series are invalid or misaligned.
        """
        from forgepulse.measurement.derivation import compute_pulse_statistics

        stats = compute_pulse_statistics(voltage_series, current_series)

        char = ElectricalCharacterization(
            peak_voltage_v=Quantity(value=stats.peak_voltage_v, unit="V"),
            peak_current_a=Quantity(value=stats.peak_current_a, unit="A"),
            average_voltage_v=Quantity(value=stats.avg_voltage_v, unit="V"),
            average_current_a=Quantity(value=stats.avg_current_a, unit="A"),
            pulse_energy_j=Quantity(value=stats.pulse_energy_j, unit="J"),
            provenance=ProvenanceReference(artifact_id=characterization_id),
        )
        self._characterizations.append(char)
        return char

    def characterize_thermal(
        self,
        temperature_series: MeasurementSeries,
        characterization_id: str,
    ) -> ThermalCharacterization:
        """Create a thermal characterization from a temperature series.

        Computes deterministic thermal quantities:
        - peak_temperature_k: maximum temperature
        - temperature_rise_k: peak - initial temperature
        - heating_rate_k_s: rate of temperature increase (if timestamps available)
        - cooling_rate_k_s: rate of temperature decrease (if timestamps available)

        Args:
            temperature_series: Time-series temperature measurement.
            characterization_id: Unique identifier for this characterization.

        Returns:
            A ThermalCharacterization with derived thermal properties.

        Raises:
            MeasurementValidationError: If series is invalid.
        """
        from forgepulse.measurement.derivation import compute_average

        values = temperature_series.values
        _validate_non_empty(values, "temperature")
        _validate_finite_values(values, "temperature")

        peak_temp = max(values)
        initial_temp = values[0]
        temp_rise = peak_temp - initial_temp

        heating_rate: Optional[Quantity] = None
        cooling_rate: Optional[Quantity] = None

        if temperature_series.timestamps is not None and len(temperature_series.timestamps) > 1:
            timestamps = temperature_series.timestamps
            max_idx = values.index(peak_temp)
            if max_idx > 0:
                heat_dt = (timestamps[max_idx] - timestamps[0]).total_seconds()
                if heat_dt > 0:
                    heating_rate = Quantity(value=temp_rise / heat_dt, unit="K/s")

            if max_idx < len(values) - 1:
                cool_dt = (timestamps[-1] - timestamps[max_idx]).total_seconds()
                if cool_dt > 0:
                    final_temp = values[-1]
                    cooling_rate = Quantity(
                        value=(peak_temp - final_temp) / cool_dt, unit="K/s"
                    )

        char = ThermalCharacterization(
            peak_temperature_k=Quantity(value=peak_temp, unit="K"),
            temperature_rise_k=Quantity(value=temp_rise, unit="K"),
            heating_rate_k_s=heating_rate,
            cooling_rate_k_s=cooling_rate,
            provenance=ProvenanceReference(artifact_id=characterization_id),
        )
        self._characterizations.append(char)
        return char

    @property
    def derived_count(self) -> int:
        """Number of derived measurements produced by this pipeline."""
        return len(self._derived)

    @property
    def characterization_count(self) -> int:
        """Number of characterizations produced by this pipeline."""
        return len(self._characterizations)
