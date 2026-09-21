# ADR-002: Simulation Precedes Hardware

## Status

Accepted

## Context

The project must be usable and testable without physical FJH hardware.

## Decision

All core experiment semantics must be implementable and testable via a deterministic simulator. Physical hardware integration is deferred to a future phase and adapter layer. Domain models must not depend on hardware-specific libraries.

## Consequences

- Domain models are hardware-agnostic.
- The simulator produces synthetic observations explicitly marked as simulated.
- Hardware integration occurs through interfaces, not core domain changes.
- No GPIO, DAQ, PLC, or vendor SDK dependencies during bootstrap.
