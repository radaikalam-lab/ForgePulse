# ADR-004: Process Constraints Are Separate from Physical Safety

## Status

Accepted

## Context

Experiment validity constraints and physical safety interlocks serve different purposes and have different authority.

## Decision

Process constraints describe experiment validity. Physical safety interlocks remain independent systems. ForgePulse never conflates the two.

## Consequences

- Process constraint validation does not replace safety checks.
- Safety systems may veto execution independently of ForgePulse validation.
- Emergency stop, thermal protection, and electrical protection remain outside ForgePulse domain.
