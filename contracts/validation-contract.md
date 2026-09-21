# Validation Contract

## Purpose

Define the semantics of validating an FJH experiment specification before execution.

## Terminology

- **ValidationResult**: The outcome of validating an experiment specification.
- **ConstraintViolation**: A process constraint that is violated by the specification.
- **Validator**: The entity or process performing validation.
- **InvalidExperiment**: Raised when an experiment specification is structurally or semantically invalid.
- **InvalidPulseSequence**: Raised when a pulse sequence violates domain rules.

## Invariants

1. Validation is deterministic given the same input.
2. Validation does not execute anything.
3. A successful validation does not imply successful execution.
4. Validation does not grant execution authority.
5. Validation is distinct from safety interlock checks.

## Validation Stages

```text
structural → semantic → constraint
```

## ValidationResult Structure

```text
valid: bool
errors: list[str]
warnings: list[str]
validator_id: str
validated_at: datetime (UTC)
```

## Serialization

- UTF-8 JSON
- Sorted keys
- UTC timestamps

## Failure Semantics

- `InvalidExperiment`: structural or semantic failure.
- `ConstraintViolation`: constraint failure.
- `SnapshotViolation`: mutation of immutable snapshot attempted.

## Authority Boundary

- ForgePulse validates experiment semantics.
- Physical safety validation remains independent.
- Cognitia may observe but does not control validation.

## Examples

```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Pulse duration is near the recommended maximum"],
  "validator_id": "forgepulse-validator-v1",
  "validated_at": "2026-01-15T10:25:00Z"
}
```

## Non-Goals

- This contract does not define hardware safety interlocks.
- This contract does not define physical law validation.
