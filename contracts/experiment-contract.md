# Experiment Contract

## Purpose

Define the immutable semantics of an FJH experiment specification from initial research intent through validated snapshot.

## Terminology

- **Experiment**: A complete, versioned scientific procedure definition.
- **ExperimentVersion**: An immutable snapshot of an experiment at a specific point in its lifecycle.
- **ExperimentObjective**: The scientific goal of the experiment.
- **HypothesisReference**: A reference to a hypothesis under evaluation.
- **Feedstock**: The starting material for the experiment.
- **Additive**: A material added to the feedstock.
- **Atmosphere**: The gas environment within the chamber.
- **Chamber**: The reaction vessel configuration.
- **Pulse**: A single electrical pulse specification.
- **PulseSequence**: An ordered set of pulses.
- **ProcessConstraint**: Validity rules for the experiment specification.
- **MeasurementRequirement**: What must be measured during execution.
- **CharacterizationRequirement**: What post-process characterization is required.
- **ValidatedExperimentSnapshot**: An immutable validated specification ready for execution.

## Invariants

1. Every experiment has a unique `experiment_id` and `experiment_version`.
2. Once an experiment reaches execution, its specification is immutable.
3. A `ValidatedExperimentSnapshot` is immutable after creation.
4. Target values and actual values are never merged or overwritten.
5. Process constraints are distinct from physical safety interlocks.

## Identity

```text
experiment_id: str
experiment_version: str
schema_version: str
created_at: datetime (UTC, ISO 8601)
```

## Versioning

- `experiment_id` identifies the experiment across versions.
- `experiment_version` identifies a specific iteration.
- `schema_version` identifies the contract version of the specification structure.
- Versions are compared lexicographically by default unless a richer versioning scheme is defined.

## Serialization

- UTF-8 JSON
- Sorted object keys
- Explicit units on all physical quantities
- UTC timestamps in ISO 8601 format
- No NaN or Infinity values
- Stable enum representation

## Validation

- Structural validation: required fields present, types correct.
- Semantic validation: values within scientifically or operationally meaningful ranges.
- Constraint validation: all `ProcessConstraint` instances satisfied.
- Validation is deterministic given the same input.
- Validation does not execute anything.

## Failure Semantics

- `InvalidExperiment`: specification structure or semantics are invalid.
- `ConstraintViolation`: a `ProcessConstraint` is violated.
- `SnapshotViolation`: an attempt to mutate an immutable snapshot.

## Authority Boundary

- ForgePulse owns experiment semantics.
- Validation does not imply execution authority.
- Execution does not imply measurement authority.
- Cognitia may propose; ForgePulse validates; the controller executes.

## Examples

```json
{
  "experiment_id": "exp-001",
  "experiment_version": "1.0.0",
  "schema_version": "1.0.0",
  "created_at": "2026-01-15T10:30:00Z",
  "objective": "Produce graphene from carbon black via FJH",
  "feedstock": {
    "material": "carbon black",
    "mass": 0.5,
    "unit": "g"
  },
  "pulse_sequence": {
    "pulses": [
      {
        "target_voltage": 120.0,
        "unit": "V",
        "duration": 0.05,
        "duration_unit": "s"
      }
    ],
    "inter_pulse_interval": 1.0,
    "interval_unit": "s"
  },
  "process_constraints": {
    "maximum_target_voltage": 150.0,
    "maximum_pulse_duration": 0.1
  }
}
```

## Non-Goals

- This contract does not define hardware control protocols.
- This contract does not define safety interlock semantics.
- This contract does not define Cognitia-specific cognitive models.
