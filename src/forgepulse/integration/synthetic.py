"""Synthetic edge source for testing and simulation."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from forgepulse.common import Quantity
from forgepulse.measurement import RawMeasurement, SourceType


@dataclass
class SyntheticEdgeSource:
    """Generates deterministic synthetic measurement data.

    This source does not connect to any real hardware or network.
    All values are generated using deterministic algorithms with optional
    configurable seed for reproducibility.
    """

    seed: Optional[int] = None
    _rng: random.Random = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self._rng is None:
            self._rng = random.Random(self.seed)

    def _generate_start_time(self) -> datetime:
        base_seed = self.seed if self.seed is not None else 0
        h = hashlib.sha256(str(base_seed).encode("utf-8")).hexdigest()
        offset_seconds = int(h[:8], 16) % 1_000_000
        return datetime.fromtimestamp(1_700_000_000 + offset_seconds, tz=timezone.utc)

    def generate_voltage_series(
        self,
        measurement_id: str,
        duration_s: float,
        sampling_rate_hz: float,
        nominal_voltage_v: float,
        noise_std_v: float = 0.1,
    ) -> RawMeasurement:
        """Generate a synthetic voltage measurement series.

        Args:
            measurement_id: Unique identifier for this measurement.
            duration_s: Duration of the measurement in seconds.
            sampling_rate_hz: Sampling rate in Hz.
            nominal_voltage_v: Nominal voltage value.
            noise_std_v: Standard deviation of Gaussian noise.

        Returns:
            A RawMeasurement with generated voltage values.
        """
        num_samples = int(duration_s * sampling_rate_hz)
        values = [
            nominal_voltage_v + self._rng.gauss(0, noise_std_v)
            for _ in range(num_samples)
        ]
        start_time = self._generate_start_time()
        return RawMeasurement(
            measurement_id=measurement_id,
            quantity="voltage",
            values=values,
            unit="V",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            source_type=SourceType.SIMULATED,
        )

    def generate_current_series(
        self,
        measurement_id: str,
        duration_s: float,
        sampling_rate_hz: float,
        nominal_current_a: float,
        noise_std_a: float = 0.01,
    ) -> RawMeasurement:
        """Generate a synthetic current measurement series.

        Args:
            measurement_id: Unique identifier for this measurement.
            duration_s: Duration of the measurement in seconds.
            sampling_rate_hz: Sampling rate in Hz.
            nominal_current_a: Nominal current value.
            noise_std_a: Standard deviation of Gaussian noise.

        Returns:
            A RawMeasurement with generated current values.
        """
        num_samples = int(duration_s * sampling_rate_hz)
        values = [
            nominal_current_a + self._rng.gauss(0, noise_std_a)
            for _ in range(num_samples)
        ]
        start_time = self._generate_start_time()
        return RawMeasurement(
            measurement_id=measurement_id,
            quantity="current",
            values=values,
            unit="A",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            source_type=SourceType.SIMULATED,
        )

    def generate_temperature_series(
        self,
        measurement_id: str,
        duration_s: float,
        sampling_rate_hz: float,
        nominal_temp_c: float,
        noise_std_c: float = 0.5,
    ) -> RawMeasurement:
        """Generate a synthetic temperature measurement series.

        Args:
            measurement_id: Unique identifier for this measurement.
            duration_s: Duration of the measurement in seconds.
            sampling_rate_hz: Sampling rate in Hz.
            nominal_temp_c: Nominal temperature in Celsius.
            noise_std_c: Standard deviation of Gaussian noise.

        Returns:
            A RawMeasurement with generated temperature values.
        """
        num_samples = int(duration_s * sampling_rate_hz)
        values = [
            nominal_temp_c + self._rng.gauss(0, noise_std_c)
            for _ in range(num_samples)
        ]
        start_time = self._generate_start_time()
        return RawMeasurement(
            measurement_id=measurement_id,
            quantity="temperature",
            values=values,
            unit="C",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            source_type=SourceType.SIMULATED,
        )

    def generate_pulse_profile(
        self,
        measurement_id: str,
        voltage_v: float,
        duration_s: float,
        sampling_rate_hz: float = 1000.0,
    ) -> RawMeasurement:
        """Generate a synthetic pulse profile with ramped voltage.

        Args:
            measurement_id: Unique identifier for this measurement.
            voltage_v: Peak voltage of the pulse.
            duration_s: Duration of the pulse in seconds.
            sampling_rate_hz: Sampling rate in Hz.

        Returns:
            A RawMeasurement with generated pulse voltage values.
        """
        num_samples = int(duration_s * sampling_rate_hz)
        rise_time = duration_s * 0.1
        fall_time = duration_s * 0.9
        values = []
        for i in range(num_samples):
            t = i / sampling_rate_hz
            if t < rise_time:
                v = voltage_v * (t / rise_time)
            elif t < fall_time:
                v = voltage_v
            else:
                v = voltage_v * (1 - (t - fall_time) / (duration_s - fall_time))
            values.append(v + self._rng.gauss(0, 0.01))
        start_time = self._generate_start_time()
        return RawMeasurement(
            measurement_id=measurement_id,
            quantity="voltage",
            values=values,
            unit="V",
            sampling_rate=Quantity(value=sampling_rate_hz, unit="Hz"),
            start_time=start_time,
            source_type=SourceType.SIMULATED,
        )
