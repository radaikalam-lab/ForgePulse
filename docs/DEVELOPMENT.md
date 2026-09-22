# ForgePulse Development Guide

## Setup

```bash
git clone <repository-url>
cd ForgePulse
python -m pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest -q -W error
```

## Code Conventions

- Python >= 3.12
- Type hints on all public functions and methods
- `dataclasses` for immutable value objects where appropriate
- `enum.StrEnum` for status and type enumerations
- Deterministic serialization: UTF-8, sorted keys, UTC timestamps, no NaN/Infinity
- No hardware, network, database, or AI/ML dependencies during bootstrap

## Domain Model Guidelines

1. Use `@dataclass(frozen=True)` for immutable value objects.
2. Never silently convert between target and actual values.
3. Preserve provenance for every derived artifact.
4. Explicitly mark simulated data as simulated.
5. Do not invent material properties or physical laws.
6. Use `Experiment` lifecycle transitions through the `transition()` method only.
7. Never mutate `Experiment.status` directly; transitions return new instances.

## Edge Integration Guidelines

1. The `EdgeIntegrationBoundary` enforces state-dependent access controls.
2. Observations can only be recorded when the experiment is RUNNING.
3. Measurements can only be recorded when the experiment is RUNNING or COMPLETED.
4. Experiences can only be recorded when the experiment is COMPLETED or FAILED.
5. The boundary raises `InvalidTransition` for unauthorized state operations.
6. External integration failures are wrapped in `IntegrationFailure`.

## Simulator Guidelines

1. Simulator accepts only a `ValidatedExperimentSnapshot`, never a raw `ExperimentSpecification`.
2. All simulated outputs must be explicitly marked with `SourceType.SIMULATED`.
3. The simulator must be deterministic: identical snapshots produce identical outputs.
4. Deterministic seed is derived from the snapshot identity (e.g., SHA-256 of snapshot_id).
5. The simulator does not claim physical accuracy, experimental truth, or safety.
6. Baseline model assumptions must be documented in `SimulationMetadata.assumptions`.
7. The simulator does not modify the input snapshot.
8. `to_raw_measurements()` converts simulated measurements to edge-compatible `RawMeasurement` objects.
9. Provenance is preserved across simulation and translation.
10. The simulator must raise `ValueError` for invalid inputs (e.g., empty pulse sequence).

## Synthetic Data Guidelines

1. `SyntheticEdgeSource` generates deterministic data with optional seed.
2. No randomness is introduced without explicit seed configuration.
3. All synthetic data is marked with `SourceType.SIMULATED`.
4. Synthetic data does not connect to any real hardware or network.

## Measurement Translation Guidelines

1. `MeasurementTranslator` normalizes raw edge data to `RawMeasurement`.
2. All translated measurements are marked with `SourceType.RAW`.
3. Translation validates required fields and raises `MeasurementValidationError` on invalid input.
4. No physical laws or safety constraints are enforced during translation.

## Validation Guidelines

1. Validation must be deterministic.
2. Validation must not execute anything.
3. A successful validation does not imply successful execution.
4. Process constraints are distinct from safety interlocks.
5. Validation must not claim physical safety, scientific validity, experimental success, material quality, causal validity, or epistemic acceptance.
6. Validation diagnostics must be deterministic and ordered.
7. Validation is side-effect free: it does not mutate the experiment, create snapshots, or invoke external systems.
8. Invalid experiments cannot produce snapshots.
9. No hidden defaults: unknown values must remain unknown unless explicitly defined by contract.

## Snapshot Guidelines

1. `SnapshotValidator` creates immutable validated experiment snapshots.
2. Only valid specifications may produce snapshots.
3. Snapshots are deeply immutable: nested structures cannot be modified.
4. Snapshots are independent of the source experiment object.
5. Snapshot serialization is deterministic using canonical JSON.
6. Snapshot checksum is computed using SHA-256 over canonical representation.
7. `snapshot_id` identifies the snapshot object; `snapshot_checksum` verifies its content.
8. Snapshots retain provenance and validator metadata.
9. Execution must reference a `ValidatedExperimentSnapshot`, not a mutable `ExperimentSpecification`.

## Execution Readiness Guidelines

1. Execution readiness means the experiment has satisfied ForgePulse domain validation and has an immutable snapshot.
2. Execution readiness does not imply physical safety, scientific validity, guaranteed success, human approval, Cognitia approval, or hardware controller approval.
3. An execution must reference a `ValidatedExperimentSnapshot` via `snapshot_id`.
4. Once an execution references a snapshot, that snapshot must never be modified.
5. Different experiment versions create distinct snapshots and executions.

## Testing Guidelines

1. Write contract tests before implementation where practical.
2. Verify determinism of serialization.
3. Verify that Cognitia integration is optional.
4. Verify authority boundaries are not violated.
5. Run `python -m pytest -q -W error` before committing.

## Adding New Contracts

1. Create a markdown file in `contracts/`.
2. Define purpose, terminology, invariants, identity, versioning, serialization, validation, failure semantics, authority boundary, examples, and non-goals.
3. Update `docs/ARCHITECTURE.md` if the contract introduces new layers.

## Adding New Domain Models

1. Add types to the appropriate subpackage in `src/forgepulse/`.
2. Update the relevant contract.
3. Add tests in the corresponding `tests/` directory.
4. Verify `pytest -q -W error` passes.

## Cognitia Integration

- Do not copy Cognitia source code.
- Do not implement a second cognitive architecture.
- Keep the adapter layer minimal and optional.
- The adapter must never execute, bypass safety, or declare truth.
