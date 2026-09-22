"""Tests for MeasurementTranslator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import MeasurementValidationError, Quantity
from forgepulse.integration import MeasurementTranslator
from forgepulse.measurement import SourceType


class TestMeasurementTranslator:
    def test_translate_basic_voltage(self):
        translator = MeasurementTranslator()
        raw = {
            "values": [1.0, 2.0, 3.0],
            "unit": "V",
            "sampling_rate": 100.0,
        }
        result = translator.translate_voltage("meas-001", raw)
        assert result.measurement_id == "meas-001"
        assert result.quantity == "voltage"
        assert result.values == [1.0, 2.0, 3.0]
        assert result.unit == "V"
        assert result.sampling_rate == Quantity(value=100.0, unit="Hz")
        assert result.source_type == SourceType.RAW

    def test_translate_with_dict_sampling_rate(self):
        translator = MeasurementTranslator()
        raw = {
            "values": [1.0, 2.0],
            "unit": "V",
            "sampling_rate": {"value": 50.0, "unit": "Hz"},
        }
        result = translator.translate("meas-001", raw, quantity="voltage")
        assert result.sampling_rate == Quantity(value=50.0, unit="Hz")

    def test_translate_with_iso_timestamp(self):
        translator = MeasurementTranslator()
        raw = {
            "values": [1.0],
            "unit": "V",
            "start_time": "2026-01-15T10:30:00Z",
        }
        result = translator.translate("meas-001", raw, quantity="voltage")
        assert result.start_time == datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_translate_missing_values_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="values must be a non-empty list"):
            translator.translate("meas-001", {"unit": "V"}, quantity="voltage")

    def test_translate_empty_values_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="values must be a non-empty list"):
            translator.translate("meas-001", {"values": [], "unit": "V"}, quantity="voltage")

    def test_translate_non_numeric_values_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="values must contain only numbers"):
            translator.translate("meas-001", {"values": ["a"], "unit": "V"}, quantity="voltage")

    def test_translate_missing_unit_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="unit must be a non-empty string"):
            translator.translate("meas-001", {"values": [1.0]}, quantity="voltage")

    def test_translate_empty_unit_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="unit must be a non-empty string"):
            translator.translate("meas-001", {"values": [1.0], "unit": ""}, quantity="voltage")

    def test_translate_batch(self):
        translator = MeasurementTranslator()
        raw_list = [
            {"measurement_id": "m1", "values": [1.0], "unit": "V", "quantity": "voltage"},
            {"measurement_id": "m2", "values": [2.0], "unit": "A", "quantity": "current"},
        ]
        results = translator.translate_batch(raw_list)
        assert len(results) == 2
        assert results[0].measurement_id == "m1"
        assert results[0].quantity == "voltage"
        assert results[1].measurement_id == "m2"
        assert results[1].quantity == "current"

    def test_translate_batch_missing_id_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="measurement_id is required"):
            translator.translate_batch([{"values": [1.0], "unit": "V"}])

    def test_translate_invalid_sampling_rate_raises(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="sampling_rate must be"):
            translator.translate("m1", {"values": [1.0], "unit": "V", "sampling_rate": "invalid"}, quantity="voltage")
