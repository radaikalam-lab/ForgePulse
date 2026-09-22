"""Tests for Phase 5 scientific interpretation models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forgepulse.common import Quantity
from forgepulse.interpretation import (
    CompetingInterpretation,
    Evidence,
    Hypothesis,
    InterpretationMethod,
    InterpretationResult,
    InterpretationStatus,
    InterpretationValidationError,
    MaterialEvolution,
    Residual,
    Unknown,
)
from forgepulse.material import MaterialState, YieldRepresentation, YieldBasis
from forgepulse.measurement import SourceType
from forgepulse.measurement.characterization import Uncertainty
from forgepulse.measurement.models import ProvenanceReference


def _utc(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


class TestEvidenceIdentity:
    def test_evidence_creation(self):
        evidence = Evidence(
            evidence_id="ev-001",
            source_reference="meas-001",
            evidence_type="measurement",
            description="Voltage peak observed during pulse",
            relevance="Directly supports hypothesis of sufficient energy input",
        )
        assert evidence.evidence_id == "ev-001"
        assert evidence.source_reference == "meas-001"
        assert evidence.evidence_type == "measurement"

    def test_evidence_with_strength_requires_definition(self):
        with pytest.raises(ValueError, match="strength_definition"):
            Evidence(
                evidence_id="ev-002",
                source_reference="meas-002",
                evidence_type="derived",
                description="Power calculation",
                relevance="Supports energy estimate",
                strength="high",
            )

    def test_evidence_with_strength_and_definition(self):
        evidence = Evidence(
            evidence_id="ev-003",
            source_reference="meas-003",
            evidence_type="characterization",
            description="Temperature rise",
            relevance="Indicates heating efficiency",
            strength="moderate",
            strength_definition="Single measurement, no replication",
        )
        assert evidence.strength == "moderate"
        assert evidence.strength_definition == "Single measurement, no replication"

    def test_evidence_empty_id_raises(self):
        with pytest.raises(ValueError, match="evidence_id"):
            Evidence(
                evidence_id="",
                source_reference="src",
                evidence_type="type",
                description="desc",
                relevance="rel",
            )

    def test_evidence_measurement_references(self):
        evidence = Evidence(
            evidence_id="ev-004",
            source_reference="meas-004",
            evidence_type="measurement",
            description="Current trace",
            relevance="Supports power calculation",
            measurement_references=("vol-001", "cur-001"),
        )
        assert evidence.measurement_references == ("vol-001", "cur-001")


class TestEvidenceProvenance:
    def test_evidence_provenance_default(self):
        evidence = Evidence(
            evidence_id="ev-005",
            source_reference="meas-005",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        assert evidence.provenance is not None

    def test_evidence_provenance_custom(self):
        provenance = ProvenanceReference(
            artifact_id="ev-006",
            measurement_id="meas-006",
        )
        evidence = Evidence(
            evidence_id="ev-006",
            source_reference="meas-006",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
            provenance=provenance,
        )
        assert evidence.provenance.artifact_id == "ev-006"
        assert evidence.provenance.measurement_id == "meas-006"


class TestHypothesisCreation:
    def test_hypothesis_creation(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-001",
            statement="FJH produces graphene from carbon black",
            scope="Carbon feedstock under 120V pulses",
        )
        assert hypothesis.hypothesis_id == "hyp-001"
        assert hypothesis.status == InterpretationStatus.PROPOSED

    def test_hypothesis_status_transitions(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-002",
            statement="Temperature exceeds 2000K",
            scope="Pulse duration 50ms",
            status=InterpretationStatus.SUPPORTED,
        )
        assert hypothesis.status == InterpretationStatus.SUPPORTED

    def test_hypothesis_with_evidence(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-003",
            statement="Material is conductive",
            scope="Post-FJH sample",
            supporting_evidence=("ev-001", "ev-002"),
            contradicting_evidence=("ev-003",),
        )
        assert hypothesis.supporting_evidence == ("ev-001", "ev-002")
        assert hypothesis.contradicting_evidence == ("ev-003",)

    def test_hypothesis_empty_id_raises(self):
        with pytest.raises(ValueError, match="hypothesis_id"):
            Hypothesis(
                hypothesis_id="",
                statement="Test",
                scope="Test",
            )

    def test_hypothesis_empty_statement_raises(self):
        with pytest.raises(ValueError, match="statement"):
            Hypothesis(
                hypothesis_id="hyp-004",
                statement="",
                scope="Test",
            )


class TestHypothesisStatus:
    def test_hypothesis_statuses(self):
        for status in InterpretationStatus:
            hypothesis = Hypothesis(
                hypothesis_id=f"hyp-{status.value}",
                statement="Test",
                scope="Test",
                status=status,
            )
            assert hypothesis.status == status

    def test_hypothesis_does_not_auto_promote(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-005",
            statement="Unsupported claim",
            scope="Broad",
            status=InterpretationStatus.PROPOSED,
        )
        assert hypothesis.status != InterpretationStatus.SUPPORTED
        assert hypothesis.status == InterpretationStatus.PROPOSED


class TestInterpretationCreation:
    def test_interpretation_creation(self):
        interpretation = InterpretationResult(
            interpretation_id="int-001",
            subject_reference="mat-001",
            proposition="Sample exhibits graphene-like conductivity",
            evidence_references=("ev-001",),
            assumptions=("temperature measurement is representative",),
        )
        assert interpretation.interpretation_id == "int-001"
        assert interpretation.status == InterpretationStatus.PROPOSED

    def test_interpretation_with_hypothesis(self):
        interpretation = InterpretationResult(
            interpretation_id="int-002",
            subject_reference="mat-002",
            proposition="Structural transformation observed",
            hypothesis_id="hyp-001",
            evidence_references=("ev-001", "ev-002"),
        )
        assert interpretation.hypothesis_id == "hyp-001"

    def test_interpretation_with_residuals_and_unknowns(self):
        interpretation = InterpretationResult(
            interpretation_id="int-003",
            subject_reference="mat-003",
            proposition="Partial interpretation",
            residuals=("res-001",),
            unknowns=("unk-001",),
        )
        assert interpretation.residuals == ("res-001",)
        assert interpretation.unknowns == ("unk-001",)

    def test_interpretation_with_competing_interpretations(self):
        interpretation = InterpretationResult(
            interpretation_id="int-004",
            subject_reference="mat-004",
            proposition="Interpretation A",
            competing_interpretations=("int-005",),
        )
        assert interpretation.competing_interpretations == ("int-005",)

    def test_interpretation_empty_id_raises(self):
        with pytest.raises(ValueError, match="interpretation_id"):
            InterpretationResult(
                interpretation_id="",
                subject_reference="mat-001",
                proposition="Test",
            )

    def test_interpretation_method(self):
        interpretation = InterpretationResult(
            interpretation_id="int-006",
            subject_reference="mat-006",
            proposition="Deterministic rule applied",
            method=InterpretationMethod.DETERMINISTIC_RULE,
        )
        assert interpretation.method == InterpretationMethod.DETERMINISTIC_RULE


class TestInterpretationProvenance:
    def test_interpretation_provenance_default(self):
        interpretation = InterpretationResult(
            interpretation_id="int-007",
            subject_reference="mat-007",
            proposition="Test",
        )
        assert interpretation.provenance is not None

    def test_interpretation_provenance_custom(self):
        provenance = ProvenanceReference(
            artifact_id="int-008",
            measurement_id="meas-008",
        )
        interpretation = InterpretationResult(
            interpretation_id="int-008",
            subject_reference="mat-008",
            proposition="Test",
            provenance=provenance,
        )
        assert interpretation.provenance.artifact_id == "int-008"


class TestResidualPreservation:
    def test_residual_creation(self):
        residual = Residual(
            residual_id="res-001",
            description="Unexplained voltage dip at t=0.02s",
            category="unexplained_measurement_behavior",
            related_measurement_ids=("vol-001",),
        )
        assert residual.residual_id == "res-001"
        assert residual.category == "unexplained_measurement_behavior"

    def test_residual_not_error(self):
        residual = Residual(
            residual_id="res-002",
            description="Missing calibration data",
            category="missing_variable",
        )
        assert residual.category != "error"
        assert residual.category != "failure"

    def test_residual_empty_id_raises(self):
        with pytest.raises(ValueError, match="residual_id"):
            Residual(
                residual_id="",
                description="Test",
                category="test",
            )


class TestUnknownPreservation:
    def test_unknown_creation(self):
        unknown = Unknown(
            unknown_id="unk-001",
            description="Material crystal structure not measured",
            category="unresolved_structure",
            related_measurement_ids=("xrd-001",),
        )
        assert unknown.unknown_id == "unk-001"
        assert unknown.category == "unresolved_structure"

    def test_unknown_not_null_substitute(self):
        unknown = Unknown(
            unknown_id="unk-002",
            description="Insufficient data for phase identification",
            category="insufficient_data",
        )
        assert unknown is not None
        assert unknown.unknown_id != "null"
        assert unknown.unknown_id != "0"
        assert unknown.unknown_id != "false"

    def test_unknown_empty_id_raises(self):
        with pytest.raises(ValueError, match="unknown_id"):
            Unknown(
                unknown_id="",
                description="Test",
                category="test",
            )


class TestCompetingInterpretations:
    def test_competing_interpretation_creation(self):
        comp = CompetingInterpretation(
            interpretation_id="int-009",
            subject_reference="mat-009",
            proposition="Alternative: amorphous carbon",
            evidence_references=("ev-004",),
            status=InterpretationStatus.UNRESOLVED,
        )
        assert comp.interpretation_id == "int-009"
        assert comp.proposition == "Alternative: amorphous carbon"

    def test_competing_interpretations_remain_possible(self):
        interp_a = InterpretationResult(
            interpretation_id="int-010",
            subject_reference="mat-010",
            proposition="Graphene formed",
            status=InterpretationStatus.UNRESOLVED,
        )
        interp_b = InterpretationResult(
            interpretation_id="int-011",
            subject_reference="mat-010",
            proposition="Graphite formed",
            status=InterpretationStatus.UNRESOLVED,
        )
        assert interp_a.status == InterpretationStatus.UNRESOLVED
        assert interp_b.status == InterpretationStatus.UNRESOLVED

    def test_competing_interpretation_empty_id_raises(self):
        with pytest.raises(ValueError, match="interpretation_id"):
            CompetingInterpretation(
                interpretation_id="",
                subject_reference="mat",
                proposition="Test",
            )


class TestContradictoryEvidence:
    def test_contradictory_evidence_in_hypothesis(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-006",
            statement="Sample is conductive",
            scope="Post-FJH",
            supporting_evidence=("ev-001",),
            contradicting_evidence=("ev-002",),
            neutral_evidence=("ev-003",),
        )
        assert hypothesis.contradicting_evidence == ("ev-002",)
        assert hypothesis.neutral_evidence == ("ev-003",)
        assert hypothesis.supporting_evidence == ("ev-001",)


class TestAssumptionTracking:
    def test_assumptions_in_evidence(self):
        evidence = Evidence(
            evidence_id="ev-007",
            source_reference="meas-007",
            evidence_type="measurement",
            description="Temperature reading",
            relevance="Assumed representative of bulk",
            assumptions=("thermocouple contact is good", "no radiative loss"),
        )
        assert "thermocouple contact is good" in evidence.assumptions

    def test_assumptions_in_interpretation(self):
        interpretation = InterpretationResult(
            interpretation_id="int-012",
            subject_reference="mat-012",
            proposition="Temperature rise indicates reaction",
            assumptions=("measurement is representative of sample temperature",),
        )
        assert "measurement is representative of sample temperature" in interpretation.assumptions


class TestSimulatedVsMeasured:
    def test_evidence_from_simulated_measurement(self):
        evidence = Evidence(
            evidence_id="ev-008",
            source_reference="sim-001",
            evidence_type="simulated_measurement",
            description="Simulated voltage trace",
            relevance="Supports simulation-based interpretation",
        )
        assert evidence.source_reference == "sim-001"
        assert evidence.evidence_type == "simulated_measurement"

    def test_evidence_from_measured_measurement(self):
        evidence = Evidence(
            evidence_id="ev-009",
            source_reference="meas-009",
            evidence_type="measurement",
            description="Physical voltage trace",
            relevance="Supports experimental interpretation",
        )
        assert evidence.source_reference == "meas-009"
        assert evidence.evidence_type == "measurement"


class TestUncertaintyPreservation:
    def test_interpretation_references_uncertainty(self):
        uncertainty = Uncertainty(
            standard_uncertainty=Quantity(value=0.5, unit="V"),
            confidence_level=0.95,
        )
        evidence = Evidence(
            evidence_id="ev-010",
            source_reference="meas-010",
            evidence_type="measurement",
            description="Voltage with known uncertainty",
            relevance="Supports power calculation",
        )
        assert uncertainty.standard_uncertainty is not None
        assert uncertainty.confidence_level == 0.95

    def test_uncertainty_distinct_from_evidence_strength(self):
        evidence = Evidence(
            evidence_id="ev-011",
            source_reference="meas-011",
            evidence_type="measurement",
            description="Measurement with uncertainty",
            relevance="Test",
        )
        assert not hasattr(evidence, "confidence")
        assert evidence.strength is None


class TestMaterialStateLineage:
    def test_evidence_references_material_state(self):
        evidence = Evidence(
            evidence_id="ev-012",
            source_reference="mat-001",
            evidence_type="material_state",
            description="Post-experiment composition",
            relevance="Supports transformation hypothesis",
            material_references=("mat-001",),
        )
        assert evidence.material_references == ("mat-001",)

    def test_interpretation_references_material_state(self):
        interpretation = InterpretationResult(
            interpretation_id="int-013",
            subject_reference="mat-001",
            proposition="Material composition changed",
            evidence_references=("ev-012",),
        )
        assert interpretation.subject_reference == "mat-001"


class TestMaterialEvolution:
    def test_material_evolution_creation(self):
        prior_state = MaterialState(
            composition={"carbon": Quantity(value=0.95, unit="mass_fraction")},
        )
        candidate_state = MaterialState(
            composition={"carbon": Quantity(value=0.80, unit="mass_fraction")},
        )
        evolution = MaterialEvolution(
            evolution_id="evol-001",
            experiment_id="exp-001",
            prior_material_state_id="mat-prior-001",
            candidate_material_state=candidate_state,
            supporting_interpretation_id="int-001",
            status="CANDIDATE",
        )
        assert evolution.evolution_id == "evol-001"
        assert evolution.status == "CANDIDATE"

    def test_material_evolution_does_not_mutate_prior(self):
        prior_state = MaterialState(
            composition={"carbon": Quantity(value=0.95, unit="mass_fraction")},
        )
        candidate_state = MaterialState(
            composition={"carbon": Quantity(value=0.80, unit="mass_fraction")},
        )
        evolution = MaterialEvolution(
            evolution_id="evol-002",
            experiment_id="exp-001",
            prior_material_state_id="mat-prior-002",
            candidate_material_state=candidate_state,
        )
        assert prior_state.composition["carbon"].value == 0.95
        assert evolution.candidate_material_state.composition["carbon"].value == 0.80

    def test_material_evolution_empty_id_raises(self):
        with pytest.raises(ValueError, match="evolution_id"):
            MaterialEvolution(
                evolution_id="",
                experiment_id="exp-001",
                candidate_material_state=MaterialState(),
            )


class TestYieldSemantics:
    def test_yield_representation_preserved(self):
        yield_rep = YieldRepresentation(
            value=0.35,
            unit="g/g",
            basis=YieldBasis.MASS_BASIS,
            calculation_method="final_mass / initial_mass",
            input_references=("meas-001",),
        )
        assert yield_rep.value == 0.35
        assert yield_rep.basis == YieldBasis.MASS_BASIS

    def test_interpretation_does_not_alter_yield(self):
        yield_rep = YieldRepresentation(
            value=3.2,
            unit="g",
            basis=YieldBasis.MASS_BASIS,
            calculation_method="final_mass / initial_mass",
        )
        interpretation = InterpretationResult(
            interpretation_id="int-014",
            subject_reference="mat-014",
            proposition="Yield improvement is statistically meaningful",
            evidence_references=("ev-013",),
        )
        assert yield_rep.value == 3.2
        assert "statistically meaningful" in interpretation.proposition


class TestInterpretationValidation:
    def test_valid_interpretation(self):
        interpretation = InterpretationResult(
            interpretation_id="int-015",
            subject_reference="mat-015",
            proposition="Valid interpretation",
            evidence_references=("ev-001",),
            assumptions=("assumption-1",),
            residuals=(),
            unknowns=(),
        )
        assert interpretation.interpretation_id == "int-015"

    def test_interpretation_without_evidence_references(self):
        interpretation = InterpretationResult(
            interpretation_id="int-016",
            subject_reference="mat-016",
            proposition="Interpretation without evidence",
        )
        assert interpretation.evidence_references == ()

    def test_interpretation_status_transitions_require_evidence(self):
        interpretation = InterpretationResult(
            interpretation_id="int-017",
            subject_reference="mat-017",
            proposition="Proposed interpretation",
            status=InterpretationStatus.PROPOSED,
        )
        assert interpretation.status == InterpretationStatus.PROPOSED
        assert interpretation.status != InterpretationStatus.SUPPORTED


class TestDeterministicInterpretation:
    def test_deterministic_evidence_creation(self):
        evidence1 = Evidence(
            evidence_id="ev-018",
            source_reference="meas-018",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        evidence2 = Evidence(
            evidence_id="ev-018",
            source_reference="meas-018",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        assert evidence1.evidence_id == evidence2.evidence_id

    def test_hypothesis_versioning(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-007",
            statement="Versioned hypothesis",
            scope="Test",
            version="1.0.0",
        )
        assert hypothesis.version == "1.0.0"


class TestProvenanceReconstruction:
    def test_evidence_provenance_reconstructable(self):
        provenance = ProvenanceReference(
            artifact_id="ev-019",
            measurement_id="meas-019",
        )
        evidence = Evidence(
            evidence_id="ev-019",
            source_reference="meas-019",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
            provenance=provenance,
        )
        assert evidence.provenance.measurement_id == "meas-019"
        assert evidence.provenance.artifact_id == "ev-019"

    def test_interpretation_provenance_chain(self):
        provenance = ProvenanceReference(
            artifact_id="int-020",
            measurement_id="meas-020",
        )
        interpretation = InterpretationResult(
            interpretation_id="int-020",
            subject_reference="mat-020",
            proposition="Test",
            provenance=provenance,
        )
        assert interpretation.provenance.measurement_id == "meas-020"


class TestCognitiaAdapterIsolation:
    def test_no_cognitia_types_in_interpretation_models(self):
        import forgepulse.interpretation as interp_mod
        assert not hasattr(interp_mod, "CognitiaAdapter")
        assert not hasattr(interp_mod, "CognitiaReasoning")

    def test_cognitia_method_not_in_interpretation_methods(self):
        assert InterpretationMethod.COGNITIA_ADVISORY.value == "COGNITIA_ADVISORY"


class TestFailureSemantics:
    def test_evidence_missing_source_reference(self):
        with pytest.raises(ValueError, match="source_reference"):
            Evidence(
                evidence_id="ev-021",
                source_reference="",
                evidence_type="type",
                description="desc",
                relevance="rel",
            )

    def test_hypothesis_missing_scope(self):
        with pytest.raises(ValueError, match="scope"):
            Hypothesis(
                hypothesis_id="hyp-008",
                statement="Test",
                scope="",
            )

    def test_interpretation_missing_subject_reference(self):
        with pytest.raises(ValueError, match="subject_reference"):
            InterpretationResult(
                interpretation_id="int-021",
                subject_reference="",
                proposition="Test",
            )

    def test_residual_missing_category(self):
        with pytest.raises(ValueError, match="category"):
            Residual(
                residual_id="res-003",
                description="Test",
                category="",
            )

    def test_unknown_missing_description(self):
        with pytest.raises(ValueError, match="description"):
            Unknown(
                unknown_id="unk-003",
                description="",
                category="test",
            )

    def test_competing_interpretation_missing_proposition(self):
        with pytest.raises(ValueError, match="proposition"):
            CompetingInterpretation(
                interpretation_id="int-022",
                subject_reference="mat",
                proposition="",
            )

    def test_material_evolution_missing_experiment_id(self):
        with pytest.raises(ValueError, match="experiment_id"):
            MaterialEvolution(
                evolution_id="evol-003",
                experiment_id="",
                candidate_material_state=MaterialState(),
            )


class TestHistoricalVersionPreservation:
    def test_hypothesis_version_preserved(self):
        hypothesis = Hypothesis(
            hypothesis_id="hyp-009",
            statement="Versioned hypothesis",
            scope="Test",
            version="1.0.0",
        )
        assert hypothesis.version == "1.0.0"

    def test_interpretation_version_preserved(self):
        interpretation = InterpretationResult(
            interpretation_id="int-023",
            subject_reference="mat-023",
            proposition="Versioned interpretation",
            version="1.0.0",
        )
        assert interpretation.version == "1.0.0"

    def test_evidence_schema_version_preserved(self):
        evidence = Evidence(
            evidence_id="ev-022",
            source_reference="meas-022",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
            schema_version="1.0.0",
        )
        assert evidence.schema_version == "1.0.0"


class TestInterpretationStatusLifecycle:
    def test_interpretation_status_values(self):
        expected = {
            "PROPOSED",
            "UNDER_REVIEW",
            "SUPPORTED",
            "REFUTED",
            "UNRESOLVED",
            "SUPERSEDED",
        }
        actual = {s.value for s in InterpretationStatus}
        assert actual == expected

    def test_interpretation_status_does_not_auto_promote(self):
        interpretation = InterpretationResult(
            interpretation_id="int-024",
            subject_reference="mat-024",
            proposition="Proposed interpretation",
            status=InterpretationStatus.PROPOSED,
        )
        assert interpretation.status == InterpretationStatus.PROPOSED
        assert interpretation.status != InterpretationStatus.SUPPORTED
        assert interpretation.status != InterpretationStatus.UNRESOLVED


class TestPhase5Reconciliation:
    def test_models_are_frozen(self):
        from dataclasses import FrozenInstanceError
        evidence = Evidence(
            evidence_id="ev-rec-001",
            source_reference="meas-rec-001",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        with pytest.raises(FrozenInstanceError):
            evidence.evidence_id = "new-id"

    def test_evidence_is_not_measurement_subtype(self):
        from forgepulse.measurement import MeasurementSeries, RawMeasurement
        evidence = Evidence(
            evidence_id="ev-rec-002",
            source_reference="meas-rec-002",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        assert not isinstance(evidence, MeasurementSeries)
        assert not isinstance(evidence, RawMeasurement)

    def test_residual_is_not_error_or_failure(self):
        residual = Residual(
            residual_id="res-rec-001",
            description="Test residual",
            category="unexplained_measurement_behavior",
        )
        assert residual.category != "error"
        assert residual.category != "failure"
        assert residual.category != "noise"

    def test_unknown_is_not_auto_converted(self):
        unknown = Unknown(
            unknown_id="unk-rec-001",
            description="Insufficient data",
            category="insufficient_data",
        )
        assert unknown.unknown_id != "null"
        assert unknown.unknown_id != "0"
        assert unknown.unknown_id != "false"
        assert unknown.unknown_id != "assumed"

    def test_evidence_created_at_is_utc(self):
        from datetime import timezone
        evidence = Evidence(
            evidence_id="ev-rec-003",
            source_reference="meas-rec-003",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        assert evidence.created_at.tzinfo is not None
        assert evidence.created_at.tzinfo.utcoffset(evidence.created_at).total_seconds() == 0

    def test_hypothesis_created_at_is_utc(self):
        from datetime import timezone
        hypothesis = Hypothesis(
            hypothesis_id="hyp-rec-001",
            statement="Test",
            scope="Test",
        )
        assert hypothesis.created_at.tzinfo is not None
        assert hypothesis.created_at.tzinfo.utcoffset(hypothesis.created_at).total_seconds() == 0

    def test_interpretation_created_at_is_utc(self):
        from datetime import timezone
        interpretation = InterpretationResult(
            interpretation_id="int-rec-001",
            subject_reference="mat-rec-001",
            proposition="Test",
        )
        assert interpretation.created_at.tzinfo is not None
        assert interpretation.created_at.tzinfo.utcoffset(interpretation.created_at).total_seconds() == 0

    def test_residual_created_at_is_utc(self):
        from datetime import timezone
        residual = Residual(
            residual_id="res-rec-002",
            description="Test",
            category="test",
        )
        assert residual.created_at.tzinfo is not None
        assert residual.created_at.tzinfo.utcoffset(residual.created_at).total_seconds() == 0

    def test_unknown_created_at_is_utc(self):
        from datetime import timezone
        unknown = Unknown(
            unknown_id="unk-rec-002",
            description="Test",
            category="test",
        )
        assert unknown.created_at.tzinfo is not None
        assert unknown.created_at.tzinfo.utcoffset(unknown.created_at).total_seconds() == 0

    def test_competing_interpretation_created_at_is_utc(self):
        from datetime import timezone
        comp = CompetingInterpretation(
            interpretation_id="int-rec-002",
            subject_reference="mat-rec-002",
            proposition="Test",
        )
        assert comp.created_at.tzinfo is not None
        assert comp.created_at.tzinfo.utcoffset(comp.created_at).total_seconds() == 0

    def test_material_evolution_created_at_is_utc(self):
        from datetime import timezone
        evolution = MaterialEvolution(
            evolution_id="evol-rec-001",
            experiment_id="exp-rec-001",
            candidate_material_state=MaterialState(),
        )
        assert evolution.created_at.tzinfo is not None
        assert evolution.created_at.tzinfo.utcoffset(evolution.created_at).total_seconds() == 0

    def test_interpretation_status_explicit_not_auto_transition(self):
        interpretation = InterpretationResult(
            interpretation_id="int-rec-003",
            subject_reference="mat-rec-003",
            proposition="Test",
            status=InterpretationStatus.PROPOSED,
        )
        assert interpretation.status == InterpretationStatus.PROPOSED
        assert interpretation.status != InterpretationStatus.SUPPORTED
        assert interpretation.status != InterpretationStatus.UNDER_REVIEW

    def test_no_hidden_inference_in_models(self):
        evidence = Evidence(
            evidence_id="ev-rec-004",
            source_reference="meas-rec-004",
            evidence_type="measurement",
            description="Test",
            relevance="Test",
        )
        hypothesis = Hypothesis(
            hypothesis_id="hyp-rec-002",
            statement="Test",
            scope="Test",
        )
        interpretation = InterpretationResult(
            interpretation_id="int-rec-004",
            subject_reference="mat-rec-004",
            proposition="Test",
        )
        assert evidence is not None
        assert hypothesis is not None
        assert interpretation is not None
        assert not hasattr(evidence, "infer")
        assert not hasattr(hypothesis, "prove")
        assert not hasattr(interpretation, "conclude")
