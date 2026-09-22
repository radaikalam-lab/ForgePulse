"""Tests for Phase 4 material state and characterization integration."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.measurement import (
    MeasurementSeries,
    SourceType,
)
from forgepulse.measurement.characterization import (
    CharacterizationResult,
    ElectricalCharacterization,
    ThermalCharacterization,
)
from forgepulse.measurement.pipeline import MeasurementPipeline, MeasurementIngestionBoundary
from forgepulse.material import (
    CharacterizationResult as MaterialCharResult,
    MaterialResult,
    MaterialState,
    YieldBasis,
    YieldRepresentation,
)


class TestMaterialStateProvenance:
    def test_material_state_with_provenance(self):
        state = MaterialState(
            composition={"carbon": Quantity(value=0.92, unit="mass_fraction")},
            provenance={"experiment_id": "exp-001", "measurement_id": "meas-001"},
        )
        assert state.provenance["experiment_id"] == "exp-001"

    def test_unknown_properties_remain_unknown(self):
        state = MaterialState(
            composition={"carbon": Quantity(value=0.92, unit="mass_fraction")},
            structure=None,
            morphology=None,
        )
        assert state.composition is not None
        assert state.structure is None
        assert state.morphology is None

    def test_no_manufactured_values(self):
        state = MaterialState()
        assert state.composition is None
        assert state.structure is None
        assert state.electronic_properties is None


class TestCharacterizationIntegration:
    def test_measurement_to_characterization_lineage(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        voltage = MeasurementSeries(
            measurement_id="vol-001",
            quantity="voltage",
            values=[10.0, 20.0],
            unit="V",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=t0,
            source_type=SourceType.MEASURED,
        )
        current = MeasurementSeries(
            measurement_id="cur-001",
            quantity="current",
            values=[2.0, 2.0],
            unit="A",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=t0,
            source_type=SourceType.MEASURED,
        )
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        char = pipeline.characterize_electrical(voltage, current, "char-001")
        assert char.peak_voltage_v.value == 20.0
        assert char.provenance is not None

    def test_thermal_measurement_to_characterization(self):
        t0 = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        temp = MeasurementSeries(
            measurement_id="temp-001",
            quantity="temperature",
            values=[300.0, 500.0],
            unit="K",
            sampling_rate=Quantity(value=1000.0, unit="Hz"),
            start_time=t0,
            source_type=SourceType.MEASURED,
        )
        boundary = MeasurementIngestionBoundary(source_type=SourceType.MEASURED)
        pipeline = MeasurementPipeline(ingestion_boundary=boundary)
        char = pipeline.characterize_thermal(temp, "char-002")
        assert char.peak_temperature_k.value == 500.0
        assert char.temperature_rise_k.value == 200.0

    def test_characterization_result_preserves_source_measurements(self):
        char = CharacterizationResult(
            result_id="char-001",
            technique="electrical_characterization",
            summary="Peak voltage from measurement",
            source_measurement_ids=("vol-001", "cur-001"),
        )
        assert "vol-001" in char.source_measurement_ids
        assert "cur-001" in char.source_measurement_ids

    def test_material_result_aggregates_characterization(self):
        result = MaterialResult(
            material_result_id="mat-001",
            experiment_id="exp-001",
            yield_representation=YieldRepresentation(
                value=0.35,
                unit="g/g",
                basis=YieldBasis.MASS_BASIS,
                calculation_method="final_mass / initial_mass",
                input_references=("meas-001",),
            ),
            material_state=MaterialState(
                composition={"carbon": Quantity(value=0.92, unit="mass_fraction")},
            ),
            characterizations=(
                MaterialCharResult(
                    result_id="char-001",
                    technique="electrical_characterization",
                    summary="Test characterization",
                ),
            ),
        )
        assert result.yield_representation.value == 0.35
        assert len(result.characterizations) == 1
        assert result.characterizations[0].technique == "electrical_characterization"

    def test_yield_basis_is_explicit(self):
        yield_rep = YieldRepresentation(
            value=0.35,
            unit="g/g",
            basis=YieldBasis.MASS_BASIS,
            calculation_method="final_mass / initial_mass",
        )
        assert yield_rep.basis == YieldBasis.MASS_BASIS
        assert yield_rep.calculation_method is not None

    def test_yield_not_fabricated_when_absent(self):
        result = MaterialResult(
            material_result_id="mat-002",
            experiment_id="exp-001",
        )
        assert result.yield_representation is None

    def test_no_unsupported_material_properties(self):
        state = MaterialState()
        assert state.composition is None
        assert state.structure is None
        assert state.optical_properties is None
        assert state.mechanical_properties is None

    def test_characterization_methods_explicit(self):
        from forgepulse.measurement.characterization import CharacterizationMethod
        assert CharacterizationMethod.RAMAN.value == "Raman"
        assert CharacterizationMethod.XRD.value == "XRD"
        assert CharacterizationMethod.SEM.value == "SEM"
        assert CharacterizationMethod.TEM.value == "TEM"
        assert CharacterizationMethod.ELECTRICAL.value == "electrical_characterization"
        assert CharacterizationMethod.THERMAL.value == "thermal_characterization"
