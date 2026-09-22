# ADR-003: Experiment Specifications Become Immutable at Execution Snapshot

## Status

Accepted

## Context

An experiment specification must not silently change between validation and execution.

## Decision

Every execution references a `ValidatedExperimentSnapshot`. Once an experiment reaches execution, its validated specification is immutable. The snapshot includes a `checksum` field.

Current implementation:
- The checksum is computed as the first 16 hex characters of SHA-256 over the canonical JSON representation of the frozen experiment specification.
- Canonical JSON uses UTF-8 encoding, sorted object keys, compact separators, explicit units, UTC timestamps in ISO 8601 format with `Z` suffix, no NaN or Infinity values, and stable enum representation.
- The checksum is deterministic: identical semantic content produces identical checksums, and meaningful changes produce different checksums.

## Consequences

- Execution cannot reference a mutable experiment definition.
- Version identity (`experiment_id`, `experiment_version`, `schema_version`) is explicit and immutable.
- Mutation of a snapshot raises `FrozenInstanceError` (dataclass frozen=True).
