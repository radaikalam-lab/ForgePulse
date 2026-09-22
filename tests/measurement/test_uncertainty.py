"""Tests for measurement uncertainty semantics."""

from __future__ import annotations

import pytest

from forgepulse.common import Quantity
from forgepulse.measurement.characterization import (
    ElectricalCharacterization,
    ThermalCharacterization,
    Uncertainty,
)
from forgepulse.measurement import (
    DerivedMeasurement,
    SourceType,
)
from forgepulse.measurement.pipeline import MeasurementIngestionBoundary


class TestUncertaintyRepresentation:
    def test_uncertainty_defaults_none(self):
        u = Uncertainty()
        assert u.standard_uncertainty is None
        assert u.expanded_uncertainty is None
        assert u.confidence_level is None
        assert u.coverage_factor is None

    def test_uncertainty_with_standard(self):
        u = Uncertainty(standard_uncertainty=Quantity(value=0.1, unit="V"))
        assert u.standard_uncertainty.value == 0.1
        assert u.standard_uncertainty.unit == "V"

    def test_uncertainty_with_expanded(self):
        u = Uncertainty(
            expanded_uncertainty=Quantity(value=0.2, unit="V"),
            coverage_factor=2.0,
        )
        assert u.expanded_uncertainty.value == 0.2
        assert u.coverage_factor == 2.0

    def test_uncertainty_confidence_level_range(self):
        with pytest.raises(ValueError, match="confidence_level"):
            Uncertainty(confidence_level=-0.1)
        with pytest.raises(ValueError, match="confidence_level"):
            Uncertainty(confidence_level=1.5)
        u = Uncertainty(confidence_level=0.95)
        assert u.confidence_level == 0.95

    def test_uncertainty_in_electrical_characterization(self):
        char = ElectricalCharacterization(
            peak_voltage_v=Quantity(value=50.0, unit="V"),
            uncertainty=Uncertainty(
                standard_uncertainty=Quantity(value=0.5, unit="V"),
                confidence_level=0.95,
            ),
        )
        assert char.uncertainty is not None
        assert char.uncertainty.standard_uncertainty.value == 0.5
        assert char.uncertainty.confidence_level == 0.95

    def test_uncertainty_in_thermal_characterization(self):
        char = ThermalCharacterization(
            peak_temperature_k=Quantity(value=1000.0, unit="K"),
            uncertainty=Uncertainty(
                expanded_uncertainty=Quantity(value=10.0, unit="K"),
                coverage_factor=2.0,
            ),
        )
        assert char.uncertainty.expanded_uncertainty.value == 10.0
        assert char.uncertainty.coverage_factor == 2.0

    def test_uncertainty_distinct_from_confidence(self):
        u = Uncertainty(confidence_level=0.95)
        derived = DerivedMeasurement(
            measurement_id="d-001",
            quantity="avg_v",
            value=Quantity(value=15.0, unit="V"),
            source_type=SourceType.DERIVED,
        )
        assert not hasattr(derived, "confidence")
        assert u.confidence_level == 0.95

    def test_no_arbitrary_confidence_as_uncertainty(self):
        u = Uncertainty()
        assert u.standard_uncertainty is None
        assert u.confidence_level is None
        assert u.expanded_uncertainty is None
