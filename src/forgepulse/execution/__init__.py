"""Execution domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Optional

from forgepulse.common import Quantity
from forgepulse.experiment import ExperimentSpecification


class ExecutionStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class TargetProcess:
    voltage: Optional[Quantity] = None
    current: Optional[Quantity] = None
    pulse_duration: Optional[Quantity] = None
    inter_pulse_interval: Optional[Quantity] = None


@dataclass(frozen=True)
class ActualProcess:
    measured_voltage: Optional[Quantity] = None
    measured_current: Optional[Quantity] = None
    measured_duration: Optional[Quantity] = None
    measured_interval: Optional[Quantity] = None


@dataclass(frozen=True)
class Execution:
    execution_id: str
    snapshot: ExperimentSpecification
    status: ExecutionStatus = ExecutionStatus.QUEUED
    target_process: TargetProcess = field(default_factory=TargetProcess)
    actual_process: ActualProcess = field(default_factory=ActualProcess)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    controller_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.started_at is not None and self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware UTC")
        if self.completed_at is not None and self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware UTC")
