# Interpretation Contract

## Purpose

Define the semantics of scientific interpretation above the Phase 4 measurement and characterization system.

Interpretation answers: "What can be scientifically inferred from the measured/derived/characterized state?"

Interpretation is NOT measurement. Interpretation is NOT characterization. Interpretation is NOT material truth. Interpretation is NOT execution authority. Interpretation is NOT Cognitia authority.

## Terminology

- **Evidence**: Information supporting or constraining an interpretation.
- **Hypothesis**: Candidate scientific explanation.
- **Interpretation**: Explicit inference derived from available evidence.
- **Residual**: Observed information not adequately explained by the current interpretation.
- **Unknown**: Information not established by available evidence.
- **CompetingInterpretation**: Alternative explanation retained explicitly.
- **InterpretationStatus**: Lifecycle state of an interpretation.
- **MaterialEvolution**: Candidate material state proposed from interpretation.

## Invariants

1. Evidence, hypotheses, and interpretations are immutable once created.
2. No layer silently replaces another: measurement ≠ characterization ≠ interpretation ≠ material truth.
3. Unknown remains unknown; no values are manufactured for unestablished information.
4. Residuals are preserved, not suppressed.
5. Competing interpretations remain possible when evidence does not distinguish them.
6. Assumptions are explicit and provenance-linked.
7. Contradictory evidence remains inspectable.
8. SIMULATED and MEASURED provenance is preserved through all stages.
9. Measurement uncertainty remains distinct from epistemic confidence.
10. Material representation remains distinct from material truth.
11. Provenance is reconstructable from interpretation to raw measurement.
12. No autonomous scientific conclusions are encoded.

## Semantic Layers

```text
RAW MEASUREMENT
    = source measurement representation

DERIVED MEASUREMENT
    = deterministic mathematical transformation

CHARACTERIZATION
    = structured characterization of measured/derived state

MATERIAL STATE
    = structured representation of material state

EVIDENCE
    = information supporting or constraining an interpretation

HYPOTHESIS
    = candidate scientific explanation

INTERPRETATION
    = explicit inference derived from available evidence

RESIDUAL
    = observed information not adequately explained

UNKNOWN
    = information not established by available evidence

COMPETING INTERPRETATION
    = alternative explanation retained explicitly
```

No layer may silently replace another.

## Evidence

```text
evidence_id: str
source_reference: str
evidence_type: str
description: str
measurement_references: tuple[str, ...] = ()
material_references: tuple[str, ...] = ()
relevance: str
strength: Optional[str]
strength_definition: Optional[str]
assumptions: tuple[str, ...] = ()
provenance: ProvenanceReference
created_at: datetime (UTC)
schema_version: str
```

Evidence strength, when represented, is explicitly defined. It is not equivalent to confidence, probability, truth, or epistemic status.

## Hypothesis

```text
hypothesis_id: str
statement: str
scope: str
supporting_evidence: tuple[str, ...] = ()
contradicting_evidence: tuple[str, ...] = ()
neutral_evidence: tuple[str, ...] = ()
assumptions: tuple[str, ...] = ()
status: InterpretationStatus
residuals: tuple[str, ...] = ()
provenance: ProvenanceReference
version: str
created_at: datetime (UTC)
```

## Interpretation

```text
interpretation_id: str
subject_reference: str
hypothesis_id: Optional[str]
proposition: str
evidence_references: tuple[str, ...] = ()
assumptions: tuple[str, ...] = ()
residuals: tuple[str, ...] = ()
unknowns: tuple[str, ...] = ()
competing_interpretations: tuple[str, ...] = ()
status: InterpretationStatus
method: Optional[InterpretationMethod]
provenance: ProvenanceReference
version: str
created_at: datetime (UTC)
```

Interpretations must be reconstructable from evidence, assumptions, and residuals.

## Interpretation Status

```text
PROPOSED
UNDER_REVIEW
SUPPORTED
REFUTED
UNRESOLVED
SUPERSEDED
```

Status transitions must have identifiable evidence and provenance. No automatic status promotion.

## Residual

```text
residual_id: str
description: str
category: str
related_measurement_ids: tuple[str, ...] = ()
related_interpretation_id: Optional[str]
provenance: ProvenanceReference
created_at: datetime (UTC)
```

Residual is not error, not failure, not noise unless explicitly established.

## Unknown

```text
unknown_id: str
description: str
category: str
related_measurement_ids: tuple[str, ...] = ()
related_interpretation_id: Optional[str]
provenance: ProvenanceReference
created_at: datetime (UTC)
```

Unknown is first-class. It is not represented as null, 0, false, or low confidence.

## Competing Interpretation

```text
interpretation_id: str
subject_reference: str
proposition: str
evidence_references: tuple[str, ...] = ()
assumptions: tuple[str, ...] = ()
status: InterpretationStatus
provenance: ProvenanceReference
created_at: datetime (UTC)
```

## Material Evolution

```text
evolution_id: str
experiment_id: str
prior_material_state_id: Optional[str]
candidate_material_state: MaterialState
supporting_interpretation_id: Optional[str]
status: str
provenance: ProvenanceReference
created_at: datetime (UTC)
```

Candidate material states do not silently become canonical truth.

## Provenance Chain

```text
Experiment
    ↓
Validated Snapshot
    ↓
Execution / Simulation
    ↓
Raw Measurement
    ↓
Derived Measurement
    ↓
Characterization
    ↓
Material State
    ↓
Evidence
    ↓
Hypothesis
    ↓
Interpretation
```

Every interpretation is traceable to evidence. Every evidence item identifies its source.

## Interpretation Methods

```text
DETERMINISTIC_RULE
MODEL_BASED
EXPERIMENTAL_COMPARISON
HUMAN_AUTHORED
COGNITIA_ADVISORY
EXTERNAL_ANALYSIS
```

Only methods actually supported by the repository are implemented. Deterministic rules do not claim the authority of experimentally validated models.

## Failure Semantics

- `InterpretationValidationError`: interpretation structure or contract compliance fails.
- `ProvenanceError`: lineage is missing or circular.

## Authority Boundary

- ForgePulse owns interpretation semantics.
- Cognitia may provide advisory reasoning through the adapter boundary.
- Interpretation does not grant execution authority.
- Interpretation does not claim scientific truth.

## Serialization

- UTF-8 JSON
- Sorted keys
- UTC timestamps in ISO 8601 format
- Explicit units where applicable
- No NaN or Infinity

## Non-Goals

- This contract does not implement autonomous scientific discovery.
- This contract does not define universal scientific reasoning engines.
- This contract does not require Cognitia for ForgePulse to function.
- This contract does not define hardware control or safety interlocks.
