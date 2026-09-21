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
         Simulator       Instruments       Hardware
```

## Layer Responsibilities

### Domain Layer
Owns FJH experiment semantics: experiments, pulse sequences, feedstock, atmosphere, process constraints, material states, and provenance. No hardware, network, or database dependencies.

### Validation Layer
Validates experiment specifications deterministically. Does not execute experiments. Does not grant execution authority.

### Execution Layer
Represents execution state and target/actual process parameters. Execution authority belongs to the FJH controller, not ForgePulse core.

### Measurement Layer
Represents raw, derived, and interpreted measurements. Preserves lineage and explicit source typing.

### Material Layer
Represents material results and states. Does not invent unmeasured properties.

### Provenance Layer
Maintains structured lineage for all derived artifacts.

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
    → Validated Experiment Snapshot
    → Execution (Simulator or Hardware)
    → Raw Measurements
    → Derived Measurements
    → Material Results
    → Interpretation
```

Each stage is explicit and immutable once created.
