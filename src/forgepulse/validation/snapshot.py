"""Immutable validated experiment snapshot creation."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Optional

from forgepulse.common import (
    InvalidExperiment,
    _utc_now,
    compute_checksum,
)
from forgepulse.experiment import ExperimentSpecification


def _freeze_specification(spec: ExperimentSpecification) -> ExperimentSpecification:
    """Create a deeply immutable copy of an ExperimentSpecification.

    Converts mutable collections (dicts) to immutable representations
    to ensure snapshot deep immutability.
    """
    frozen_metadata = MappingProxyType(dict(sorted(spec.metadata.items())))
    frozen_pulse_sequence = replace(
        spec.pulse_sequence,
        metadata=MappingProxyType(dict(sorted(spec.pulse_sequence.metadata.items()))),
    )
    frozen_process_constraints = replace(spec.process_constraints)
    frozen_feedstock = replace(
        spec.feedstock,
        additives=tuple(
            replace(a, role=a.role) for a in spec.feedstock.additives
        ),
    )
    frozen_chamber = replace(spec.chamber)
    frozen_objective = replace(spec.objective)
    return replace(
        spec,
        objective=frozen_objective,
        feedstock=frozen_feedstock,
        chamber=frozen_chamber,
        pulse_sequence=frozen_pulse_sequence,
        process_constraints=frozen_process_constraints,
        metadata=frozen_metadata,
    )


def _snapshot_id(spec: ExperimentSpecification) -> str:
    """Generate a deterministic snapshot identifier."""
    return f"snap-{spec.experiment_id}-{spec.experiment_version}"


@dataclass(frozen=True)
class SnapshotValidator:
    """Creates immutable validated experiment snapshots.

    Validation is side-effect free and deterministic.
    Snapshots are deeply immutable and independent of the source experiment object.
    """

    validator_id: str = "forgepulse-validator-v1"
    validator_version: str = "1.0.0"

    def validate(self, spec: ExperimentSpecification) -> "ValidationResult":
        """Deterministically validate an experiment specification.

        This method is side-effect free. It does not mutate the specification,
        create snapshots, or invoke any external systems.

        Args:
            spec: The experiment specification to validate.

        Returns:
            A deterministic ValidationResult.
        """
        from forgepulse.validation import validate_experiment
        return validate_experiment(spec)

    def create_snapshot(
        self,
        spec: ExperimentSpecification,
        validator_id: Optional[str] = None,
    ) -> "ValidatedExperimentSnapshot":
        """Create an immutable validated experiment snapshot.

        Only valid specifications may produce snapshots.

        Args:
            spec: The experiment specification to snapshot.
            validator_id: Optional override for the validator identifier.

        Returns:
            An immutable ValidatedExperimentSnapshot.

        Raises:
            InvalidExperiment: If the specification is invalid.
        """
        from forgepulse.validation import validate_experiment, ValidationResult
        validation_result = validate_experiment(spec)
        if not validation_result.valid:
            raise InvalidExperiment(
                f"Cannot create snapshot for invalid experiment: {validation_result.errors}"
            )

        effective_validator_id = validator_id or self.validator_id
        frozen_spec = _freeze_specification(spec)
        snapshot_id = _snapshot_id(frozen_spec)
        created_at = _utc_now()
        checksum = compute_checksum(frozen_spec)

        from forgepulse.experiment import ValidatedExperimentSnapshot
        snapshot = ValidatedExperimentSnapshot(
            snapshot_id=snapshot_id,
            experiment_id=frozen_spec.experiment_id,
            experiment_version=frozen_spec.experiment_version,
            schema_version=frozen_spec.schema_version,
            specification=frozen_spec,
            validation_result=validation_result,
            validator_id=effective_validator_id,
            created_at=created_at,
            checksum=checksum,
        )
        return snapshot

    def verify_checksum(self, snapshot: "ValidatedExperimentSnapshot") -> bool:
        """Verify that a snapshot's checksum matches its content.

        Args:
            snapshot: The snapshot to verify.

        Returns:
            True if the checksum is valid, False otherwise.
        """
        expected = compute_checksum(snapshot.specification)
        return snapshot.checksum == expected