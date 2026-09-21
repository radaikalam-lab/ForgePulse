# ADR-001: ForgePulse is Independent from Cognitia

## Status

Accepted

## Context

ForgePulse must provide FJH experiment semantics as a standalone platform. Cognitia is an external cognitive infrastructure dependency.

## Decision

ForgePulse and Cognitia are independent systems. ForgePulse owns FJH domain semantics. Cognitia owns cognitive/epistemic infrastructure. Integration occurs only through a clean, optional adapter boundary.

## Consequences

- ForgePulse can operate without Cognitia.
- Cognitia can operate without ForgePulse.
- No Cognitia source code is copied into ForgePulse.
- No Cognitia vocabulary leaks into core domain modules.
- The integration layer must remain optional and non-authoritative.
