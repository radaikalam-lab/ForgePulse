"""Tests for SIMULATED/MEASURED source separation and measurement stages."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.measurement import (
    DerivedMeasurement,
    MeasurementSeries,
    RawMeasurement,
    SourceType,
)
from forgepulse.measurement.derivation import compute_power
from forgepulse.measurement.pipeline import MeasurementIngestionBoundary


class TestSourceSeparation:
    def test_simulated_source_type(self):
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
        assert series.source_type != SourceType.MEASURED
        assert series.source_type != SourceType.RAW

    def test_measured_source_type(self):
        raw = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[118.5],
            unit="V",
            source_type=SourceType.MEASURED,
        )
        assert raw.source_type == SourceType.MEASURED
        assert raw.source_type != SourceType.SIMULATED
        assert raw.source_type != SourceType.RAW

    def test_raw_source_type(self):
        raw = RawMeasurement(
            measurement_id="raw-001",
            quantity="voltage",
            values=[118.5],
            unit="V",
            source_type=SourceType.RAW,
        )
        assert raw.source_type == SourceType.RAW
        assert raw.source_type != SourceType.SIMULATED
        assert raw.source_type != SourceType.MEASURED

    def test_simulated_never_becomes_measured(self):
        series = MeasurementSeries(
            measurement_id="sim-002",
            quantity="voltage",
            values=[120.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.SIMULATED,
        )
        assert series.source_type != SourceType.MEASURED
        assert series.source_type != SourceType.RAW

    def test_derived_from_simulated_remains_derived(self):
        voltage = MeasurementSeries(
            measurement_id="sim-v",
            quantity="voltage",
            values=[10.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.SIMULATED,
        )
        current = MeasurementSeries(
            measurement_id="sim-i",
            quantity="current",
            values=[2.0],
            unit="A",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.SIMULATED,
        )
        power = compute_power(voltage, current)
        assert power.source_type == SourceType.DERIVED

    def test_synthetic_edge_source_produces_simulated(self):
        from forgepulse.integration import SyntheticEdgeSource
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_voltage_series(
            measurement_id="v-001",
            duration_s=0.1,
            sampling_rate_hz=100.0,
            nominal_voltage_v=120.0,
        )
        assert measurement.source_type == SourceType.SIMULATED

    def test_measurement_translator_produces_raw(self):
        from forgepulse.integration import MeasurementTranslator
        translator = MeasurementTranslator()
        raw = {"values": [1.0, 2.0], "unit": "V", "sampling_rate": 100.0}
        result = translator.translate_voltage("m-001", raw)
        assert result.source_type == SourceType.RAW

    def test_simulated_measurement_distinct_from_measured(self):
        sim = RawMeasurement(
            measurement_id="sim-001",
            quantity="voltage",
            values=[120.0],
            unit="V",
            source_type=SourceType.SIMULATED,
        )
        meas = RawMeasurement(
            measurement_id="meas-001",
            quantity="voltage",
            values=[118.5],
            unit="V",
            source_type=SourceType.MEASURED,
        )
        assert sim.source_type != meas.source_type
        assert sim.source_type == SourceType.SIMULATED
        assert meas.source_type == SourceType.MEASURED

    def test_measured_data_enters_same_pipeline(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        raw = RawMeasurement(
            measurement_id="daq-001",
            quantity="voltage",
            values=[10.0, 20.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            instrument_reference="daq-01",
            source_type=SourceType.MEASURED,
        )
        result = boundary.ingest_raw(raw)
        assert result.source_type == SourceType.MEASURED
        assert boundary.ingested_count == 1

    def test_simulated_data_enters_same_pipeline(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.SIMULATED)
        raw = RawMeasurement(
            measurement_id="sim-001",
            quantity="voltage",
            values=[10.0, 20.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            instrument_reference="simulator",
            source_type=SourceType.SIMULATED,
        )
        result = boundary.ingest_raw(raw)
        assert result.source_type == SourceType.SIMULATED
        assert boundary.ingested_count == 1
