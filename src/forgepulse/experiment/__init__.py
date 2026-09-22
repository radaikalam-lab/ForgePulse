"""FJH experiment domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional, Tuple

from forgepulse.common import InvalidTransition, Quantity


@dataclass(frozen=True)
class ValidatedExperimentSnapshot:
    snapshot_id: str
    experiment_id: str
    experiment_version: str
    schema_version: str
    specification: ExperimentSpecification
    validation_result: "ValidationResult"
    validator_id: str
    created_at: datetime
    checksum: str

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


class ExperimentStatus(StrEnum):
    RESEARCH_INTENT = "RESEARCH_INTENT"
    PROPOSED = "PROPOSED"
    SPECIFIED = "SPECIFIED"
    VALIDATED = "VALIDATED"
    SNAPSHOTTED = "SNAPSHOTTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    CHARACTERIZED = "CHARACTERIZED"
    INTERPRETED = "INTERPRETED"


@dataclass(frozen=True)
class LifecycleEvent:
    from_status: ExperimentStatus
    to_status: ExperimentStatus
    occurred_at: datetime
    note: Optional[str] = None

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware UTC")


_VALID_TRANSITIONS = {
    ExperimentStatus.RESEARCH_INTENT: (ExperimentStatus.PROPOSED,),
    ExperimentStatus.PROPOSED: (ExperimentStatus.SPECIFIED,),
    ExperimentStatus.SPECIFIED: (ExperimentStatus.VALIDATED,),
    ExperimentStatus.VALIDATED: (ExperimentStatus.SNAPSHOTTED,),
    ExperimentStatus.SNAPSHOTTED: (ExperimentStatus.QUEUED,),
    ExperimentStatus.QUEUED: (ExperimentStatus.RUNNING,),
    ExperimentStatus.RUNNING: (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED, ExperimentStatus.ABORTED),
    ExperimentStatus.COMPLETED: (ExperimentStatus.MEASURED,),
    ExperimentStatus.FAILED: (ExperimentStatus.MEASURED,),
    ExperimentStatus.ABORTED: (),
    ExperimentStatus.MEASURED: (ExperimentStatus.DERIVED,),
    ExperimentStatus.DERIVED: (ExperimentStatus.CHARACTERIZED,),
    ExperimentStatus.CHARACTERIZED: (ExperimentStatus.INTERPRETED,),
    ExperimentStatus.INTERPRETED: (),
}


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    specification: ExperimentSpecification
    status: ExperimentStatus = ExperimentStatus.RESEARCH_INTENT
    history: tuple[LifecycleEvent, ...] = ()

    def transition(self, new_status: ExperimentStatus, note: Optional[str] = None) -> Experiment:
        allowed = _VALID_TRANSITIONS.get(self.status, ())
        if new_status not in allowed:
            raise InvalidTransition(
                f"Cannot transition from {self.status} to {new_status}. "
                f"Allowed: {allowed}"
            )
        event = LifecycleEvent(
            from_status=self.status,
            to_status=new_status,
            occurred_at=datetime.now(timezone.utc),
            note=note,
        )
        return Experiment(
            experiment_id=self.experiment_id,
            specification=self.specification,
            status=new_status,
            history=self.history + (event,),
        )


@dataclass(frozen=True)
class ExperimentObjective:
    description: str
    hypothesis_reference: Optional[str] = None


@dataclass(frozen=True)
class Additive:
    material: str
    mass: Quantity
    role: Optional[str] = None


@dataclass(frozen=True)
class Feedstock:
    material: str
    mass: Quantity
    additives: Tuple[Additive, ...] = ()


@dataclass(frozen=True)
class Atmosphere:
    gas: str
    pressure: Optional[Quantity] = None
    flow_rate: Optional[Quantity] = None


@dataclass(frozen=True)
class Chamber:
    geometry: str
    atmosphere: Atmosphere
    electrodes: Optional[str] = None


@dataclass(frozen=True)
class Pulse:
    target_voltage: Quantity
    duration: Quantity
    target_current: Optional[Quantity] = None


@dataclass(frozen=True)
class PulseSequence:
    pulses: Tuple[Pulse, ...]
    inter_pulse_interval: Quantity
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessConstraint:
    maximum_target_voltage: Optional[Quantity] = None
    maximum_target_current: Optional[Quantity] = None
    maximum_pulse_duration: Optional[Quantity] = None
    maximum_sequence_duration: Optional[Quantity] = None
    required_atmosphere: Optional[str] = None
    required_chamber_state: Optional[str] = None
    required_measurements: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MeasurementRequirement:
    quantity: str
    unit: str
    sampling_rate: Optional[Quantity] = None


@dataclass(frozen=True)
class CharacterizationRequirement:
    technique: str
    target_properties: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ExperimentSpecification:
    experiment_id: str
    experiment_version: str
    schema_version: str
    created_at: datetime
    objective: ExperimentObjective
    feedstock: Feedstock
    chamber: Chamber
    pulse_sequence: PulseSequence
    process_constraints: ProcessConstraint
    measurement_requirements: Tuple[MeasurementRequirement, ...] = ()
    characterization_requirements: Tuple[CharacterizationRequirement, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")
