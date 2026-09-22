"""Tests for measurement characterization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.measurement import (
    MeasurementSeries,
    SourceType,
)
from forgepulse.measurement.characterization import (
    CharacterizationMethod,
    CharacterizationResult,
    ElectricalCharacterization,
    ThermalCharacterization,
    Uncertainty,
)
from forgepulse.measurement.derivation import compute_power, compute_pulse_statistics
from forgepulse.measurement.pipeline import MeasurementPipeline, MeasurementIngestionBoundary


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
        source_type=SourceType.RAW,
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
        source_type=SourceType.RAW,
    )


def _make_temperature_series():
    t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    return MeasurementSeries(
        measurement_id="temp-001",
        quantity="temperature",
        values=[300.0, 400.0, 350.0],
        unit="K",
        sampling_rate=Quantity(value=1000.0, unit="Hz"),
        start_time=t0,
        timestamps=[t0.replace(microsecond=i * 1000) for i in range(3)],
        source_type=SourceType.RAW,
    )


class TestUncertainty:
    def test_uncertainty_defaults(self):
        u = Uncertainty()
        assert u.standard_uncertainty is None
        assert u.expanded_uncertainty is None
        assert u.confidence_level is None
        assert u.coverage_factor is None

    def test_uncertainty_with_values(self):
        u = Uncertainty(
            standard_uncertainty=Quantity(value=0.1, unit="V"),
            confidence_level=0.95,
        )
        assert u.standard_uncertainty.value == 0.1
        assert u.confidence_level == 0.95

    def test_confidence_level_out_of_range_raises(self):
        with pytest.raises(ValueError, match="confidence_level"):
            Uncertainty(confidence_level=1.5)

    def test_uncertainty_distinct_from_confidence(self):
        u = Uncertainty(confidence_level=0.95)
        assert u.confidence_level == 0.95
        assert u.standard_uncertainty is None


class TestElectricalCharacterization:
    def test_electrical_characterization_defaults(self):
        char = ElectricalCharacterization()
        assert char.peak_voltage_v is None
        assert char.peak_current_a is None
        assert char.average_power_w is None
        assert char.pulse_energy_j is None
        assert char.provenance is not None

    def test_electrical_characterization_with_values(self):
        char = ElectricalCharacterization(
            peak_voltage_v=Quantity(value=50.0, unit="V"),
            peak_current_a=Quantity(value=5.0, unit="A"),
            average_power_w=Quantity(value=100.0, unit="W"),
            pulse_energy_j=Quantity(value=500.0, unit="J"),
        )
        assert char.peak_voltage_v.value == 50.0
        assert char.average_power_w.value == 100.0

    def test_electrical_characterization_from_pipeline(self):
        voltage = _make_voltage_series()
        current = _make_current_series()
        pipeline = MeasurementPipeline(
            ingestion_boundary=MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        )
        char = pipeline.characterize_electrical(voltage, current, "char-001")
        assert char.peak_voltage_v.value == 30.0
        assert char.peak_current_a.value == 2.0
        assert char.average_voltage_v.value == 20.0
        assert char.pulse_energy_j.value > 0


class TestThermalCharacterization:
    def test_thermal_characterization_defaults(self):
        char = ThermalCharacterization()
        assert char.peak_temperature_k is None
        assert char.temperature_rise_k is None
        assert char.heating_rate_k_s is None
        assert char.cooling_rate_k_s is None
        assert char.provenance is not None

    def test_thermal_characterization_from_pipeline(self):
        temp = _make_temperature_series()
        pipeline = MeasurementPipeline(
            ingestion_boundary=MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        )
        char = pipeline.characterize_thermal(temp, "char-002")
        assert char.peak_temperature_k.value == 400.0
        assert char.temperature_rise_k.value == 100.0
        assert char.heating_rate_k_s is not None
        assert char.cooling_rate_k_s is not None

    def test_thermal_characterization_without_timestamps(self):
        temp = MeasurementSeries(
            measurement_id="temp-002",
            quantity="temperature",
            values=[300.0, 400.0],
            unit="K",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.RAW,
        )
        pipeline = MeasurementPipeline(
            ingestion_boundary=MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        )
        char = pipeline.characterize_thermal(temp, "char-003")
        assert char.peak_temperature_k.value == 400.0
        assert char.temperature_rise_k.value == 100.0
        assert char.heating_rate_k_s is None
        assert char.cooling_rate_k_s is None


class TestCharacterizationResult:
    def test_characterization_result_creation(self):
        result = CharacterizationResult(
            result_id="char-001",
            technique="electrical_characterization",
            summary="Peak voltage observed",
            property="peak_voltage",
            value=Quantity(value=50.0, unit="V"),
            unit="V",
            method="peak",
            source_measurement_ids=("vol-001",),
        )
        assert result.result_id == "char-001"
        assert result.technique == "electrical_characterization"
        assert result.value.value == 50.0
        assert result.source_measurement_ids == ("vol-001",)
        assert result.provenance is not None

    def test_characterization_result_empty_id_raises(self):
        with pytest.raises(ValueError, match="result_id"):
            CharacterizationResult(
                result_id="",
                technique="test",
                summary="test",
            )

    def test_characterization_result_empty_technique_raises(self):
        with pytest.raises(ValueError, match="technique"):
            CharacterizationResult(
                result_id="char-001",
                technique="",
                summary="test",
            )

    def test_characterization_method_enum(self):
        assert CharacterizationMethod.ELECTRICAL.value == "electrical_characterization"
        assert CharacterizationMethod.RAMAN.value == "Raman"
        assert CharacterizationMethod.XRD.value == "XRD"

    def test_characterization_distinct_from_derived_measurement(self):
        derived = MeasurementSeries(
            measurement_id="pwr-001",
            quantity="power",
            values=[20.0],
            unit="W",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.DERIVED,
        )
        char = CharacterizationResult(
            result_id="char-001",
            technique="electrical_characterization",
            summary="Power derived from V and I",
            source_measurement_ids=("vol-001", "cur-001"),
        )
        assert derived.measurement_id != char.result_id
        assert derived.quantity != char.technique
