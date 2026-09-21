"""Tests for measurement domain models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
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


class TestRawMeasurement:
    def test_raw_measurement_preserved(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[118.5, 119.2, 118.9],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 5, tzinfo=timezone.utc),
            instrument_reference="daq-01",
            provenance=ProvenanceReference(measurement_id="meas-001"),
        )
        assert raw.values == [118.5, 119.2, 118.9]
        assert raw.source_type == SourceType.RAW

    def test_raw_measurement_has_explicit_unit(self):
        raw = RawMeasurement(
            measurement_id="meas-002",
            quantity="temperature",
            values=[300.0],
            unit="K",
        )
        assert raw.unit == "K"


class TestDerivedMeasurement:
    def test_derived_preserves_lineage(self):
        derived = DerivedMeasurement(
            measurement_id="derived-001",
            quantity="avg_voltage",
            value=Quantity(value=118.9, unit="V"),
            source_ids=("meas-001",),
            transformation="average",
            provenance=ProvenanceReference(measurement_id="meas-001"),
        )
        assert "meas-001" in derived.source_ids
        assert derived.transformation == "average"

    def test_derived_does_not_replace_raw(self):
        raw = RawMeasurement(
            measurement_id="meas-003",
            quantity="voltage",
            values=[118.5],
            unit="V",
        )
        derived = DerivedMeasurement(
            measurement_id="derived-002",
            quantity="avg_voltage",
            value=Quantity(value=118.5, unit="V"),
            source_ids=(raw.measurement_id,),
        )
        assert raw.values == [118.5]
        assert derived.value.value == 118.5
        assert raw.measurement_id != derived.measurement_id


class TestMeasurementSeries:
    def test_scalar_measurement_series(self):
        series = MeasurementSeries(
            measurement_id="series-001",
            quantity="voltage",
            values=[118.5],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.RAW,
        )
        assert series.values == [118.5]
        assert series.unit == "V"

    def test_time_series_with_timestamps(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 15, 10, 30, 1, tzinfo=timezone.utc)
        series = MeasurementSeries(
            measurement_id="series-002",
            quantity="current",
            values=[0.5, 0.6],
            unit="A",
            sampling_rate=Quantity(value=1.0, unit="Hz"),
            start_time=t0,
            timestamps=[t0, t1],
            source_type=SourceType.RAW,
        )
        assert len(series.timestamps) == 2
        assert series.timestamps[0] == t0


class TestSimulatedSource:
    def test_simulated_source_explicitly_identified(self):
        series = MeasurementSeries(
            measurement_id="sim-001",
            quantity="voltage",
            values=[120.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.SIMULATED,
        )
        assert series.source_type == SourceType.SIMULATED

    def test_raw_not_confused_with_simulated(self):
        raw = MeasurementSeries(
            measurement_id="raw-001",
            quantity="voltage",
            values=[120.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.RAW,
        )
        sim = MeasurementSeries(
            measurement_id="sim-002",
            quantity="voltage",
            values=[120.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.SIMULATED,
        )
        assert raw.source_type != sim.source_type


class TestMeasuredVsEstimated:
    def test_measured_distinction(self):
        raw = RawMeasurement(
            measurement_id="m-001",
            quantity="voltage",
            values=[118.5],
            unit="V",
        )
        derived = DerivedMeasurement(
            measurement_id="d-001",
            quantity="estimated_voltage",
            value=Quantity(value=120.0, unit="V"),
            source_ids=(),
            transformation="model_estimate",
        )
        assert raw.source_type == SourceType.RAW
        assert derived.source_type == SourceType.DERIVED
        assert derived.measurement_id != raw.measurement_id
