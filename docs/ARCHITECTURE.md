# ForgePulse Architecture

## Overview

ForgePulse is an independent Flash Joule Heating (FJH) experimental platform. It provides domain authority for FJH experiment semantics while remaining operationally independent from external cognitive infrastructure.

## System Layers

```text
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
           Simulator       Edge Boundary     Hardware
```

## Layer Responsibilities

### Domain Layer
Owns FJH experiment semantics: experiments, pulse sequences, feedstock, atmosphere, process constraints, material states, and provenance. No hardware, network, or database dependencies.

### Validation Layer
Deterministically validates experiment specifications. Does not execute experiments. Does not grant execution authority. Does not claim physical safety, scientific validity, experimental success, material quality, causal validity, or epistemic acceptance.

### Snapshot Layer
Creates immutable validated experiment snapshots. Snapshots are deeply immutable and independent of the source experiment object. Snapshots use deterministic serialization and SHA-256 checksums.

### Execution Layer
Represents execution state and target/actual process parameters. Execution authority belongs to the FJH controller, not ForgePulse core. Every execution references an immutable `ValidatedExperimentSnapshot`.

### Measurement Layer
Represents raw, derived, and interpreted measurements. Preserves lineage and explicit source typing.

### Material Layer
Represents material results and states. Does not invent unmeasured properties.

### Provenance Layer
Maintains structured lineage for all derived artifacts.

### Edge Integration Boundary
Manages the authority boundary between ForgePulse domain and external systems (including optional Cognitia integration). Enforces state-dependent access controls. Does not execute hardware commands.

### Interpretation Layer
Structured scientific interpretation above characterization. Does not claim scientific truth. Does not grant execution authority. Assumptions are explicit. Residuals and unknowns are first-class.

### Cognitia Adapter Layer
Optional translation boundary between ForgePulse and Cognitia. Never executes, never bypasses safety, never claims scientific truth.

### Simulator Layer
Produces synthetic observations explicitly marked as simulated. Cannot masquerade as hardware.

## Authority Flow

```text
Scientific/domain authority
        ForgePulse
            │
            ▼
    Edge Integration Boundary
            │
            ▼
    External Systems (optional)
            │
            ▼
Execution authority
        FJH Controller
            │
            ▼
Physical safety authority
     Safety / Interlocks
            │
            ▼
       Hardware
```

Cognitia is advisory only.

## Data Flow

```text
Research Intent
    → Experiment Proposal
    → Experiment Specification
    → Validation
    → Validated Snapshot
    → Queued Execution
    → Running Execution
    → Completed/Failed/Aborted
    → Raw Measurements
    → Derived Measurements
    → Characterization
    → Interpretation
    → Material Evolution Candidate
```

## Immutability Semantics

Experiment specifications and validated snapshots are immutable once committed. Execution lifecycle state may transition according to the experiment contract. Historical execution states must not be silently rewritten.

```text
Experiment Specification
        ↓
Immutable Version

Validated Experiment Snapshot
        ↓
Immutable

Experiment
         ↓
Lifecycle State
RESEARCH_INTENT → PROPOSED → SPECIFIED → VALIDATED → SNAPSHOTTED → QUEUED → RUNNING → COMPLETED/FAILED/ABORTED → MEASURED → DERIVED → CHARACTERIZED → INTERPRETED

Interpretation Status
PROPOSED → UNDER_REVIEW → SUPPORTED/REFUTED/UNRESOLVED/SUPERSEDED

Experiment History
        ↓
Auditable
```
