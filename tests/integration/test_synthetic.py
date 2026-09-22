"""Tests for SyntheticEdgeSource."""

from __future__ import annotations

import pytest

from forgepulse.common import Quantity
from forgepulse.integration import SyntheticEdgeSource
from forgepulse.measurement import SourceType


class TestSyntheticEdgeSource:
    def test_generate_voltage_series_returns_raw_measurement(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_voltage_series(
            measurement_id="vol-001",
            duration_s=1.0,
            sampling_rate_hz=100.0,
            nominal_voltage_v=120.0,
        )
        assert measurement.measurement_id == "vol-001"
        assert measurement.quantity == "voltage"
        assert measurement.unit == "V"
        assert len(measurement.values) == 100
        assert measurement.source_type == SourceType.SIMULATED
        assert measurement.sampling_rate == Quantity(value=100.0, unit="Hz")

    def test_generate_current_series_returns_raw_measurement(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_current_series(
            measurement_id="cur-001",
            duration_s=0.5,
            sampling_rate_hz=200.0,
            nominal_current_a=10.0,
        )
        assert measurement.measurement_id == "cur-001"
        assert measurement.quantity == "current"
        assert measurement.unit == "A"
        assert len(measurement.values) == 100
        assert measurement.source_type == SourceType.SIMULATED

    def test_generate_temperature_series_returns_raw_measurement(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_temperature_series(
            measurement_id="temp-001",
            duration_s=2.0,
            sampling_rate_hz=50.0,
            nominal_temp_c=300.0,
        )
        assert measurement.measurement_id == "temp-001"
        assert measurement.quantity == "temperature"
        assert measurement.unit == "C"
        assert len(measurement.values) == 100
        assert measurement.source_type == SourceType.SIMULATED

    def test_generate_pulse_profile_returns_raw_measurement(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_pulse_profile(
            measurement_id="pulse-001",
            voltage_v=500.0,
            duration_s=0.1,
            sampling_rate_hz=1000.0,
        )
        assert measurement.measurement_id == "pulse-001"
        assert measurement.quantity == "voltage"
        assert measurement.unit == "V"
        assert len(measurement.values) == 100
        assert measurement.source_type == SourceType.SIMULATED

    def test_deterministic_with_seed(self):
        source1 = SyntheticEdgeSource(seed=42)
        source2 = SyntheticEdgeSource(seed=42)
        m1 = source1.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        m2 = source2.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert m1.values == m2.values

    def test_different_seeds_produce_different_values(self):
        source1 = SyntheticEdgeSource(seed=1)
        source2 = SyntheticEdgeSource(seed=2)
        m1 = source1.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        m2 = source2.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert m1.values != m2.values

    def test_start_time_is_utc(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_voltage_series(
            measurement_id="vol-001",
            duration_s=1.0,
            sampling_rate_hz=100.0,
            nominal_voltage_v=120.0,
        )
        assert measurement.start_time.tzinfo is not None
