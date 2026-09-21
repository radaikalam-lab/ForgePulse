"""Tests for Cognitia integration boundary."""

from __future__ import annotations

import pytest

from forgepulse.common import UnsupportedOperation
from forgepulse.integration import CognitiaAdapter


class TestCognitiaOptional:
    def test_adapter_disabled_by_default(self):
        adapter = CognitiaAdapter()
        # Should not raise when disabled
        adapter.record_experiment_observation(None)
        adapter.record_measurement(None)
        adapter.record_experience(None)
        adapter.record_evidence(None)
        assert adapter.request_advisory(None) is None

    def test_adapter_enabled_raises_unsupported(self):
        adapter = CognitiaAdapter(enabled=True)
        with pytest.raises(UnsupportedOperation):
            adapter.record_experiment_observation(None)
        with pytest.raises(UnsupportedOperation):
            adapter.record_measurement(None)
        with pytest.raises(UnsupportedOperation):
            adapter.record_experience(None)
        with pytest.raises(UnsupportedOperation):
            adapter.record_evidence(None)
        with pytest.raises(UnsupportedOperation):
            adapter.request_advisory(None)

    def test_adapter_never_executes(self):
        adapter = CognitiaAdapter(enabled=True)
        with pytest.raises(UnsupportedOperation):
            adapter.request_advisory({"action": "execute_pulse"})
