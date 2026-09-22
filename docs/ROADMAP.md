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
**Status: COMPLETE / FROZEN**

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
- Full test suite passes under `-W error`
- Phase 3.1 audit passed

## Phase 3.1 — Deterministic Simulator Audit & Freeze
**Status: COMPLETE**

Formal audit, reconciliation, and freeze of Phase 3.

Acceptance:
- 183 tests passed, 0 failures, 0 errors, 0 warnings
- Snapshot input boundary verified
- Snapshot immutability verified (deep)
- Deterministic seed verified
- Timestamp determinism verified
- 100x determinism verified
- Target/actual separation verified
- SIMULATED/MEASURED separation verified
- Raw/derived separation verified
- Provenance reconstructable
- Edge convergence verified
- Cognitia isolation verified
- Hardware isolation verified
- Dependency audit passed
- Contracts reconciled
- ADRs consistent
- Documentation reconciled

## Phase 4 — Measurement and Material State
**Status: COMPLETE**

Implement full measurement series, derived measurements, material state, and yield representations.

Acceptance:
- MeasurementSeries, RawMeasurement, DerivedMeasurement models with explicit source typing
- Deterministic derivation functions (power, energy, pulse statistics)
- Measurement validation with structural and semantic checks
- Characterization models (ElectricalCharacterization, ThermalCharacterization, Uncertainty)
- MeasurementPipeline and MeasurementIngestionBoundary for canonical data path
- SIMULATED/MEASURED separation preserved
- RAW/DERIVED/INTERPRETED distinctions preserved
- Provenance lineage preserved for all derived artifacts
- No hardware drivers, GPIO, DAQ, oscilloscope, or camera SDKs
- No Cognitia reasoning or autonomous scientific interpretation
- No external runtime dependencies introduced
- Existing tests remain green

## Phase 4.1 — Measurement & Material Characterization Contract Reconciliation and Freeze
**Status: COMPLETE / FROZEN**

Formal audit, reconciliation, and freeze of Phase 4.

Acceptance:
- 287 tests passed, 0 failures, 0 errors, 0 warnings
- SIMULATED/MEASURED separation verified
- RAW/DERIVED/INTERPRETED distinctions verified
- Material representation ≠ material truth verified
- Uncertainty ≠ epistemic confidence verified
- Target/actual separation verified
- Experiment spec ≠ execution verified
- Execution ≠ measurement verified
- Measurement ≠ characterization verified
- Characterization ≠ interpretation verified
- Yield basis explicit verified
- Provenance structured and immutable verified
- Cognitia isolation verified
- Hardware isolation verified
- Dependency audit passed
- Contracts reconciled
- Documentation reconciled

## Phase 5 — Cognitia Integration
Implement the adapter layer translating ForgePulse artifacts to Cognitia-compatible structures. Keep adapter optional.

## Phase 5 — Scientific Interpretation & Material Evolution
**Status: COMPLETE**

Establish a contract-first scientific interpretation layer above the frozen Phase 4 measurement and characterization system.

Acceptance:
- Evidence, Hypothesis, Interpretation, Residual, Unknown models
- CompetingInterpretation and MaterialEvolution models
- InterpretationStatus lifecycle semantics
- Explicit assumption tracking
- Contradictory evidence preservation
- SIMULATED/MEASURED boundary preserved
- Measurement uncertainty distinct from epistemic confidence
- Material representation distinct from material truth
- Provenance reconstructable through interpretation chain
- Cognitia remains optional/advisory
- No autonomous scientific conclusions
- No hardware dependencies introduced
- No external runtime dependencies introduced
- Full test suite passes under `-W error`

## Phase 6 — Scientific Experiment Workflow
**Status: COMPLETE**

Implement end-to-end experiment workflow: proposal → validation → snapshot → execution → measurement → derivation → characterization → interpretation.

Acceptance:
- ExperimentWorkflow immutable container for end-to-end state
- WorkflowStage enum for all workflow stages
- StageResult for per-stage validation diagnostics
- ScientificValidationResult for aggregate workflow validation
- Deterministic stage validation functions
- No autonomous scientific conclusions
- No hardware dependencies introduced
- No external runtime dependencies introduced
- Full test suite passes under `-W error`

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
