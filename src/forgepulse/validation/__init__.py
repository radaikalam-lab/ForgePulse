"""Validation for FJH experiment specifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from forgepulse.common import (
    ConstraintViolation,
    InvalidExperiment,
    InvalidPulseSequence,
    Quantity,
    _utc_now,
)
from forgepulse.experiment import (
    ExperimentSpecification,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
)
from forgepulse.validation.snapshot import SnapshotValidator


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    validator_id: str = "forgepulse-validator-v1"
    validated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.validated_at.tzinfo is None:
            raise ValueError("validated_at must be timezone-aware UTC")


def _finite_quantity(q: Optional[Quantity], name: str) -> list[str]:
    errors: list[str] = []
    if q is not None:
        if q.value <= 0:
            errors.append(f"{name} must be positive, got {q.value}")
        if q.value != q.value or q.value in (float("inf"), float("-inf")):
            errors.append(f"{name} must be finite")
    return errors


def _validate_pulse(pulse: Pulse, index: int) -> list[str]:
    errors: list[str] = []
    errors.extend(_finite_quantity(pulse.target_voltage, f"pulse[{index}].target_voltage"))
    errors.extend(_finite_quantity(pulse.duration, f"pulse[{index}].duration"))
    if pulse.target_current is not None:
        errors.extend(_finite_quantity(pulse.target_current, f"pulse[{index}].target_current"))
    return errors


def _validate_pulse_sequence(sequence: PulseSequence) -> list[str]:
    errors: list[str] = []
    if not sequence.pulses:
        errors.append("pulse_sequence.pulses must not be empty")
        return errors
    if sequence.inter_pulse_interval.value < 0:
        errors.append("pulse_sequence.inter_pulse_interval must be non-negative")
    for idx, pulse in enumerate(sequence.pulses):
        errors.extend(_validate_pulse(pulse, idx))
    return errors


def _validate_feedstock(feedstock: Feedstock) -> list[str]:
    errors: list[str] = []
    if not feedstock.material.strip():
        errors.append("feedstock.material must not be empty")
    if feedstock.mass.value <= 0:
        errors.append("feedstock.mass must be positive")
    return errors


def _validate_constraints(spec: ExperimentSpecification) -> list[str]:
    errors: list[str] = []
    constraints = spec.process_constraints
    pulses = spec.pulse_sequence.pulses
    if not pulses:
        return errors

    max_voltage = constraints.maximum_target_voltage
    if max_voltage is not None:
        if any(p.target_voltage.value > max_voltage.value for p in pulses):
            errors.append(
                f"pulse voltage exceeds maximum_target_voltage ({max_voltage.value} {max_voltage.unit})"
            )

    max_current = constraints.maximum_target_current
    if max_current is not None:
        for p in pulses:
            if p.target_current is not None and p.target_current.value > max_current.value:
                errors.append(
                    f"pulse current exceeds maximum_target_current ({max_current.value} {max_current.unit})"
                )

    max_duration = constraints.maximum_pulse_duration
    if max_duration is not None:
        if any(p.duration.value > max_duration.value for p in pulses):
            errors.append(
                f"pulse duration exceeds maximum_pulse_duration ({max_duration.value} {max_duration.unit})"
            )

    max_seq_duration = constraints.maximum_sequence_duration
    if max_seq_duration is not None:
        total = sum(p.duration.value for p in pulses) + (
            spec.pulse_sequence.inter_pulse_interval.value * max(0, len(pulses) - 1)
        )
        if total > max_seq_duration.value:
            errors.append(
                f"sequence duration exceeds maximum_sequence_duration ({max_seq_duration.value} {max_seq_duration.unit})"
            )

    return errors


def validate_experiment(spec: ExperimentSpecification) -> ValidationResult:
    """Deterministically validate an experiment specification.

    Validation does not execute anything.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not spec.experiment_id.strip():
        errors.append("experiment_id must not be empty")
    if not spec.experiment_version.strip():
        errors.append("experiment_version must not be empty")
    if not spec.objective.description.strip():
        errors.append("objective.description must not be empty")

    errors.extend(_validate_feedstock(spec.feedstock))
    errors.extend(_validate_pulse_sequence(spec.pulse_sequence))
    errors.extend(_validate_constraints(spec))

    if not errors:
        if spec.pulse_sequence.pulses:
            if spec.process_constraints.maximum_pulse_duration is None:
                warnings.append("No maximum_pulse_duration constraint defined")
            if spec.process_constraints.maximum_target_voltage is None:
                warnings.append("No maximum_target_voltage constraint defined")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
