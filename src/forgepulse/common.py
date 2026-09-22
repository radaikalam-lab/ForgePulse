"""Common types, errors, and utilities for ForgePulse."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class ForgePulseError(Exception):
    """Base exception for ForgePulse domain errors."""


class InvalidExperiment(ForgePulseError):
    """Raised when an experiment specification is structurally or semantically invalid."""


class InvalidPulseSequence(ForgePulseError):
    """Raised when a pulse sequence violates domain rules."""


class ConstraintViolation(ForgePulseError):
    """Raised when a process constraint is violated."""


class SnapshotViolation(ForgePulseError):
    """Raised when an immutable snapshot is mutated."""


class MeasurementValidationError(ForgePulseError):
    """Raised when a measurement fails structural or semantic validation."""


class ProvenanceError(ForgePulseError):
    """Raised when lineage is missing or circular."""


class UnsupportedOperation(ForgePulseError):
    """Raised when an operation is not supported in the current context."""


class AuthorityViolation(ForgePulseError):
    """Raised when an authority boundary is violated."""


class IntegrationFailure(ForgePulseError):
    """Raised when an external integration fails."""


class InvalidTransition(ForgePulseError):
    """Raised when an invalid lifecycle transition is attempted."""


@dataclass(frozen=True)
class Quantity:
    """A physical value with an explicit unit."""

    value: float
    unit: str

    def __post_init__(self) -> None:
        if self.value != self.value or self.value in (float("inf"), float("-inf")):
            raise ValueError("Quantity value must be finite and not NaN")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_value(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(obj, Quantity):
        return {"value": obj.value, "unit": obj.unit}
    if isinstance(obj, StrEnum):
        return obj.value
    if isinstance(obj, MappingProxyType):
        return {k: _serialize_value(v) for k, v in sorted(obj.items())}
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialize_value(v) for k, v in sorted(obj.__dict__.items()) if v is not None}
    if isinstance(obj, Mapping):
        return {k: _serialize_value(v) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [_serialize_value(v) for v in obj]
    return obj


def to_canonical_json(obj: Any) -> str:
    """Serialize a domain object to deterministic UTF-8 JSON."""
    serialized = _serialize_value(obj)
    return json.dumps(serialized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_checksum(obj: Any) -> str:
    """Compute a deterministic SHA-256 checksum for a domain object."""
    canonical = to_canonical_json(obj)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
