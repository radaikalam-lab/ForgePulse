"""Material domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional

from forgepulse.common import Quantity


class YieldBasis(StrEnum):
    MASS_BASIS = "mass_basis"
    MOLAR_BASIS = "molar_basis"
    ELEMENTAL_BASIS = "elemental_basis"
    ENERGY_BASIS = "energy_basis"
    PROCESS_BASIS = "process_basis"


@dataclass(frozen=True)
class YieldRepresentation:
    value: float
    unit: str
    basis: YieldBasis
    calculation_method: str
    input_references: tuple[str, ...] = ()
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MaterialState:
    composition: Optional[dict[str, Optional[Quantity]]] = None
    structure: Optional[str] = None
    morphology: Optional[str] = None
    electronic_properties: Optional[dict[str, Optional[Quantity]]] = None
    thermal_properties: Optional[dict[str, Optional[Quantity]]] = None
    optical_properties: Optional[dict[str, Optional[Quantity]]] = None
    mechanical_properties: Optional[dict[str, Optional[Quantity]]] = None
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CharacterizationResult:
    result_id: str
    technique: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MaterialResult:
    material_result_id: str
    experiment_id: str
    yield_representation: Optional[YieldRepresentation] = None
    material_state: Optional[MaterialState] = None
    characterizations: tuple[CharacterizationResult, ...] = ()
    provenance: dict[str, str] = field(default_factory=dict)
