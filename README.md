# ForgePulse

**ForgePulse** is an independent Flash Joule Heating (FJH) experimental platform.

It provides a machine-independent, scientifically disciplined software architecture for defining, validating, simulating, executing, and recording FJH experiments with complete provenance.

## What ForgePulse is

- Domain authority for FJH experiment semantics
- Experiment lifecycle management
- Pulse sequence representation
- Process constraint validation
- Deterministic simulation
- Measurement and material state representation
- Complete experimental provenance
- Optional cognitive integration via **Cognitia**

## What ForgePulse is not

ForgePulse is **not** Cognitia.

- Cognitia is an external cognitive infrastructure dependency.
- ForgePulse does not provide general-purpose cognitive reasoning, generic memory, recall, attention, or plasticity.
- ForgePulse does not control hardware, safety interlocks, or emergency stop systems.

## Relationship with Cognitia

```
                         Cognitia
                    Cognitive Substrate
                            │
                       FJH Adapter
                            │
                            ▼
                     ┌──────────────┐
                     │  ForgePulse  │
                     │ FJH Platform │
                     └───────┬──────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
         Simulator       Instruments       Hardware
```

ForgePulse must remain usable when Cognitia is unavailable. Cognitia must remain usable without ForgePulse.

## Simulator-First Approach

All core experiment semantics are testable without physical hardware. The simulator produces synthetic observations explicitly marked as simulated. Physical measurements are never replaced or confused with simulated data.

## Hardware Independence

Domain models do not depend on GPIO, DAQ, PLC, serial protocols, vendor SDKs, or specific controllers. Hardware integration is deferred to a future adapter layer.

## Getting Started

```bash
python -m pip install -e ".[dev]"
python -m pytest -q -W error
```

## License

MIT
