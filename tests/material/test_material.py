"""Tests for material domain models."""

from __future__ import annotations

import pytest

from forgepulse.common import Quantity
from forgepulse.material import (
    CharacterizationResult,
    MaterialResult,
    MaterialState,
    YieldBasis,
    YieldRepresentation,
)


class TestMaterialResult:
    def test_material_result_representation(self):
        result = MaterialResult(
            material_result_id="mat-001",
            experiment_id="exp-001",
            yield_representation=YieldRepresentation(
                value=0.35,
                unit="g/g",
                basis=YieldBasis.MASS_BASIS,
                calculation_method="final_mass / initial_mass",
                input_references=("meas-001", "meas-002"),
            ),
            material_state=MaterialState(
                composition={"carbon": Quantity(value=0.92, unit="mass_fraction")},
            ),
        )
        assert result.yield_representation.value == 0.35
        assert result.yield_representation.basis == YieldBasis.MASS_BASIS

    def test_explicit_yield_basis(self):
        yield_rep = YieldRepresentation(
            value=0.35,
            unit="g/g",
            basis=YieldBasis.MASS_BASIS,
            calculation_method="final_mass / initial_mass",
        )
        assert yield_rep.basis is not None
        assert yield_rep.calculation_method == "final_mass / initial_mass"

    def test_different_yield_bases(self):
        mass_basis = YieldBasis.MASS_BASIS
        molar_basis = YieldBasis.MOLAR_BASIS
        assert mass_basis != molar_basis


class TestMaterialState:
    def test_unknown_values_remain_unknown(self):
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


class TestProvenancePreservation:
    def test_yield_provenance_preserved(self):
        yield_rep = YieldRepresentation(
            value=0.35,
            unit="g/g",
            basis=YieldBasis.MASS_BASIS,
            calculation_method="final_mass / initial_mass",
            input_references=("meas-001",),
            provenance={"experiment_id": "exp-001"},
        )
        assert yield_rep.input_references == ("meas-001",)
        assert yield_rep.provenance["experiment_id"] == "exp-001"

    def test_material_result_provenance(self):
        result = MaterialResult(
            material_result_id="mat-002",
            experiment_id="exp-001",
            provenance={"derived_from": "exec-001"},
        )
        assert result.provenance["derived_from"] == "exec-001"
