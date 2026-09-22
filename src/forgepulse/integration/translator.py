"""Measurement translator for normalizing raw edge data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from forgepulse.common import Quantity, MeasurementValidationError
from forgepulse.measurement import RawMeasurement, SourceType


@dataclass
class MeasurementTranslator:
    """Translates raw edge data into normalized ForgePulse measurements.

    This translator enforces the authority boundary by validating and
    normalizing incoming raw data without executing any hardware commands
    or bypassing safety constraints.
    """

    def translate_voltage(
        self,
        measurement_id: str,
        raw_data: dict[str, Any],
    ) -> RawMeasurement:
        """Translate raw voltage data to a normalized RawMeasurement.

        Args:
            measurement_id: Unique identifier for the measurement.
            raw_data: Raw data dictionary containing:
                - values: list of float voltage readings (required)
                - unit: unit string (required)
                - sampling_rate: sampling rate in Hz (optional)
                - start_time: ISO 8601 timestamp (optional)
                - instrument_reference: instrument ID (optional)

        Returns:
            A normalized RawMeasurement.

        Raises:
            MeasurementValidationError: If the raw data is invalid.
        """
        return self.translate(measurement_id, raw_data, quantity="voltage")

    def translate_current(
        self,
        measurement_id: str,
        raw_data: dict[str, Any],
    ) -> RawMeasurement:
        """Translate raw current data to a normalized RawMeasurement.

        Args:
            measurement_id: Unique identifier for the measurement.
            raw_data: Raw data dictionary.

        Returns:
            A normalized RawMeasurement.

        Raises:
            MeasurementValidationError: If the raw data is invalid.
        """
        return self.translate(measurement_id, raw_data, quantity="current")

    def translate(
        self,
        measurement_id: str,
        raw_data: dict[str, Any],
        quantity: str = "unknown",
    ) -> RawMeasurement:
        """Translate raw data to a normalized RawMeasurement.

        Args:
            measurement_id: Unique identifier for the measurement.
            raw_data: Raw data dictionary.
            quantity: Physical quantity name.

        Returns:
            A normalized RawMeasurement.

        Raises:
            MeasurementValidationError: If the raw data is invalid.
        """
        values = raw_data.get("values")
        if not isinstance(values, list) or not values:
            raise MeasurementValidationError("values must be a non-empty list")
        if not all(isinstance(v, (int, float)) for v in values):
            raise MeasurementValidationError("values must contain only numbers")

        unit = raw_data.get("unit")
        if not unit or not isinstance(unit, str):
            raise MeasurementValidationError("unit must be a non-empty string")

        sampling_rate = raw_data.get("sampling_rate")
        if sampling_rate is not None:
            if isinstance(sampling_rate, dict):
                sampling_rate = Quantity(
                    value=sampling_rate.get("value", 0),
                    unit=sampling_rate.get("unit", "Hz"),
                )
            elif isinstance(sampling_rate, (int, float)):
                sampling_rate = Quantity(value=float(sampling_rate), unit="Hz")
            else:
                raise MeasurementValidationError(
                    "sampling_rate must be a number or a dict with 'value' and 'unit'"
                )

        start_time = raw_data.get("start_time")
        if start_time is not None:
            if isinstance(start_time, str):
                try:
                    start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise MeasurementValidationError(
                        f"start_time must be a valid ISO 8601 timestamp: {exc}"
                    ) from exc
            if not isinstance(start_time, datetime):
                raise MeasurementValidationError("start_time must be a datetime or ISO string")
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
        else:
            start_time = datetime.now(timezone.utc)

        instrument_reference = raw_data.get("instrument_reference")

        return RawMeasurement(
            measurement_id=measurement_id,
            quantity=quantity,
            values=[float(v) for v in values],
            unit=unit,
            sampling_rate=sampling_rate,
            start_time=start_time,
            instrument_reference=instrument_reference,
            source_type=SourceType.RAW,
        )

    def translate_batch(
        self,
        raw_measurements: list[dict[str, Any]],
    ) -> list[RawMeasurement]:
        """Translate a batch of raw measurement data.

        Args:
            raw_measurements: List of raw data dictionaries, each containing
                at least 'measurement_id', 'values', 'unit', and 'quantity'.

        Returns:
            List of normalized RawMeasurement objects.

        Raises:
            MeasurementValidationError: If any raw data is invalid.
        """
        result = []
        for raw in raw_measurements:
            measurement_id = raw.get("measurement_id")
            if not measurement_id:
                raise MeasurementValidationError("measurement_id is required")
            quantity = raw.get("quantity", "unknown")
            result.append(self.translate(measurement_id, raw, quantity=quantity))
        return result
