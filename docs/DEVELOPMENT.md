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

## Validation Guidelines

1. Validation must be deterministic.
2. Validation must not execute anything.
3. A successful validation does not imply successful execution.
4. Process constraints are distinct from safety interlocks.

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
