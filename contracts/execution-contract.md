# Execution Contract

## Purpose

Define the semantics of executing a validated FJH experiment, distinguishing target specifications from actual physical outcomes.

## Terminology

- **Execution**: An attempt to run a `ValidatedExperimentSnapshot`.
- **ExecutionStatus**: The current state of an execution attempt.
- **TargetProcess**: The electrical and thermal parameters requested for the experiment.
- **ActualProcess**: The parameters measured during physical execution.
- **FJHController**: The entity responsible for physically executing pulses.

## Invariants

1. Every execution references a `ValidatedExperimentSnapshot`.
2. Target values are never overwritten by actual values.
3. An execution must not begin if the referenced snapshot has been invalidated.
4. Execution authority belongs to the FJH controller, not Cognitia.
5. Safety systems may veto execution independently.

## Identity

```text
execution_id: str
snapshot_id: str
status: ExecutionStatus
started_at: datetime (UTC)
completed_at: datetime (UTC, optional)
```

## Target vs Actual

```text
TargetProcess:
  voltage: Quantity
  current: Quantity
  pulse_duration: Quantity
  inter_pulse_interval: Quantity

ActualProcess:
  measured_voltage: Quantity
  measured_current: Quantity
  measured_duration: Quantity
  measured_interval: Quantity
```

## Execution Lifecycle

```text
QUEUED → RUNNING → COMPLETED
                       → FAILED
                       → ABORTED
```

## Serialization

- UTF-8 JSON
- Sorted keys
- UTC timestamps
- Explicit units

## Failure Semantics

- `AuthorityViolation`: Cognitia or adapter attempted execution.
- `SnapshotViolation`: execution references a mutable or invalid snapshot.
- `ExecutionFailure`: physical execution could not proceed.

## Authority Boundary

- Execution is controlled by the FJH controller.
- Cognitia may propose but never execute.
- Safety systems may veto.

## Examples

```json
{
  "execution_id": "exec-001",
  "snapshot_id": "snap-001",
  "status": "COMPLETED",
  "target_process": {
    "voltage": { "value": 120.0, "unit": "V" },
    "pulse_duration": { "value": 0.05, "unit": "s" }
  },
  "actual_process": {
    "measured_voltage": { "value": 118.7, "unit": "V" },
    "measured_duration": { "value": 0.051, "unit": "s" }
  }
}
```

## Non-Goals

- This contract does not define GPIO or hardware protocols.
- This contract does not define safety interlock logic.
