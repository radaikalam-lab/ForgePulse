# ADR-003: Experiment Specifications Become Immutable at Execution Snapshot

## Status

Accepted

## Context

An experiment specification must not silently change between validation and execution.

## Decision

Every execution references a `ValidatedExperimentSnapshot`. Once an experiment reaches execution, its validated specification is immutable. The snapshot includes a `checksum` field.

Current implementation:
- The checksum is stored as an explicit string field.
- The canonical checksum algorithm and canonicalization rules are not yet frozen.

Future canonical contract:
- The checksum algorithm and canonicalization rules will be formally frozen as part of the Phase 2 Validation and Snapshot contract.
- Until then, checksum values are application-defined and must be treated as opaque strings.

## Consequences

- Execution cannot reference a mutable experiment definition.
- Version identity (`experiment_id`, `experiment_version`, `schema_version`) is explicit and immutable.
- Mutation of a snapshot raises `SnapshotViolation`.
