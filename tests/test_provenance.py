"""Tests for provenance."""

from __future__ import annotations

from datetime import datetime, timezone

from forgepulse.provenance import LineageReference, ProvenanceRecord


class TestProvenanceRecord:
    def test_provenance_record_creation(self):
        record = ProvenanceRecord(
            artifact_id="derived-001",
            artifact_type="derived_measurement",
            source_ids=(LineageReference(artifact_id="meas-001", artifact_type="raw_measurement"),),
            transformation="average",
        )
        assert record.artifact_id == "derived-001"
        assert record.source_ids[0].artifact_id == "meas-001"
        assert record.transformation == "average"

    def test_provenance_record_utc_timestamp(self):
        record = ProvenanceRecord(artifact_id="art-001", artifact_type="measurement")
        assert record.created_at.tzinfo is not None

    def test_provenance_record_deterministic_ordering(self):
        sources = (
            LineageReference(artifact_id="b-001", artifact_type="measurement"),
            LineageReference(artifact_id="a-001", artifact_type="measurement"),
        )
        record = ProvenanceRecord(
            artifact_id="art-002",
            artifact_type="measurement",
            source_ids=sources,
        )
        assert record.source_ids[0].artifact_id == "b-001"
        assert record.source_ids[1].artifact_id == "a-001"
