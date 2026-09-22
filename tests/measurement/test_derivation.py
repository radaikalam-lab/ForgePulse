"""Tests for deterministic measurement derivation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from forgepulse.common import MeasurementValidationError, Quantity
from forgepulse.measurement import (
    MeasurementSeries,
    RawMeasurement,
    SourceType,
)
from forgepulse.measurement.derivation import (
    PulseStatistics,
    compute_average,
    compute_energy,
    compute_power,
    compute_pulse_statistics,
)


def _make_voltage_series(values=None, unit="V", sampling_rate=None, timestamps=None):
    if values is None:
        values = [10.0, 20.0, 30.0]
    if sampling_rate is None:
        sampling_rate = Quantity(value=1000.0, unit="Hz")
    if timestamps is None:
        base = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        dt = 1.0 / sampling_rate.value if sampling_rate is not None else 0.001
        timestamps = [base + timedelta(seconds=i * dt) for i in range(len(values) + 1)]
    return MeasurementSeries(
        measurement_id="vol-001",
        quantity="voltage",
        values=values,
        unit=unit,
        sampling_rate=sampling_rate,
        start_time=timestamps[0],
        timestamps=timestamps,
        source_type=SourceType.RAW,
    )


def _make_current_series(values=None, unit="A", sampling_rate=None, timestamps=None):
    if values is None:
        values = [2.0, 2.0, 2.0]
    if sampling_rate is None:
        sampling_rate = Quantity(value=1000.0, unit="Hz")
    if timestamps is None:
        base = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        dt = 1.0 / sampling_rate.value if sampling_rate is not None else 0.001
        timestamps = [base + timedelta(seconds=i * dt) for i in range(len(values) + 1)]
    return MeasurementSeries(
        measurement_id="cur-001",
        quantity="current",
        values=values,
        unit=unit,
        sampling_rate=sampling_rate,
        start_time=timestamps[0],
        timestamps=timestamps,
        source_type=SourceType.RAW,
    )


class TestComputePower:
    def test_power_is_voltage_times_current(self):
        voltage = _make_voltage_series([10.0, 20.0, 30.0])
        current = _make_current_series([2.0, 2.0, 2.0])
        power = compute_power(voltage, current)
        assert power.values == [20.0, 40.0, 60.0]
        assert power.unit == "W"
        assert power.quantity == "power"
        assert power.source_type == SourceType.DERIVED

    def test_power_preserves_timestamps(self):
        voltage = _make_voltage_series([10.0, 20.0])
        current = _make_current_series([2.0, 2.0])
        power = compute_power(voltage, current)
        assert power.timestamps == voltage.timestamps

    def test_power_preserves_sampling_rate(self):
        voltage = _make_voltage_series([10.0, 20.0])
        current = _make_current_series([2.0, 2.0])
        power = compute_power(voltage, current)
        assert power.sampling_rate == voltage.sampling_rate

    def test_power_source_ids_preserved(self):
        voltage = _make_voltage_series([10.0])
        current = _make_current_series([2.0])
        power = compute_power(voltage, current)
        assert voltage.measurement_id in power.measurement_id
        assert current.measurement_id in power.measurement_id

    def test_power_mismatched_lengths_raises(self):
        voltage = _make_voltage_series([10.0, 20.0])
        current = _make_current_series([2.0])
        with pytest.raises(MeasurementValidationError, match="length mismatch"):
            compute_power(voltage, current)

    def test_power_with_nan_raises(self):
        voltage = _make_voltage_series([10.0, float("nan")])
        current = _make_current_series([2.0, 2.0])
        with pytest.raises(MeasurementValidationError, match="non-finite"):
            compute_power(voltage, current)

    def test_power_with_infinity_raises(self):
        voltage = _make_voltage_series([10.0, float("inf")])
        current = _make_current_series([2.0, 2.0])
        with pytest.raises(MeasurementValidationError, match="non-finite"):
            compute_power(voltage, current)

    def test_power_deterministic(self):
        voltage = _make_voltage_series([10.0, 20.0, 30.0])
        current = _make_current_series([2.0, 2.0, 2.0])
        result1 = compute_power(voltage, current)
        result2 = compute_power(voltage, current)
        assert result1.values == result2.values

    def test_golden_numerical_power(self):
        voltage = _make_voltage_series([10.0])
        current = _make_current_series([2.0])
        power = compute_power(voltage, current)
        assert power.values[0] == 20.0
        assert power.unit == "W"


class TestComputeEnergy:
    def test_energy_from_power_with_sampling_rate(self):
        power_series = MeasurementSeries(
            measurement_id="pwr-001",
            quantity="power",
            values=[20.0, 40.0, 60.0],
            unit="W",
            sampling_rate=Quantity(value=2.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.DERIVED,
        )
        energy = compute_energy(power_series)
        assert energy.value.value == 60.0
        assert energy.value.unit == "J"
        assert energy.quantity == "energy"
        assert energy.transformation == "integral_power_over_time"

    def test_energy_from_power_with_timestamps(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 15, 10, 30, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 1, 15, 10, 30, 2, tzinfo=timezone.utc)
        power_series = MeasurementSeries(
            measurement_id="pwr-002",
            quantity="power",
            values=[20.0, 40.0],
            unit="W",
            sampling_rate=Quantity(value=1.0, unit="Hz"),
            start_time=t0,
            timestamps=[t0, t1, t2],
            source_type=SourceType.DERIVED,
        )
        energy = compute_energy(power_series)
        assert energy.value.value == 60.0
        assert energy.value.unit == "J"

    def test_energy_golden_numerical(self):
        power_series = MeasurementSeries(
            measurement_id="pwr-003",
            quantity="power",
            values=[20.0],
            unit="W",
            sampling_rate=Quantity(value=5.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.DERIVED,
        )
        energy = compute_energy(power_series)
        assert energy.value.value == 4.0
        assert energy.value.unit == "J"

    def test_energy_deterministic(self):
        power_series = MeasurementSeries(
            measurement_id="pwr-004",
            quantity="power",
            values=[20.0, 40.0],
            unit="W",
            sampling_rate=Quantity(value=1.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.DERIVED,
        )
        e1 = compute_energy(power_series)
        e2 = compute_energy(power_series)
        assert e1.value.value == e2.value.value

    def test_energy_empty_series_raises(self):
        power_series = MeasurementSeries(
            measurement_id="pwr-005",
            quantity="power",
            values=[],
            unit="W",
            sampling_rate=Quantity(value=1.0, unit="Hz"),
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.DERIVED,
        )
        with pytest.raises(MeasurementValidationError, match="at least one value"):
            compute_energy(power_series)

    def test_energy_no_timestamps_no_sampling_rate_raises(self):
        power_series = MeasurementSeries(
            measurement_id="pwr-006",
            quantity="power",
            values=[20.0],
            unit="W",
            start_time=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            source_type=SourceType.DERIVED,
        )
        with pytest.raises(MeasurementValidationError, match="must have either"):
            compute_energy(power_series)


class TestComputePulseStatistics:
    def test_peak_values(self):
        voltage = _make_voltage_series([10.0, 50.0, 30.0])
        current = _make_current_series([2.0, 5.0, 3.0])
        stats = compute_pulse_statistics(voltage, current)
        assert stats.peak_voltage_v == 50.0
        assert stats.peak_current_a == 5.0

    def test_average_values(self):
        voltage = _make_voltage_series([10.0, 20.0, 30.0])
        current = _make_current_series([2.0, 2.0, 2.0])
        stats = compute_pulse_statistics(voltage, current)
        assert stats.avg_voltage_v == 20.0
        assert stats.avg_current_a == 2.0

    def test_pulse_duration_from_sampling_rate(self):
        voltage = _make_voltage_series([10.0, 20.0, 30.0])
        current = _make_current_series([2.0, 2.0, 2.0])
        stats = compute_pulse_statistics(voltage, current)
        assert stats.pulse_duration_s == 0.003

    def test_pulse_energy_from_sampling_rate(self):
        voltage = _make_voltage_series([10.0, 20.0, 30.0])
        current = _make_current_series([2.0, 2.0, 2.0])
        stats = compute_pulse_statistics(voltage, current)
        expected_energy = (20.0 + 40.0 + 60.0) * 0.001
        assert abs(stats.pulse_energy_j - expected_energy) < 1e-10

    def test_inter_pulse_interval(self):
        voltage = _make_voltage_series([10.0])
        current = _make_current_series([2.0])
        stats = compute_pulse_statistics(voltage, current, inter_pulse_interval_s=1.5)
        assert stats.inter_pulse_interval_s == 1.5

    def test_deterministic(self):
        voltage = _make_voltage_series([10.0, 20.0])
        current = _make_current_series([2.0, 2.0])
        s1 = compute_pulse_statistics(voltage, current)
        s2 = compute_pulse_statistics(voltage, current)
        assert s1.peak_voltage_v == s2.peak_voltage_v
        assert s1.pulse_energy_j == s2.pulse_energy_j


class TestComputeAverage:
    def test_average_of_values(self):
        assert compute_average([1.0, 2.0, 3.0]) == 2.0

    def test_average_single_value(self):
        assert compute_average([5.0]) == 5.0

    def test_average_empty_raises(self):
        with pytest.raises(MeasurementValidationError, match="at least one value"):
            compute_average([])

    def test_average_nan_raises(self):
        with pytest.raises(MeasurementValidationError, match="non-finite"):
            compute_average([1.0, float("nan")])


class TestGoldenNumerical:
    def test_v10_i2_duration5s(self):
        dt = 0.001
        n = int(5.0 / dt)
        voltage = _make_voltage_series(
            [10.0] * n,
            sampling_rate=Quantity(value=1.0 / dt, unit="Hz"),
        )
        current = _make_current_series(
            [2.0] * n,
            sampling_rate=Quantity(value=1.0 / dt, unit="Hz"),
        )
        power = compute_power(voltage, current)
        assert all(p == 20.0 for p in power.values)
        energy = compute_energy(power)
        assert abs(energy.value.value - 100.0) < 1e-6
        assert energy.value.unit == "J"
