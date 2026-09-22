"""Measurement validation for ForgePulse.

This module provides deterministic structural and semantic validation
for measurements. Validation does not repair data; it rejects or
explicitly flags invalid measurements.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from forgepulse.common import MeasurementValidationError, Quantity
from forgepulse.measurement.models import (
    DerivedMeasurement,
    MeasurementSeries,
    RawMeasurement,
    SourceType,
)


def _validate_finite_values(values: list[float], name: str) -> list[str]:
    """Check that all values are finite (no NaN or Infinity)."""
    errors = []
    for i, v in enumerate(values):
        if v != v or v in (float("inf"), float("-inf")):
            errors.append(f"{name} contains non-finite value at index {i}: {v}")
    return errors


def _validate_non_empty(values: list[float], name: str) -> list[str]:
    """Check that a value list is non-empty."""
    if not values:
        return [f"{name} must contain at least one value"]
    return []


def _validate_unit(unit: Optional[str]) -> list[str]:
    """Check that a unit is present and is a non-empty string."""
    errors = []
    if unit is None or not isinstance(unit, str) or not unit.strip():
        errors.append("unit must be a non-empty string")
    return errors


def _validate_timestamps(
    timestamps: Optional[list[datetime]],
    num_values: int,
    name: str,
) -> list[str]:
    """Validate timestamp list consistency."""
    errors = []
    if timestamps is not None:
        if len(timestamps) != num_values:
            errors.append(
                f"{name} timestamps length ({len(timestamps)}) must match "
                f"values length ({num_values})"
            )
        for i, ts in enumerate(timestamps):
            if ts.tzinfo is None:
                errors.append(
                    f"{name} timestamps[{i}] must be timezone-aware UTC"
                )
    return errors


def _validate_sampling_consistency(
    sampling_rate: Optional[Quantity],
    timestamps: Optional[list[datetime]],
    num_values: int,
    name: str,
) -> list[str]:
    """Validate sampling rate and timestamp consistency."""
    errors = []
    if sampling_rate is not None and sampling_rate.value <= 0:
        errors.append(f"{name} sampling_rate must be positive, got {sampling_rate.value}")
    if timestamps is not None and len(timestamps) > 1:
        for i in range(len(timestamps) - 1):
            if timestamps[i + 1] <= timestamps[i]:
                errors.append(
                    f"{name} timestamps must be monotonically increasing"
                )
                break
    return errors


def validate_raw_measurement(measurement: RawMeasurement) -> tuple[str, ...]:
    """Validate a RawMeasurement for structural and semantic correctness.

    Checks:
    - measurement_id is present and non-empty
    - quantity is present and non-empty
    - values list is non-empty
    - values contain only finite numbers
    - unit is present and non-empty
    - start_time is timezone-aware UTC if provided
    - sampling_rate is positive if provided
    - timestamps are consistent with values if provided

    Args:
        measurement: The RawMeasurement to validate.

    Returns:
        Tuple of error strings. Empty tuple means validation passed.
    """
    errors = []

    if not measurement.measurement_id or not measurement.measurement_id.strip():
        errors.append("measurement_id must be a non-empty string")

    if not measurement.quantity or not measurement.quantity.strip():
        errors.append("quantity must be a non-empty string")

    errors.extend(_validate_non_empty(measurement.values, "values"))
    errors.extend(_validate_finite_values(measurement.values, "values"))
    errors.extend(_validate_unit(measurement.unit))

    if measurement.sampling_rate is not None:
        if measurement.sampling_rate.value <= 0:
            errors.append(
                f"sampling_rate must be positive, got {measurement.sampling_rate.value}"
            )

    return tuple(errors)


def validate_measurement_series(series: MeasurementSeries) -> tuple[str, ...]:
    """Validate a MeasurementSeries for structural and semantic correctness.

    Checks:
    - measurement_id is present and non-empty
    - quantity is present and non-empty
    - values list is non-empty
    - values contain only finite numbers
    - unit is present and non-empty
    - start_time is timezone-aware UTC
    - timestamps are consistent with values if provided
    - timestamps are monotonically increasing if provided
    - sampling_rate is positive if provided

    Args:
        series: The MeasurementSeries to validate.

    Returns:
        Tuple of error strings. Empty tuple means validation passed.
    """
    errors = []

    if not series.measurement_id or not series.measurement_id.strip():
        errors.append("measurement_id must be a non-empty string")

    if not series.quantity or not series.quantity.strip():
        errors.append("quantity must be a non-empty string")

    errors.extend(_validate_non_empty(series.values, "values"))
    errors.extend(_validate_finite_values(series.values, "values"))
    errors.extend(_validate_unit(series.unit))

    if series.start_time.tzinfo is None:
        errors.append("start_time must be timezone-aware UTC")

    errors.extend(_validate_timestamps(series.timestamps, len(series.values), series.measurement_id))
    errors.extend(_validate_sampling_consistency(
        series.sampling_rate, series.timestamps, len(series.values), series.measurement_id
    ))

    return tuple(errors)


def validate_derived_measurement(measurement: DerivedMeasurement) -> tuple[str, ...]:
    """Validate a DerivedMeasurement for structural and semantic correctness.

    Checks:
    - measurement_id is present and non-empty
    - quantity is present and non-empty
    - value is finite (no NaN or Infinity)
    - source_ids are present if the measurement claims lineage
    - transformation is present if source_ids are present

    Args:
        measurement: The DerivedMeasurement to validate.

    Returns:
        Tuple of error strings. Empty tuple means validation passed.
    """
    errors = []

    if not measurement.measurement_id or not measurement.measurement_id.strip():
        errors.append("measurement_id must be a non-empty string")

    if not measurement.quantity or not measurement.quantity.strip():
        errors.append("quantity must be a non-empty string")

    if measurement.value.value != measurement.value.value or measurement.value.value in (
        float("inf"),
        float("-inf"),
    ):
        errors.append(
            f"derived value must be finite, got {measurement.value.value}"
        )

    if measurement.source_ids and not measurement.transformation:
        errors.append("transformation must be specified when source_ids are present")

    return tuple(errors)


def validate_measurement(measurement) -> tuple[str, ...]:
    """Dispatch validation to the appropriate validator based on measurement type.

    Args:
        measurement: A RawMeasurement, MeasurementSeries, or DerivedMeasurement.

    Returns:
        Tuple of error strings. Empty tuple means validation passed.
    """
    if isinstance(measurement, RawMeasurement):
        return validate_raw_measurement(measurement)
    if isinstance(measurement, MeasurementSeries):
        return validate_measurement_series(measurement)
    if isinstance(measurement, DerivedMeasurement):
        return validate_derived_measurement(measurement)
    raise MeasurementValidationError(
        f"Unknown measurement type: {type(measurement).__name__}"
    )
