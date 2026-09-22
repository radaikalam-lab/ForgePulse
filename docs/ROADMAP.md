# ForgePulse Roadmap

## Phase 0 — Project Bootstrap
**Status: COMPLETE**

Establish repository structure, contracts, core domain models, validation, serialization, simulator boundary, test suite, and authority boundaries.

Acceptance:
- 53 tests passed
- 0 failures
- 0 errors
- 0 warnings
- No runtime external dependencies
- No hardware dependencies
- No network dependencies
- No AI/ML dependencies

## Phase 1 — Experiment Domain & Edge Integration
**Status: COMPLETE**

Implement experiment lifecycle, edge integration boundary, synthetic edge source, and measurement translator.

Acceptance:
- Experiment lifecycle with valid/invalid transitions
- EdgeIntegrationBoundary with state-dependent access controls
- SyntheticEdgeSource for deterministic synthetic data
- MeasurementTranslator for normalizing raw edge data
- Comprehensive test coverage

## Phase 2 — Validation and Snapshots
**Status: COMPLETE**

Implement deterministic validation pipeline and immutable snapshot creation.

Acceptance:
- Deterministic experiment validation
- Validation result model with structured diagnostics
- Immutable validated experiment snapshots
- Snapshot deep immutability verified
- Snapshot independent of source experiment object
- Deterministic snapshot serialization
- Snapshot checksum semantics documented
- Execution references immutable snapshot
- Lifecycle integration correct
- Edge Integration cannot bypass validation
- Cognitia not required for validation or snapshot creation
- No physical safety claim made by validation
- No scientific success claim made by validation
- Simulator remains outside Phase 2 implementation
- No hardware dependencies introduced
- No external runtime dependencies introduced
- Existing Phase 1 tests remain green

## Phase 3 — Deterministic FJH Simulator
**Status: IN PROGRESS**

Implement a minimum deterministic simulator that produces synthetic observations clearly marked as simulated.

Acceptance:
- Simulator accepts validated immutable experiment snapshot only
- All outputs explicitly marked as simulated (SourceType.SIMULATED)
- Deterministic seed derived from snapshot identity
- SimulatorResult includes measurements, observations, metadata, provenance
- to_raw_measurements enables edge boundary integration
- Empty pulse sequence rejected
- No physical safety or scientific truth claims
- Baseline model assumptions documented
- No hardware dependencies introduced
- No external runtime dependencies introduced

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
