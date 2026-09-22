"""Phase 1.1 Edge Boundary Audit regression tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from forgepulse.common import IntegrationFailure, InvalidTransition, MeasurementValidationError, Quantity, UnsupportedOperation
from forgepulse.experiment import (
    Atmosphere,
    Chamber,
    Experiment,
    ExperimentObjective,
    ExperimentSpecification,
    ExperimentStatus,
    Feedstock,
    Pulse,
    PulseSequence,
    ProcessConstraint,
    ValidatedExperimentSnapshot,
)
from forgepulse.integration import (
    CognitiaAdapter,
    EdgeIntegrationBoundary,
    MeasurementTranslator,
    SyntheticEdgeSource,
)
from forgepulse.measurement import (
    RawMeasurement,
    SourceType,
)
from forgepulse.simulation import Simulator
from forgepulse.validation import SnapshotValidator


def _make_spec() -> ExperimentSpecification:
    return ExperimentSpecification(
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


def _make_experiment() -> Experiment:
    spec = _make_spec()
    return Experiment(experiment_id=spec.experiment_id, specification=spec)


def _experiment_at_status(target_status: ExperimentStatus) -> Experiment:
    spec = _make_spec()
    e = Experiment(experiment_id=spec.experiment_id, specification=spec)
    if target_status == ExperimentStatus.RESEARCH_INTENT:
        return e
    e = e.transition(ExperimentStatus.PROPOSED)
    if target_status == ExperimentStatus.PROPOSED:
        return e
    e = e.transition(ExperimentStatus.SPECIFIED)
    if target_status == ExperimentStatus.SPECIFIED:
        return e
    e = e.transition(ExperimentStatus.VALIDATED)
    if target_status == ExperimentStatus.VALIDATED:
        return e
    e = e.transition(ExperimentStatus.SNAPSHOTTED)
    if target_status == ExperimentStatus.SNAPSHOTTED:
        return e
    e = e.transition(ExperimentStatus.QUEUED)
    if target_status == ExperimentStatus.QUEUED:
        return e
    e = e.transition(ExperimentStatus.RUNNING)
    if target_status == ExperimentStatus.RUNNING:
        return e
    if target_status == ExperimentStatus.COMPLETED:
        e = e.transition(ExperimentStatus.COMPLETED)
        return e
    if target_status == ExperimentStatus.FAILED:
        e = Experiment(experiment_id=spec.experiment_id, specification=spec)
        e = e.transition(ExperimentStatus.PROPOSED)
        e = e.transition(ExperimentStatus.SPECIFIED)
        e = e.transition(ExperimentStatus.VALIDATED)
        e = e.transition(ExperimentStatus.SNAPSHOTTED)
        e = e.transition(ExperimentStatus.QUEUED)
        e = e.transition(ExperimentStatus.RUNNING)
        e = e.transition(ExperimentStatus.FAILED)
        return e
    if target_status == ExperimentStatus.ABORTED:
        e = Experiment(experiment_id=spec.experiment_id, specification=spec)
        e = e.transition(ExperimentStatus.PROPOSED)
        e = e.transition(ExperimentStatus.SPECIFIED)
        e = e.transition(ExperimentStatus.VALIDATED)
        e = e.transition(ExperimentStatus.SNAPSHOTTED)
        e = e.transition(ExperimentStatus.QUEUED)
        e = e.transition(ExperimentStatus.RUNNING)
        e = e.transition(ExperimentStatus.ABORTED)
        return e
    if target_status == ExperimentStatus.MEASURED:
        e = Experiment(experiment_id=spec.experiment_id, specification=spec)
        e = e.transition(ExperimentStatus.PROPOSED)
        e = e.transition(ExperimentStatus.SPECIFIED)
        e = e.transition(ExperimentStatus.VALIDATED)
        e = e.transition(ExperimentStatus.SNAPSHOTTED)
        e = e.transition(ExperimentStatus.QUEUED)
        e = e.transition(ExperimentStatus.RUNNING)
        e = e.transition(ExperimentStatus.COMPLETED)
        e = e.transition(ExperimentStatus.MEASURED)
        return e
    if target_status == ExperimentStatus.DERIVED:
        e = Experiment(experiment_id=spec.experiment_id, specification=spec)
        e = e.transition(ExperimentStatus.PROPOSED)
        e = e.transition(ExperimentStatus.SPECIFIED)
        e = e.transition(ExperimentStatus.VALIDATED)
        e = e.transition(ExperimentStatus.SNAPSHOTTED)
        e = e.transition(ExperimentStatus.QUEUED)
        e = e.transition(ExperimentStatus.RUNNING)
        e = e.transition(ExperimentStatus.COMPLETED)
        e = e.transition(ExperimentStatus.MEASURED)
        e = e.transition(ExperimentStatus.DERIVED)
        return e
    if target_status == ExperimentStatus.CHARACTERIZED:
        e = Experiment(experiment_id=spec.experiment_id, specification=spec)
        e = e.transition(ExperimentStatus.PROPOSED)
        e = e.transition(ExperimentStatus.SPECIFIED)
        e = e.transition(ExperimentStatus.VALIDATED)
        e = e.transition(ExperimentStatus.SNAPSHOTTED)
        e = e.transition(ExperimentStatus.QUEUED)
        e = e.transition(ExperimentStatus.RUNNING)
        e = e.transition(ExperimentStatus.COMPLETED)
        e = e.transition(ExperimentStatus.MEASURED)
        e = e.transition(ExperimentStatus.DERIVED)
        e = e.transition(ExperimentStatus.CHARACTERIZED)
        return e
    if target_status == ExperimentStatus.INTERPRETED:
        e = Experiment(experiment_id=spec.experiment_id, specification=spec)
        e = e.transition(ExperimentStatus.PROPOSED)
        e = e.transition(ExperimentStatus.SPECIFIED)
        e = e.transition(ExperimentStatus.VALIDATED)
        e = e.transition(ExperimentStatus.SNAPSHOTTED)
        e = e.transition(ExperimentStatus.QUEUED)
        e = e.transition(ExperimentStatus.RUNNING)
        e = e.transition(ExperimentStatus.COMPLETED)
        e = e.transition(ExperimentStatus.MEASURED)
        e = e.transition(ExperimentStatus.DERIVED)
        e = e.transition(ExperimentStatus.CHARACTERIZED)
        e = e.transition(ExperimentStatus.INTERPRETED)
        return e
    raise ValueError(f"Unknown status {target_status}")


class TestLifecycleAudit:
    def test_run_through_full_lifecycle(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.COMPLETED)
        experiment = experiment.transition(ExperimentStatus.MEASURED)
        experiment = experiment.transition(ExperimentStatus.DERIVED)
        experiment = experiment.transition(ExperimentStatus.CHARACTERIZED)
        experiment = experiment.transition(ExperimentStatus.INTERPRETED)
        assert experiment.status == ExperimentStatus.INTERPRETED

    def test_failed_can_reach_measured(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.FAILED)
        experiment = experiment.transition(ExperimentStatus.MEASURED)
        assert experiment.status == ExperimentStatus.MEASURED

    def test_aborted_cannot_proceed(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        experiment = experiment.transition(ExperimentStatus.ABORTED)
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.COMPLETED)

    def test_history_is_auditable(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED, note="initial")
        experiment = experiment.transition(ExperimentStatus.SPECIFIED, note="specified")
        assert len(experiment.history) == 2
        assert experiment.history[0].from_status == ExperimentStatus.RESEARCH_INTENT
        assert experiment.history[0].to_status == ExperimentStatus.PROPOSED
        assert experiment.history[0].note == "initial"
        assert experiment.history[1].from_status == ExperimentStatus.PROPOSED
        assert experiment.history[1].to_status == ExperimentStatus.SPECIFIED

    def test_experiment_is_immutable(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        with pytest.raises(AttributeError):
            experiment.status = ExperimentStatus.RUNNING


class TestTargetActualSeparation:
    def test_simulator_does_not_copy_target_to_actual(self):
        spec = _make_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        target_v = spec.pulse_sequence.pulses[0].target_voltage.value
        actual_v = result.actual_process.measured_voltage.value
        assert actual_v != target_v, "Actual voltage must not equal target voltage"

    def test_simulator_different_execution_ids_produce_different_actuals(self):
        spec1 = ExperimentSpecification(
            experiment_id="exp-a",
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
        spec2 = ExperimentSpecification(
            experiment_id="exp-b",
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
        snapshot1 = SnapshotValidator().create_snapshot(spec1)
        snapshot2 = SnapshotValidator().create_snapshot(spec2)
        simulator = Simulator()
        result1 = simulator.simulate(snapshot1)
        result2 = simulator.simulate(snapshot2)
        assert result1.actual_process.measured_voltage != result2.actual_process.measured_voltage

    def test_simulator_same_execution_id_produces_same_actuals(self):
        spec = _make_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        simulator = Simulator()
        result1 = simulator.simulate(snapshot)
        result2 = simulator.simulate(snapshot)
        assert result1.actual_process.measured_voltage == result2.actual_process.measured_voltage


class TestSyntheticSourceIdentity:
    def test_synthetic_voltage_is_simulated(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert measurement.source_type == SourceType.SIMULATED

    def test_synthetic_cannot_masquerade_as_measured(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert measurement.source_type != SourceType.MEASURED

    def test_synthetic_deterministic_with_seed(self):
        source1 = SyntheticEdgeSource(seed=42)
        source2 = SyntheticEdgeSource(seed=42)
        m1 = source1.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        m2 = source2.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert m1.values == m2.values
        assert m1.start_time == m2.start_time

    def test_synthetic_different_seeds_different_values(self):
        source1 = SyntheticEdgeSource(seed=1)
        source2 = SyntheticEdgeSource(seed=2)
        m1 = source1.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        m2 = source2.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert m1.values != m2.values

    def test_synthetic_start_time_is_deterministic(self):
        source = SyntheticEdgeSource(seed=42)
        m1 = source.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        m2 = source.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert m1.start_time == m2.start_time


class TestEdgeBoundaryAudit:
    def test_edge_cannot_issue_hardware_commands(self):
        experiment = _make_experiment()
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        methods = [m for m in dir(boundary) if not m.startswith("_")]
        for method in methods:
            assert "fire" not in method.lower()
            assert "pulse" not in method.lower()
            assert "voltage" not in method.lower()
            assert "current" not in method.lower()
            assert "execute" not in method.lower()
            assert "energize" not in method.lower()

    def test_edge_does_not_mutate_specification(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        original_id = experiment.specification.experiment_id
        boundary.record_observation({"data": "test"})
        assert experiment.specification.experiment_id == original_id

    def test_observation_requires_running(self):
        for status in [
            ExperimentStatus.RESEARCH_INTENT,
            ExperimentStatus.PROPOSED,
            ExperimentStatus.SPECIFIED,
            ExperimentStatus.VALIDATED,
            ExperimentStatus.SNAPSHOTTED,
            ExperimentStatus.QUEUED,
            ExperimentStatus.COMPLETED,
            ExperimentStatus.FAILED,
            ExperimentStatus.ABORTED,
            ExperimentStatus.MEASURED,
            ExperimentStatus.DERIVED,
            ExperimentStatus.CHARACTERIZED,
            ExperimentStatus.INTERPRETED,
        ]:
            if status == ExperimentStatus.RUNNING:
                continue
            e = _experiment_at_status(status)
            b = EdgeIntegrationBoundary(experiment=e)
            with pytest.raises(InvalidTransition):
                b.record_observation({"data": "test"})

    def test_measurement_requires_running_or_completed(self):
        for status in [
            ExperimentStatus.RESEARCH_INTENT,
            ExperimentStatus.PROPOSED,
            ExperimentStatus.SPECIFIED,
            ExperimentStatus.VALIDATED,
            ExperimentStatus.SNAPSHOTTED,
            ExperimentStatus.QUEUED,
            ExperimentStatus.FAILED,
            ExperimentStatus.ABORTED,
            ExperimentStatus.MEASURED,
            ExperimentStatus.DERIVED,
            ExperimentStatus.CHARACTERIZED,
            ExperimentStatus.INTERPRETED,
        ]:
            e = _experiment_at_status(status)
            b = EdgeIntegrationBoundary(experiment=e)
            measurement = RawMeasurement(
                measurement_id="m1",
                quantity="voltage",
                values=[1.0],
                unit="V",
                source_type=SourceType.RAW,
            )
            if status in (ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED):
                b.record_measurement(measurement)
            else:
                with pytest.raises(InvalidTransition):
                    b.record_measurement(measurement)

    def test_measurement_does_not_transition_to_measured(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        measurement = RawMeasurement(
            measurement_id="m1",
            quantity="voltage",
            values=[1.0],
            unit="V",
            source_type=SourceType.RAW,
        )
        boundary.record_measurement(measurement)
        assert experiment.status == ExperimentStatus.RUNNING
        assert boundary.measurement_count == 1


class TestCognitiaIsolation:
    def test_cognitia_unavailable_does_not_break_ingestion(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        boundary.record_observation({"data": "test"})
        boundary.record_measurement(
            RawMeasurement(
                measurement_id="m1",
                quantity="v",
                values=[1.0],
                unit="V",
                source_type=SourceType.RAW,
            )
        )

    def test_cognitia_advisory_failure_does_not_break_experiment(self):
        class FailingAdapter:
            def request_advisory(self, request):
                raise RuntimeError("Cognitia down")

        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment, cognitia_adapter=FailingAdapter())
        with pytest.raises(IntegrationFailure):
            boundary.request_advisory({"request": "test"})
        assert experiment.status == ExperimentStatus.RUNNING

    def test_cognitia_disabled_returns_none_for_advisory(self):
        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment)
        result = boundary.request_advisory({"request": "test"})
        assert result is None

    def test_cognitia_cannot_execute_experiment(self):
        adapter = CognitiaAdapter(enabled=True)
        with pytest.raises(UnsupportedOperation):
            adapter.request_advisory({"action": "execute_pulse"})


class TestTranslatorAudit:
    def test_translator_preserves_source_as_raw(self):
        translator = MeasurementTranslator()
        raw = {"values": [1.0, 2.0], "unit": "V"}
        result = translator.translate("m1", raw, quantity="voltage")
        assert result.source_type == SourceType.RAW

    def test_translator_preserves_unit(self):
        translator = MeasurementTranslator()
        raw = {"values": [1.0], "unit": "mV"}
        result = translator.translate("m1", raw, quantity="voltage")
        assert result.unit == "mV"

    def test_translator_normalizes_iso_timestamp(self):
        translator = MeasurementTranslator()
        raw = {"values": [1.0], "unit": "V", "start_time": "2026-01-15T10:30:00Z"}
        result = translator.translate("m1", raw, quantity="voltage")
        assert result.start_time == datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_translator_normalizes_sampling_rate_dict(self):
        translator = MeasurementTranslator()
        raw = {"values": [1.0], "unit": "V", "sampling_rate": {"value": 50.0, "unit": "Hz"}}
        result = translator.translate("m1", raw, quantity="voltage")
        assert result.sampling_rate == Quantity(value=50.0, unit="Hz")

    def test_translator_rejects_missing_values(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="values must be a non-empty list"):
            translator.translate("m1", {"unit": "V"}, quantity="voltage")

    def test_translator_rejects_non_numeric_values(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="values must contain only numbers"):
            translator.translate("m1", {"values": ["a"], "unit": "V"}, quantity="voltage")

    def test_translator_rejects_missing_unit(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="unit must be a non-empty string"):
            translator.translate("m1", {"values": [1.0]}, quantity="voltage")

    def test_translator_batch_requires_measurement_id(self):
        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError, match="measurement_id is required"):
            translator.translate_batch([{"values": [1.0], "unit": "V"}])

    def test_translator_no_scientific_interpretation(self):
        translator = MeasurementTranslator()
        raw = {"values": [1.0, 2.0, 3.0], "unit": "V", "sampling_rate": 100.0}
        result = translator.translate("m1", raw, quantity="voltage")
        assert result.quantity == "voltage"
        assert result.values == [1.0, 2.0, 3.0]
        assert result.source_type == SourceType.RAW


class TestProvenancePreservation:
    def test_simulator_preserves_provenance(self):
        spec = _make_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        assert result.provenance.artifact_id.startswith("sim-")
        assert result.provenance.artifact_type == "simulation"
        assert result.provenance.transformation == "deterministic_baseline_simulation"

    def test_raw_measurement_has_provenance_reference(self):
        source = SyntheticEdgeSource(seed=42)
        measurement = source.generate_voltage_series("v1", 1.0, 100.0, 120.0)
        assert measurement.provenance is not None

    def test_measurement_series_provenance_survives_translation(self):
        spec = _make_spec()
        snapshot = SnapshotValidator().create_snapshot(spec)
        simulator = Simulator()
        result = simulator.simulate(snapshot)
        raw_measurements = simulator.to_raw_measurements(result)
        assert len(raw_measurements) == 4
        assert raw_measurements[0].provenance.artifact_id == snapshot.snapshot_id


class TestFailureSemantics:
    def test_invalid_transition_distinct_from_measurement_error(self):
        spec = _make_spec()
        experiment = Experiment(experiment_id=spec.experiment_id, specification=spec)
        with pytest.raises(InvalidTransition):
            experiment.transition(ExperimentStatus.RUNNING)

        translator = MeasurementTranslator()
        with pytest.raises(MeasurementValidationError):
            translator.translate("m1", {"values": [], "unit": "V"}, quantity="voltage")

    def test_integration_failure_distinct_from_unsupported(self):
        adapter = CognitiaAdapter(enabled=True)
        with pytest.raises(UnsupportedOperation):
            adapter.record_measurement(None)

        class FailingAdapter:
            def record_measurement(self, measurement):
                raise RuntimeError("connection lost")

        experiment = _make_experiment()
        experiment = experiment.transition(ExperimentStatus.PROPOSED)
        experiment = experiment.transition(ExperimentStatus.SPECIFIED)
        experiment = experiment.transition(ExperimentStatus.VALIDATED)
        experiment = experiment.transition(ExperimentStatus.SNAPSHOTTED)
        experiment = experiment.transition(ExperimentStatus.QUEUED)
        experiment = experiment.transition(ExperimentStatus.RUNNING)
        boundary = EdgeIntegrationBoundary(experiment=experiment, cognitia_adapter=FailingAdapter())
        with pytest.raises(IntegrationFailure):
            boundary.record_measurement(
                RawMeasurement(
                    measurement_id="m1",
                    quantity="v",
                    values=[1.0],
                    unit="V",
                    source_type=SourceType.RAW,
                )
            )
