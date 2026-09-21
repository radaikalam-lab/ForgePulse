# ADR-006: Raw, Derived, and Interpreted Results Remain Distinct

## Status

Accepted

## Context

Scientific data must preserve explicit distinctions between observation, derivation, and interpretation.

## Decision

ForgePulse maintains explicit separation between `RawMeasurement`, `DerivedMeasurement`, and `InterpretedResult`. Derived measurements preserve lineage. Interpretations are never promoted to measurements or facts.

## Consequences

- Raw data is never silently replaced.
- Lineage is structured and traceable.
- Interpretations are explicitly labeled and governed.
- Simulated data is explicitly typed and distinguishable from physical measurements.
