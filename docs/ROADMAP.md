# ForgePulse Roadmap

## Phase 0 — Project Bootstrap
**Status: In Progress**

Establish repository structure, contracts, core domain models, validation, serialization, simulator boundary, test suite, and authority boundaries.

## Phase 1 — Experiment Domain Model
Expand domain models with full experiment specification, versioning, and lifecycle management.

## Phase 2 — Validation and Snapshots
Implement deterministic validation pipeline and immutable snapshot creation.

## Phase 3 — Deterministic FJH Simulator
Implement a minimum deterministic simulator that produces synthetic observations clearly marked as simulated.

## Phase 4 — Measurement and Material State
Implement full measurement series, derived measurements, material state, and yield representations.

## Phase 5 — Cognitia Integration
Implement the adapter layer translating ForgePulse artifacts to Cognitia-compatible structures. Keep adapter optional.

## Phase 6 — Scientific Experiment Workflow
Implement end-to-end experiment workflow: proposal → validation → snapshot → execution → measurement → derivation → characterization → interpretation.

## Phase 7 — Hardware Abstraction
Define interfaces for `FJHController`, `MeasurementSource`, `SafetyInterlock`, and `Instrument` without implementing real drivers.

## Phase 8 — Laboratory Integration
Future phase for physical hardware integration, governed by explicit safety and authority reviews.

## Out of Scope for Bootstrap

- Real FJH hardware control
- Power supply, capacitor-bank, or switching control
- GPIO, PLC, DAQ drivers
- Emergency stop or safety interlocks
- Real-time control loops
- Closed-loop optimization
- Autonomous experiment selection
- LLM reasoning or TinyML
- Material-property prediction
- Autonomous scientific discovery
