"""Tests for measurement validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import MeasurementValidationError, Quantity
from forgepulse.measurement import (
    DerivedMeasurement,
    MeasurementSeries,
    RawMeasurement,
    SourceType,
)
from forgepulse.measurement.validation import (
    validate_derived_measurement,
    validate_measurement,
    validate_measurement_series,
    validate_raw_measurement,
)


class TestValidateRawMeasurement:
    def test_valid_raw_measurement(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[118.5, 119.2],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )
        errors = validate_raw_measurement(raw)
        assert errors == ()

    def test_empty_measurement_id_raises(self):
        raw = RawMeasurement(
            measurement_id="",
            quantity="voltage",
            values=[1.0],
            unit="V",
        )
        errors = validate_raw_measurement(raw)
        assert any("measurement_id" in e for e in errors)

    def test_empty_quantity_raises(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="",
            values=[1.0],
            unit="V",
        )
        errors = validate_raw_measurement(raw)
        assert any("quantity" in e for e in errors)

    def test_empty_values_raises(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[],
            unit="V",
        )
        errors = validate_raw_measurement(raw)
        assert any("at least one value" in e for e in errors)

    def test_nan_value_raises(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[1.0, float("nan")],
            unit="V",
        )
        errors = validate_raw_measurement(raw)
        assert any("non-finite" in e for e in errors)

    def test_infinity_value_raises(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[1.0, float("inf")],
            unit="V",
        )
        errors = validate_raw_measurement(raw)
        assert any("non-finite" in e for e in errors)

    def test_missing_unit_raises(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[1.0],
            unit="",
        )
        errors = validate_raw_measurement(raw)
        assert any("unit" in e for e in errors)

    def test_negative_sampling_rate_raises(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[1.0],
            unit="V",
            sampling_rate=Quantity(value=-100.0, unit="Hz"),
        )
        errors = validate_raw_measurement(raw)
        assert any("positive" in e for e in errors)


class TestValidateMeasurementSeries:
    def test_valid_series(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        series = MeasurementSeries(
            measurement_id="series-001",
            quantity="voltage",
            values=[118.5, 119.2],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=t0,
            source_type=SourceType.RAW,
        )
        errors = validate_measurement_series(series)
        assert errors == ()

    def test_naive_start_time_raises(self):
        series = MeasurementSeries(
            measurement_id="series-001",
            quantity="voltage",
            values=[118.5],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0),
        )
        errors = validate_measurement_series(series)
        assert any("UTC" in e for e in errors)

    def test_timestamps_length_mismatch_raises(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 15, 10, 30, 1, tzinfo=timezone.utc)
        series = MeasurementSeries(
            measurement_id="series-001",
            quantity="voltage",
            values=[118.5, 119.2],
            unit="V",
            sampling_rate=Quantity(value=1.0, unit="Hz"),
            start_time=t0,
            timestamps=[t0, t1, t1],
            source_type=SourceType.RAW,
        )
        errors = validate_measurement_series(series)
        assert any("timestamps length" in e for e in errors)

    def test_non_monotonic_timestamps_raises(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 15, 10, 30, 1, tzinfo=timezone.utc)
        series = MeasurementSeries(
            measurement_id="series-001",
            quantity="voltage",
            values=[118.5, 119.2],
            unit="V",
            sampling_rate=Quantity(value=1.0, unit="Hz"),
            start_time=t0,
            timestamps=[t1, t0],
            source_type=SourceType.RAW,
        )
        errors = validate_measurement_series(series)
        assert any("monotonically increasing" in e for e in errors)


class TestValidateDerivedMeasurement:
    def test_valid_derived_measurement(self):
        derived = DerivedMeasurement(
            measurement_id="derived-001",
            quantity="avg_voltage",
            value=Quantity(value=118.9, unit="V"),
            source_ids=("meas-001",),
            transformation="average",
            source_type=SourceType.DERIVED,
        )
        errors = validate_derived_measurement(derived)
        assert errors == ()

    def test_non_finite_value_raises(self):
        derived = DerivedMeasurement(
            measurement_id="derived-001",
            quantity="avg_voltage",
            value=Quantity(value=float("nan"), unit="V"),
            source_type=SourceType.DERIVED,
        )
        errors = validate_derived_measurement(derived)
        assert any("finite" in e for e in errors)

    def test_missing_transformation_with_sources_raises(self):
        derived = DerivedMeasurement(
            measurement_id="derived-001",
            quantity="avg_voltage",
            value=Quantity(value=118.9, unit="V"),
            source_ids=("meas-001",),
            source_type=SourceType.DERIVED,
        )
        errors = validate_derived_measurement(derived)
        assert any("transformation" in e for e in errors)


class TestValidateMeasurementDispatch:
    def test_dispatch_raw(self):
        raw = RawMeasurement(
            measurement_id="m-001",
            quantity="voltage",
            values=[1.0],
            unit="V",
        )
        errors = validate_measurement(raw)
        assert errors == ()

    def test_dispatch_series(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        series = MeasurementSeries(
            measurement_id="s-001",
            quantity="voltage",
            values=[1.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=t0,
            source_type=SourceType.RAW,
        )
        errors = validate_measurement(series)
        assert errors == ()

    def test_dispatch_derived(self):
        derived = DerivedMeasurement(
            measurement_id="d-001",
            quantity="avg_v",
            value=Quantity(value=1.0, unit="V"),
            source_type=SourceType.DERIVED,
        )
        errors = validate_measurement(derived)
        assert errors == ()

    def test_dispatch_unknown_raises(self):
        with pytest.raises(MeasurementValidationError, match="Unknown measurement type"):
            validate_measurement("not-a-measurement")
