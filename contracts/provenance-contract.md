# Provenance Contract

## Purpose

Define structured lineage for every derived or interpreted artifact in ForgePulse.

## Terminology

- **Provenance**: The lineage of an artifact from its source data through all transformations.
- **ProvenanceRecord**: A structured record of lineage.
- **LineageReference**: A reference to another artifact by its stable identifier.

## Invariants

1. Every derived artifact preserves lineage to its source data.
2. Provenance is structured, not free-form text.
3. Provenance records are immutable once created.
4. Raw data provenance is established at acquisition time.

## Lineage Chain

```text
Experiment
   ↓
Execution
   ↓
Raw Measurement
   ↓
Derived Measurement
   ↓
Material Result
   ↓
Interpretation
```

## ProvenanceRecord Structure

```text
artifact_id: str
artifact_type: str
source_ids: list[LineageReference]
transformation: str | null
created_at: datetime (UTC)
created_by: str
```

## Serialization

- UTF-8 JSON
- Sorted keys
- UTC timestamps
- Deterministic ordering of `source_ids`

## Failure Semantics

- `ProvenanceError`: required lineage is missing or circular.

## Authority Boundary

- Provenance is maintained by ForgePulse.
- Cognitia may receive provenance records but does not own them.

## Examples

```json
{
  "artifact_id": "derived-001",
  "artifact_type": "derived_measurement",
  "source_ids": [
    { "artifact_id": "meas-001", "artifact_type": "raw_measurement" }
  ],
  "transformation": "average",
  "created_at": "2026-01-15T10:30:10Z",
  "created_by": "forgepulse"
}
```

## Non-Goals

- This contract does not define Cognitia's provenance model.
- This contract does not define W3C PROV-O compliance.
