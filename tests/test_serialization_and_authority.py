"""Tests for serialization and authority boundaries."""

from __future__ import annotations

from datetime import datetime, timezone

import json
import pytest

from forgepulse.common import (
    AuthorityViolation,
    Quantity,
    UnsupportedOperation,
    to_canonical_json,
)
from forgepulse.experiment import (
    Atmosphere,
    Chamber,
    ExperimentObjective,
    ExperimentSpecification,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
)
from forgepulse.integration import CognitiaAdapter


class TestCanonicalSerialization:
    def test_quantity_serialization(self):
        q = Quantity(value=120.0, unit="V")
        data = json.loads(to_canonical_json(q))
        assert data == {"unit": "V", "value": 120.0}

    def test_experiment_spec_serialization(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        json_str = to_canonical_json(spec)
        data = json.loads(json_str)
        assert data["experiment_id"] == "exp-001"
        assert data["pulse_sequence"]["pulses"][0]["target_voltage"]["value"] == 120.0

    def test_deterministic_serialization(self):
        spec = ExperimentSpecification(
            experiment_id="exp-001",
            experiment_version="1.0.0",
            schema_version="1.0.0",
            created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            objective=ExperimentObjective(description="Test"),
            feedstock=Feedstock(material="carbon black", mass=Quantity(value=0.5, unit="g")),
            chamber=Chamber(geometry="tubular", atmosphere=Atmosphere(gas="argon")),
            pulse_sequence=PulseSequence(
                pulses=(Pulse(target_voltage=Quantity(value=120.0, unit="V"), duration=Quantity(value=0.05, unit="s")),),
                inter_pulse_interval=Quantity(value=1.0, unit="s"),
            ),
            process_constraints=ProcessConstraint(),
        )
        first = to_canonical_json(spec)
        second = to_canonical_json(spec)
        assert first == second


class TestAuthorityBoundary:
    def test_cognitia_vocabulary_not_in_core_domain(self):
        import forgepulse.experiment as exp_mod
        import forgepulse.execution as exec_mod
        import forgepulse.measurement as meas_mod
        import forgepulse.material as mat_mod
        import forgepulse.validation as val_mod
        import forgepulse.simulation as sim_mod
        import forgepulse.provenance as prov_mod

        modules = [exp_mod, exec_mod, meas_mod, mat_mod, val_mod, sim_mod, prov_mod]
        for mod in modules:
            assert not hasattr(mod, "CognitiaAdapter")
            assert not hasattr(mod, "CognitiaObservation")

    def test_adapter_cannot_execute(self):
        adapter = CognitiaAdapter(enabled=True)
        with pytest.raises(UnsupportedOperation):
            adapter.request_advisory({"action": "execute"})
