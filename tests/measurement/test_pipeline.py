"""Tests for measurement pipeline and ingestion boundary."""

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
from forgepulse.measurement.pipeline import (
    IngestionError,
    MeasurementIngestionBoundary,
    MeasurementPipeline,
)


def _make_raw_measurement():
    return RawMeasurement(
        measurement_id="meas-001",
        quantity="voltage",
        values=[10.0, 20.0],
        unit="V",
        sampling_rate=Quantity(value=1000.0, unit="Hz"),
        start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        source_type=SourceType.MEASURED,
    )


def _make_voltage_series():
    t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    return MeasurementSeries(
        measurement_id="vol-001",
        quantity="voltage",
        values=[10.0, 20.0, 30.0],
        unit="V",
        sampling_rate=Quantity(value=1000.0, unit="Hz"),
        start_time=t0,
        timestamps=[t0.replace(microsecond=i * 1000) for i in range(3)],
        source_type=SourceType.MEASURED,
    )


def _make_current_series():
    t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    return MeasurementSeries(
        measurement_id="cur-001",
        quantity="current",
        values=[2.0, 2.0, 2.0],
        unit="A",
        sampling_rate=Quantity(value=1000.0, unit="Hz"),
        start_time=t0,
        timestamps=[t0.replace(microsecond=i * 1000) for i in range(3)],
        source_type=SourceType.MEASURED,
    )


class TestMeasurementIngestionBoundary:
    def test_ingest_valid_raw_measurement(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        raw = _make_raw_measurement()
        result = boundary.ingest_raw(raw)
        assert result.measurement_id == "meas-001"
        assert boundary.ingested_count == 1

    def test_ingest_invalid_raw_raises(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        raw = RawMeasurement(
            measurement_id="",
            quantity="voltage",
            values=[1.0],
            unit="V",
        )
        with pytest.raises(IngestionError, match="Invalid measurement"):
            boundary.ingest_raw(raw)

    def test_ingest_valid_series(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        series = _make_voltage_series()
        result = boundary.ingest_series(series)
        assert result.measurement_id == "vol-001"

    def test_ingest_valid_derived(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        derived = DerivedMeasurement(
            measurement_id="d-001",
            quantity="avg_v",
            value=Quantity(value=15.0, unit="V"),
            source_type=SourceType.DERIVED,
        )
        result = boundary.ingest_derived(derived)
        assert result.measurement_id == "d-001"

    def test_ingested_measurements_tracked(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        raw1 = _make_raw_measurement()
        raw2 = RawMeasurement(
            measurement_id="meas-002",
            quantity="current",
            values=[1.0],
            unit="A",
            source_type=SourceType.MEASURED,
        )
        boundary.ingest_raw(raw1)
        boundary.ingest_raw(raw2)
        assert boundary.ingested_count == 2
        assert len(boundary.ingested_measurements) == 2


class TestMeasurementPipeline:
    def test_process_raw(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        raw = _make_raw_measurement()
        result = pipeline.process_raw(raw)
        assert result.measurement_id == "meas-001"

    def test_derive_power(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        voltage = _make_voltage_series()
        current = _make_current_series()
        power = pipeline.derive_power(voltage, current)
        assert power.quantity == "power"
        assert power.values == [20.0, 40.0, 60.0]
        assert pipeline.derived_count >= 1

    def test_derive_energy(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        voltage = _make_voltage_series()
        current = _make_current_series()
        power = pipeline.derive_power(voltage, current)
        energy = pipeline.derive_energy(power)
        assert energy.quantity == "energy"
        assert energy.value.unit == "J"
        assert pipeline.derived_count >= 2

    def test_derive_pulse_statistics(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        voltage = _make_voltage_series()
        current = _make_current_series()
        stats = pipeline.derive_pulse_statistics(voltage, current)
        assert "peak_voltage" in stats
        assert "peak_current" in stats
        assert "average_voltage" in stats
        assert "average_current" in stats
        assert "pulse_energy" in stats
        assert pipeline.derived_count >= 5

    def test_characterize_electrical(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        voltage = _make_voltage_series()
        current = _make_current_series()
        char = pipeline.characterize_electrical(voltage, current, "char-001")
        assert char.peak_voltage_v.value == 30.0
        assert pipeline.characterization_count == 1

    def test_characterize_thermal(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        temp = MeasurementSeries(
            measurement_id="temp-001",
            quantity="temperature",
            values=[300.0, 400.0, 350.0],
            unit="K",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=t0,
            timestamps=[t0.replace(microsecond=i * 1000) for i in range(3)],
            source_type=SourceType.MEASURED,
        )
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        char = pipeline.characterize_thermal(temp, "char-002")
        assert char.peak_temperature_k.value == 400.0
        assert pipeline.characterization_count == 1

    def test_pipeline_with_simulated_source(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.SIMULATED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        voltage = _make_voltage_series()
        current = _make_current_series()
        power = pipeline.derive_power(voltage, current)
        assert power.source_type == SourceType.DERIVED

    def test_future_physical_edge_compatibility(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        raw = RawMeasurement(
            measurement_id="daq-001",
            quantity="voltage",
            values=[118.5, 119.2],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            instrument_reference="daq-01",
            source_type=SourceType.MEASURED,
        )
        result = boundary.ingest_raw(raw)
        assert result.source_type == SourceType.MEASURED
        assert result.instrument_reference == "daq-01"
        assert boundary.ingested_count == 1

    def test_does_not_control_instruments(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        assert not hasattr(boundary, "start_acquisition")
        assert not hasattr(boundary, "stop_acquisition")
        assert not hasattr(boundary, "configure_device")

    def test_does_not_infer_material_properties(self):
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        assert not hasattr(boundary, "infer_material")
        assert not hasattr(boundary, "classify_material")
