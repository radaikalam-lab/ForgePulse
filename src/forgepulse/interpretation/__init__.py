"""Scientific interpretation domain models for ForgePulse.

Interpretation answers: "What can be scientifically inferred from the
measured/derived/characterized state?"

Interpretation is NOT measurement. Interpretation is NOT characterization.
Interpretation is NOT material truth. Interpretation is NOT execution authority.
Interpretation is NOT Cognitia authority.

No autonomous scientific conclusions are encoded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Optional

from forgepulse.common import Quantity, _utc_now
from forgepulse.measurement.models import ProvenanceReference
from forgepulse.material import MaterialState


class InterpretationStatus(StrEnum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    UNRESOLVED = "UNRESOLVED"
    SUPERSEDED = "SUPERSEDED"


class InterpretationMethod(StrEnum):
    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    MODEL_BASED = "MODEL_BASED"
    EXPERIMENTAL_COMPARISON = "EXPERIMENTAL_COMPARISON"
    HUMAN_AUTHORED = "HUMAN_AUTHORED"
    COGNITIA_ADVISORY = "COGNITIA_ADVISORY"
    EXTERNAL_ANALYSIS = "EXTERNAL_ANALYSIS"


@dataclass(frozen=True)
class Evidence:
    """Information supporting or constraining an interpretation.

    Evidence strength, when represented, is explicitly defined.
    It is not equivalent to confidence, probability, truth, or epistemic status.
    """

    evidence_id: str
    source_reference: str
    evidence_type: str
    description: str
    relevance: str
    measurement_references: tuple[str, ...] = ()
    material_references: tuple[str, ...] = ()
    strength: Optional[str] = None
    strength_definition: Optional[str] = None
    assumptions: tuple[str, ...] = ()
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    created_at: datetime = field(default_factory=_utc_now)
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        if not self.source_reference or not self.source_reference.strip():
            raise ValueError("source_reference must be a non-empty string")
        if not self.evidence_type or not self.evidence_type.strip():
            raise ValueError("evidence_type must be a non-empty string")
        if not self.description or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        if not self.relevance or not self.relevance.strip():
            raise ValueError("relevance must be a non-empty string")
        if self.strength is not None and (self.strength_definition is None or not self.strength_definition.strip()):
            raise ValueError("strength_definition is required when strength is provided")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


@dataclass(frozen=True)
class Hypothesis:
    """Candidate scientific explanation."""

    hypothesis_id: str
    statement: str
    scope: str
    supporting_evidence: tuple[str, ...] = ()
    contradicting_evidence: tuple[str, ...] = ()
    neutral_evidence: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    status: InterpretationStatus = InterpretationStatus.PROPOSED
    residuals: tuple[str, ...] = ()
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.hypothesis_id or not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must be a non-empty string")
        if not self.statement or not self.statement.strip():
            raise ValueError("statement must be a non-empty string")
        if not self.scope or not self.scope.strip():
            raise ValueError("scope must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


@dataclass(frozen=True)
class Residual:
    """Observed information not adequately explained by the current interpretation.

    Residual is not error. Residual is not failure. Residual is not noise
    unless explicitly established.
    """

    residual_id: str
    description: str
    category: str
    related_measurement_ids: tuple[str, ...] = ()
    related_interpretation_id: Optional[str] = None
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.residual_id or not self.residual_id.strip():
            raise ValueError("residual_id must be a non-empty string")
        if not self.description or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        if not self.category or not self.category.strip():
            raise ValueError("category must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


@dataclass(frozen=True)
class Unknown:
    """Information not established by available evidence.

    Unknown is first-class. It is not represented as null, 0, false,
    or low confidence.
    """

    unknown_id: str
    description: str
    category: str
    related_measurement_ids: tuple[str, ...] = ()
    related_interpretation_id: Optional[str] = None
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.unknown_id or not self.unknown_id.strip():
            raise ValueError("unknown_id must be a non-empty string")
        if not self.description or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        if not self.category or not self.category.strip():
            raise ValueError("category must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


@dataclass(frozen=True)
class CompetingInterpretation:
    """Alternative explanation retained explicitly."""

    interpretation_id: str
    subject_reference: str
    proposition: str
    evidence_references: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    status: InterpretationStatus = InterpretationStatus.PROPOSED
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.interpretation_id or not self.interpretation_id.strip():
            raise ValueError("interpretation_id must be a non-empty string")
        if not self.subject_reference or not self.subject_reference.strip():
            raise ValueError("subject_reference must be a non-empty string")
        if not self.proposition or not self.proposition.strip():
            raise ValueError("proposition must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


@dataclass(frozen=True)
class InterpretationResult:
    """Structured scientific interpretation derived from available evidence.

    Interpretations must be reconstructable from evidence, assumptions,
    and residuals.
    """

    interpretation_id: str
    subject_reference: str
    proposition: str
    evidence_references: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    residuals: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    competing_interpretations: tuple[str, ...] = ()
    hypothesis_id: Optional[str] = None
    status: InterpretationStatus = InterpretationStatus.PROPOSED
    method: Optional[InterpretationMethod] = None
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.interpretation_id or not self.interpretation_id.strip():
            raise ValueError("interpretation_id must be a non-empty string")
        if not self.subject_reference or not self.subject_reference.strip():
            raise ValueError("subject_reference must be a non-empty string")
        if not self.proposition or not self.proposition.strip():
            raise ValueError("proposition must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


@dataclass(frozen=True)
class MaterialEvolution:
    """Candidate material state proposed from interpretation.

    Candidate material states do not silently become canonical truth.
    """

    evolution_id: str
    experiment_id: str
    candidate_material_state: MaterialState
    prior_material_state_id: Optional[str] = None
    supporting_interpretation_id: Optional[str] = None
    status: str = "CANDIDATE"
    provenance: ProvenanceReference = field(default_factory=ProvenanceReference)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.evolution_id or not self.evolution_id.strip():
            raise ValueError("evolution_id must be a non-empty string")
        if not self.experiment_id or not self.experiment_id.strip():
            raise ValueError("experiment_id must be a non-empty string")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")


class InterpretationValidationError(Exception):
    """Raised when an interpretation fails structural or semantic validation."""
