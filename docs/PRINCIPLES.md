# ForgePulse Principles

## Principle 1 — Domain Authority

ForgePulse is authoritative for FJH experiment semantics.

## Principle 2 — Cognitive Separation

Cognitia is an external cognitive subsystem, not part of the ForgePulse domain model.

## Principle 3 — Simulation First

All core experiment semantics must be testable without physical hardware.

## Principle 4 — Hardware Independence

Domain models must not depend on GPIO, DAQ, PLC, serial protocols, vendor SDKs, or specific controllers.

## Principle 5 — Safety Separation

Process constraints are not physical safety interlocks.

## Principle 6 — Requested ≠ Validated ≠ Executed ≠ Measured ≠ Derived ≠ Interpreted

Never collapse these stages.

## Principle 7 — Raw Data Preservation

Raw observations must never be silently replaced by derived or interpreted values.

## Principle 8 — Determinism

Validation and domain transformations must be deterministic wherever the contract permits.

## Principle 9 — Provenance

Every derived or interpreted artifact must preserve lineage to its source data.

## Principle 10 — Immutable Experiment Identity

An experiment version must be immutable once execution begins.

## Principle 11 — No Hidden Scientific Assumptions

The system must not invent material properties, reaction mechanisms, causal relationships, or physical laws.

## Principle 12 — Controller Independence

ForgePulse defines WHAT should be executed. A controller determines HOW it is physically executed.

## Principle 13 — Cognitia Is Optional

ForgePulse must remain operationally meaningful when Cognitia is disabled or unavailable.
