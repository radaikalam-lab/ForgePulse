"""Provenance domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from forgepulse.common import _utc_now


@dataclass(frozen=True)
class LineageReference:
    artifact_id: str
    artifact_type: str


@dataclass(frozen=True)
class ProvenanceRecord:
    artifact_id: str
    artifact_type: str
    source_ids: tuple[LineageReference, ...] = ()
    transformation: Optional[str] = None
    created_at: datetime = field(default_factory=_utc_now)
    created_by: str = "forgepulse"

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware UTC")
