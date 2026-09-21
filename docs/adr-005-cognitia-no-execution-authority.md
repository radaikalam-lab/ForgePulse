# ADR-005: Cognitia Has No Execution Authority

## Status

Accepted

## Context

The authority boundary between ForgePulse and Cognitia must be explicit and non-negotiable.

## Decision

Cognitia is advisory cognitive infrastructure. It may propose but never execute pulses, bypass validation, bypass safety, mutate hardware state, declare scientific truth, or directly activate learned models.

## Consequences

- The adapter interface does not include execution methods.
- Cognitia integration is explicitly non-authoritative.
- The authority hierarchy is enforced by design, not convention.
