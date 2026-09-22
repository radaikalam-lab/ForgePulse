"""Base measurement domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional, Union

from forgepulse.common import Quantity


class SourceType(StrEnum):
    RAW = "raw"
    DERIVED = "derived"
    INTERPRETED = "interpreted"
    SIMULATED = "simulated"
    MEASURED = "measured"


@dataclass(frozen=True)
class ProvenanceReference:
    execution_id: Optional[str] = None
    measurement_id: Optional[str] = None
    artifact_id: Optional[str] = None


@dataclass(frozen=True)
class MeasurementSeries:
    measurement_id: str
    quantity: str
    values: list[float]
    unit: str
    start_time: datetime
    sampling_rate: Optional[Quantity] = None
    timestamps: Optional[list[datetime]] = None
    instrument_reference: Optional[str] = None
    source_type: SourceType = SourceType.RAW
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)

    def __post_init__(self) -> None:
        pass


@dataclass(frozen=True)
class RawMeasurement:
    measurement_id: str
    quantity: str
    values: list[float]
    unit: str
    sampling_rate: Optional[Quantity] = None
    start_time: Optional[datetime] = None
    instrument_reference: Optional[str] = None
    source_type: SourceType = SourceType.RAW
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)

    def __post_init__(self) -> None:
        pass


@dataclass(frozen=True)
class DerivedMeasurement:
    measurement_id: str
    quantity: str
    value: Quantity
    source_ids: tuple[str, ...] = ()
    transformation: Optional[str] = None
    source_type: SourceType = SourceType.DERIVED
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)


@dataclass(frozen=True)
class InterpretedResult:
    result_id: str
    interpretation: str
    source_ids: tuple[str, ...] = ()
    confidence: Optional[float] = None
    source_type: SourceType = SourceType.INTERPRETED
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class ElectricalObservation:
    measurement_id: str
    voltage: Optional[Quantity] = None
    current: Optional[Quantity] = None
    resistance: Optional[Quantity] = None
    source_type: SourceType = SourceType.RAW
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)


@dataclass(frozen=True)
class ThermalObservation:
    measurement_id: str
    temperature: Optional[Quantity] = None
    heat_flux: Optional[Quantity] = None
    source_type: SourceType = SourceType.RAW
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)


@dataclass(frozen=True)
class PulseObservation:
    measurement_id: str
    electrical: Optional[ElectricalObservation] = None
    thermal: Optional[ThermalObservation] = None
    source_type: SourceType = SourceType.RAW
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
