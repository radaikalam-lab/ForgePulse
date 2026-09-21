# ADR-003: Experiment Specifications Become Immutable at Execution Snapshot

## Status

Accepted

## Context

An experiment specification must not silently change between validation and execution.

## Decision

Every execution references a `ValidatedExperimentSnapshot`. Once an experiment reaches execution, its validated specification is immutable. The snapshot contains a deterministic checksum.

## Consequences

- Execution cannot reference a mutable experiment definition.
- Version identity (`experiment_id`, `experiment_version`, `schema_version`) is explicit and immutable.
- Mutation of a snapshot raises `SnapshotViolation`.
