# Cognition Integration Contract

## Purpose

Define the boundary between ForgePulse and the external Cognitia cognitive substrate.

## Terminology

- **Cognitia**: An external cognitive infrastructure dependency.
- **CognitiaAdapter**: The ForgePulse integration layer for Cognitia.
- **Observation**: A ForgePulse event translated for Cognitia.
- **Experience**: An execution episode translated for Cognitia.
- **Evidence**: A scientific evidence structure translated for Cognitia.
- **Advisory**: A response from Cognitia to a ForgePulse request.

## Invariants

1. ForgePulse is independent of Cognitia.
2. Cognitia has no execution authority over ForgePulse.
3. The adapter is optional; ForgePulse functions without Cognitia.
4. No Cognitia source code is copied into ForgePulse.
5. No Cognitia vocabulary leaks into core ForgePulse domain modules.

## Translation Boundaries

```text
ForgePulse Experiment          → Cognitia Observation
ForgePulse Measurement         → Cognitia Observation
ForgePulse Experiment Episode  → Cognitia Experience
ForgePulse scientific evidence → Cognitia Evidence
ForgePulse provenance          → Cognitia ProvenanceRecord
```

## Adapter Interface (Planned)

```text
record_experiment_observation(experiment: Experiment) -> None
record_measurement(measurement: Measurement) -> None
record_experience(execution: Execution) -> None
record_evidence(evidence: Evidence) -> None
request_advisory(request: AdvisoryRequest) -> Advisory
```

## Authority Boundary

- Cognitia may propose. ForgePulse validates. The controller executes. Safety systems may veto.
- The adapter must never:
  - execute a pulse
  - bypass validation
  - bypass safety
  - mutate hardware state
  - declare scientific truth
  - directly activate learned models

## Serialization

- UTF-8 JSON
- Sorted keys
- UTC timestamps
- Same deterministic rules as core ForgePulse serialization

## Failure Semantics

- `IntegrationFailure`: Cognitia is unavailable or returns an error.
- `UnsupportedOperation`: adapter method not yet implemented.

## Non-Goals

- This contract does not define Cognitia's internal architecture.
- This contract does not require a live Cognitia installation for ForgePulse to function.
