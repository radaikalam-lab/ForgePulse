# Simulation Contract

## Purpose

Define the semantics of the deterministic FJH simulator, establishing clear boundaries between simulation, measurement, and hardware authority.

## Terminology

- **Simulator**: A deterministic program that produces synthetic FJH observations from a validated experiment snapshot.
- **SimulatorResult**: The complete output of a simulation run, including measurements, observations, metadata, and provenance.
- **SimulationMetadata**: Identifies the simulator implementation, model version, seed, sampling rate, and documented assumptions.
- **ValidatedExperimentSnapshot**: The immutable input to the simulator; only valid snapshots may be simulated.
- **Simulated**: Explicitly marked as produced by the simulator, never claiming physical accuracy or experimental truth.

## Invariants

1. The simulator accepts only a `ValidatedExperimentSnapshot`, never a raw `ExperimentSpecification`.
2. All simulator outputs are explicitly marked with `SourceType.SIMULATED`.
3. The simulator is deterministic: identical snapshots produce identical outputs.
4. The simulator does not modify the input snapshot.
5. The simulator does not claim physical accuracy, experimental truth, or safety.
6. Baseline model assumptions are documented in `SimulationMetadata.assumptions`.
7. Empty pulse sequences are rejected with `ValueError`.
8. Provenance is preserved from snapshot through simulation output.

## Identity

```text
simulation_id: str
snapshot_id: str
experiment_id: str
experiment_version: str
provenance: ProvenanceRecord
```

## Simulator Result

```text
simulation_id: str
snapshot_id: str
experiment_id: str
experiment_version: str
target_process: TargetProcess
actual_process: ActualProcess
measurements: tuple[MeasurementSeries, ...]
electrical_observation: ElectricalObservation
thermal_observation: ThermalObservation
simulation_metadata: SimulationMetadata
provenance: ProvenanceRecord
```

## Simulation Metadata

```text
simulator_id: str
simulator_version: str
model_version: str
seed: int (non-negative)
sampling_rate_hz: float (positive)
assumptions: tuple[str, ...]
```

## Determinism

- Seed is derived deterministically from `snapshot_id` (e.g., SHA-256).
- Random number generator is seeded once per simulation.
- No external randomness or system entropy is used.

## Serialization

- UTF-8 JSON
- Sorted keys
- UTC timestamps
- No NaN or Infinity

## Failure Semantics

- `ValueError`: Empty pulse sequence or other invalid input to `simulate()`.
- `InvalidExperiment`: Raised during snapshot creation if specification is invalid; simulator never receives invalid snapshots.

## Authority Boundary

- The simulator has no execution authority.
- The simulator does not execute hardware commands.
- The simulator does not bypass validation or safety constraints.
- Simulated data flows through the edge integration boundary as `SourceType.SIMULATED`.

## Non-Goals

- The simulator does not implement material-specific physics.
- The simulator does not model plasma dynamics or thermal FEM.
- The simulator does not predict real experimental outcomes.
- The simulator is not a substitute for physical measurement.
- The simulator does not grant execution or safety approval.