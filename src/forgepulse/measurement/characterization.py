"""Material and process characterization for ForgePulse.

This module provides structured characterization results derived from
measurements. Characterization is distinct from raw measurement and
from scientific interpretation.

Characterization methods are explicit metadata. The presence of a method
name does not mean the method was actually performed unless the
characterization result explicitly indicates so.

Characterization does not:
- Claim scientific truth
- Automatically interpret results
- Invent unsupported material properties
- Control instruments
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional

from forgepulse.measurement.models import ProvenanceReference


class CharacterizationMethod(StrEnum):
    """Explicit characterization methods.

    These are metadata identifiers for characterization techniques.
    The presence of a method name does not imply the method was performed.
    """

    ELECTRICAL = "electrical_characterization"
    THERMAL = "thermal_characterization"
    RAMAN = "Raman"
    XRD = "XRD"
    SEM = "SEM"
    TEM = "TEM"
    AFM = "AFM"
    XPS = "XPS"
    TGA = "TGA"
    DSC = "DSC"
    OPTICAL = "optical_characterization"
    MECHANICAL = "mechanical_characterization"


@dataclass(frozen=True)
class Uncertainty:
    """Measurement uncertainty representation.

    Uncertainty is distinct from epistemic confidence or model confidence.
    Only explicitly defined uncertainty semantics are used.
    """

    standard_uncertainty: Optional[Quantity] = None
    expanded_uncertainty: Optional[Quantity] = None
    confidence_level: Optional[float] = None
    coverage_factor: Optional[float] = None

    def __post_init__(self) -> None:
        if self.confidence_level is not None and not 0.0 <= self.confidence_level <= 1.0:
            raise ValueError("confidence_level must be between 0.0 and 1.0")


@dataclass(frozen=True)
class ElectricalCharacterization:
    """Electrical characterization result derived from electrical measurements.

    All properties are optional. Unknown values remain None.
    """

    peak_voltage_v: Optional[Quantity] = None
    peak_current_a: Optional[Quantity] = None
    average_voltage_v: Optional[Quantity] = None
    average_current_a: Optional[Quantity] = None
    average_power_w: Optional[Quantity] = None
    pulse_energy_j: Optional[Quantity] = None
    resistance_ohm: Optional[Quantity] = None
    uncertainty: Optional[Uncertainty] = None
    provenance: Optional[ProvenanceReference] = None

    def __post_init__(self) -> None:
        if self.provenance is None:
            object.__setattr__(self, "provenance", ProvenanceReference())


@dataclass(frozen=True)
class ThermalCharacterization:
    """Thermal characterization result derived from thermal measurements.

    All properties are optional. Unknown values remain None.
    """

    peak_temperature_k: Optional[Quantity] = None
    temperature_rise_k: Optional[Quantity] = None
    heating_rate_k_s: Optional[Quantity] = None
    cooling_rate_k_s: Optional[Quantity] = None
    thermal_exposure_duration_s: Optional[float] = None
    uncertainty: Optional[Uncertainty] = None
    provenance: Optional[ProvenanceReference] = None

    def __post_init__(self) -> None:
        if self.provenance is None:
            object.__setattr__(self, "provenance", ProvenanceReference())


@dataclass(frozen=True)
class CharacterizationResult:
    """Structured characterization result.

    Distinct from DerivedMeasurement:
    - DerivedMeasurement = computed measurement quantity
    - CharacterizationResult = structured characterization of material/process state

    The result_id uniquely identifies this characterization result.
    source_measurement_ids traces back to the measurements used.
    """

    result_id: str
    technique: str
    summary: str
    property: Optional[str] = None
    value: Optional[Quantity] = None
    unit: Optional[str] = None
    method: Optional[str] = None
    source_measurement_ids: tuple[str, ...] = ()
    uncertainty: Optional[Uncertainty] = None
    data: dict[str, Any] = field(default_factory=dict)
    provenance: Optional[ProvenanceReference] = None

    def __post_init__(self) -> None:
        if not self.result_id or not self.result_id.strip():
            raise ValueError("result_id must be a non-empty string")
        if not self.technique or not self.technique.strip():
            raise ValueError("technique must be a non-empty string")
        if self.provenance is None:
            object.__setattr__(self, "provenance", ProvenanceReference())
