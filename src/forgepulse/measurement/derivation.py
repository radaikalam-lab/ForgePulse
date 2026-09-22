"""Deterministic measurement derivation for ForgePulse.

This module provides deterministic calculation functions for deriving
secondary quantities from raw measurements. All derived measurements
preserve lineage to their source data and use explicit transformation
identifiers.

Derivation does not:
- Control instruments
- Issue hardware commands
- Infer material properties automatically
- Claim scientific truth
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from forgepulse.common import Quantity, MeasurementValidationError
from forgepulse.measurement.models import (
    DerivedMeasurement,
    MeasurementSeries,
    ProvenanceReference,
    SourceType,
)


def _validate_series_alignment(
    series_a: MeasurementSeries,
    series_b: MeasurementSeries,
) -> None:
    """Validate that two measurement series are aligned for element-wise operations."""
    if len(series_a.values) != len(series_b.values):
        raise MeasurementValidationError(
            f"Series length mismatch: {series_a.measurement_id} has "
            f"{len(series_a.values)} values, {series_b.measurement_id} has "
            f"{len(series_b.values)} values"
        )


def _validate_finite_values(values: list[float], name: str) -> None:
    """Validate that all values are finite (no NaN or Infinity)."""
    for i, v in enumerate(values):
        if v != v or v in (float("inf"), float("-inf")):
            raise MeasurementValidationError(
                f"{name} contains non-finite value at index {i}: {v}"
            )


def _validate_non_empty(values: list[float], name: str) -> None:
    """Validate that a value list is non-empty."""
    if not values:
        raise MeasurementValidationError(f"{name} must contain at least one value")


def compute_power(
    voltage_series: MeasurementSeries,
    current_series: MeasurementSeries,
    measurement_id: Optional[str] = None,
) -> MeasurementSeries:
    """Compute instantaneous electrical power P(t) = V(t) * I(t).

    This is a deterministic derivation. The resulting measurement series
    is explicitly marked as derived and preserves lineage to the source
    voltage and current measurements.

    Args:
        voltage_series: Time-series voltage measurement.
        current_series: Time-series current measurement.
        measurement_id: Optional identifier for the derived measurement.
            Defaults to a deterministic ID based on source IDs.

    Returns:
        A MeasurementSeries with source_type=DERIVED containing power values.

    Raises:
        MeasurementValidationError: If series are misaligned or contain
            non-finite values.
    """
    _validate_non_empty(voltage_series.values, "voltage")
    _validate_non_empty(current_series.values, "current")
    _validate_finite_values(voltage_series.values, "voltage")
    _validate_finite_values(current_series.values, "current")
    _validate_series_alignment(voltage_series, current_series)

    power_values = [v * c for v, c in zip(voltage_series.values, current_series.values)]

    derived_id = measurement_id or (
        f"derived-power-{voltage_series.measurement_id}-{current_series.measurement_id}"
    )

    return MeasurementSeries(
        measurement_id=derived_id,
        quantity="power",
        values=power_values,
        unit="W",
        sampling_rate=voltage_series.sampling_rate,
        start_time=voltage_series.start_time,
        timestamps=voltage_series.timestamps,
        instrument_reference=None,
        source_type=SourceType.DERIVED,
        provenance=ProvenanceReference(
            artifact_id=derived_id,
        ),
    )


def compute_energy(
    power_series: MeasurementSeries,
    measurement_id: Optional[str] = None,
) -> DerivedMeasurement:
    """Compute total energy as the integral of power over time.

    Uses a deterministic trapezoidal-style summation based on the
    available sampling rate or explicit timestamps.

    The numerical method:
    - If timestamps are provided: sum of P(t_i) * (t_{i+1} - t_i) for each interval
    - If only sampling_rate is provided: sum of P(t) * dt where dt = 1/sampling_rate

    Args:
        power_series: Time-series power measurement in Watts.
        measurement_id: Optional identifier for the derived measurement.

    Returns:
        A DerivedMeasurement with energy value in Joules.

    Raises:
        MeasurementValidationError: If power series is empty or contains
            non-finite values.
    """
    _validate_non_empty(power_series.values, "power")
    _validate_finite_values(power_series.values, "power")

    power_values = power_series.values

    if power_series.timestamps is not None and len(power_series.timestamps) > 1:
        timestamps = power_series.timestamps
        energy = 0.0
        for i in range(len(timestamps) - 1):
            dt = (timestamps[i + 1] - timestamps[i]).total_seconds()
            if dt < 0:
                raise MeasurementValidationError(
                    f"Timestamps must be monotonically increasing in {power_series.measurement_id}"
                )
            energy += power_values[i] * dt
    elif power_series.sampling_rate is not None:
        dt = 1.0 / power_series.sampling_rate.value
        energy = sum(power_values) * dt
    else:
        raise MeasurementValidationError(
            f"Power series {power_series.measurement_id} must have either "
            "timestamps or sampling_rate for energy integration"
        )

    derived_id = measurement_id or f"derived-energy-{power_series.measurement_id}"

    return DerivedMeasurement(
        measurement_id=derived_id,
        quantity="energy",
        value=Quantity(value=energy, unit="J"),
        source_ids=(power_series.measurement_id,),
        transformation="integral_power_over_time",
        source_type=SourceType.DERIVED,
        provenance=ProvenanceReference(artifact_id=derived_id),
    )


@dataclass(frozen=True)
class PulseStatistics:
    """Deterministic pulse-level statistics derived from voltage and current series."""

    pulse_duration_s: float
    peak_voltage_v: float
    peak_current_a: float
    avg_voltage_v: float
    avg_current_a: float
    pulse_energy_j: float
    inter_pulse_interval_s: float = 0.0


def compute_pulse_statistics(
    voltage_series: MeasurementSeries,
    current_series: MeasurementSeries,
    inter_pulse_interval_s: float = 0.0,
) -> PulseStatistics:
    """Compute deterministic pulse-level statistics from electrical measurements.

    Only quantities with clear definitions are computed. No speculative
    scientific metrics are introduced.

    Args:
        voltage_series: Time-series voltage measurement.
        current_series: Time-series current measurement.
        inter_pulse_interval_s: Interval between pulses in seconds.

    Returns:
        PulseStatistics with deterministic pulse-level quantities.

    Raises:
        MeasurementValidationError: If series are misaligned or invalid.
    """
    _validate_non_empty(voltage_series.values, "voltage")
    _validate_non_empty(current_series.values, "current")
    _validate_finite_values(voltage_series.values, "voltage")
    _validate_finite_values(current_series.values, "current")
    _validate_series_alignment(voltage_series, current_series)

    values = voltage_series.values
    num_samples = len(values)

    if voltage_series.sampling_rate is not None:
        pulse_duration = num_samples / voltage_series.sampling_rate.value
    elif voltage_series.timestamps is not None and len(voltage_series.timestamps) > 1:
        pulse_duration = (
            voltage_series.timestamps[-1] - voltage_series.timestamps[0]
        ).total_seconds()
    else:
        raise MeasurementValidationError(
            f"Voltage series {voltage_series.measurement_id} must have either "
            "timestamps or sampling_rate for pulse duration calculation"
        )

    power_values = [v * c for v, c in zip(voltage_series.values, current_series.values)]
    energy = sum(power_values)
    if voltage_series.sampling_rate is not None:
        dt = 1.0 / voltage_series.sampling_rate.value
        energy = energy * dt

    return PulseStatistics(
        pulse_duration_s=pulse_duration,
        peak_voltage_v=max(voltage_series.values),
        peak_current_a=max(current_series.values),
        avg_voltage_v=sum(voltage_series.values) / num_samples,
        avg_current_a=sum(current_series.values) / num_samples,
        pulse_energy_j=energy,
        inter_pulse_interval_s=inter_pulse_interval_s,
    )


def compute_peak(values: list[float], name: str = "value") -> float:
    """Compute the peak (maximum) value from a list of values.

    Args:
        values: List of numeric values.
        name: Name of the quantity for error messages.

    Returns:
        The maximum value.

    Raises:
        MeasurementValidationError: If values list is empty or contains
            non-finite values.
    """
    _validate_non_empty(values, name)
    _validate_finite_values(values, name)
    return max(values)


def compute_average(values: list[float], name: str = "value") -> float:
    """Compute the arithmetic mean of a list of values.

    Args:
        values: List of numeric values.
        name: Name of the quantity for error messages.

    Returns:
        The arithmetic mean.

    Raises:
        MeasurementValidationError: If values list is empty or contains
            non-finite values.
    """
    _validate_non_empty(values, name)
    _validate_finite_values(values, name)
    return sum(values) / len(values)
