"""
Unit Tests for Claim-Level Audit Engine (Phase 4 Stage 4K & Section 55 Fixtures)
"""

import pytest
import os
import json
from src.audit.schemas import ExtractedClaim
from src.audit.audit_engine import run_claim_audit, execute_full_audit
from src.audit.evidence_checker import load_canonical_evidence_matrix


def test_fixture_1_correct_evidence_backed_statement():
    claims = [
        ExtractedClaim(
            claim_id="TEST-FIX-01",
            claim_text="Care Health provides 60 days pre and 180 days post hospitalization reimbursement.",
            claim_type="coverage",
            source_output="test",
            evidence_ids=["CARE-002"],
            extracted_numbers=["60 days", "180 days"],
            extracted_conditions=[]
        )
    ]
    report = run_claim_audit(claims)
    assert report.audited_claims[0].audit_status == "PASS"


def test_fixture_2_incorrect_number_fails():
    claims = [
        ExtractedClaim(
            claim_id="TEST-FIX-02",
            claim_text="Care Health provides 90 days pre-hospitalization reimbursement.",
            claim_type="coverage",
            source_output="test",
            evidence_ids=["CARE-002"],
            extracted_numbers=["90 days"],
            extracted_conditions=[]
        )
    ]
    report = run_claim_audit(claims)
    assert report.audited_claims[0].audit_status == "FAIL"
    assert "90" in report.audited_claims[0].audit_reason


def test_fixture_3_omitted_qualifier_triggers_review():
    claims = [
        ExtractedClaim(
            claim_id="TEST-FIX-03",
            claim_text="Policy provides maternity coverage.",
            claim_type="coverage",
            source_output="test",
            evidence_ids=["CARE-007"],
            extracted_numbers=[],
            extracted_conditions=[]
        )
    ]
    report = run_claim_audit(claims)
    assert report.audited_claims[0].audit_status in ["REVIEW", "FAIL"]


def test_fixture_4_unsupported_feature_fails():
    claims = [
        ExtractedClaim(
            claim_id="TEST-FIX-04",
            claim_text="Policy covers space travel hospitalizations.",
            claim_type="coverage",
            source_output="test",
            evidence_ids=["INVALID-999"],
            extracted_numbers=[],
            extracted_conditions=[]
        )
    ]
    report = run_claim_audit(claims)
    assert report.audited_claims[0].audit_status == "FAIL"


def test_fixture_5_multiple_evidence_ids_pass():
    claims = [
        ExtractedClaim(
            claim_id="TEST-FIX-05",
            claim_text="Network hospital access available.",
            claim_type="coverage",
            source_output="test",
            evidence_ids=["CARE-008", "NIVA-007B"],
            extracted_numbers=[],
            extracted_conditions=[]
        )
    ]
    report = run_claim_audit(claims)
    assert report.audited_claims[0].audit_status == "PASS"


def test_O_pitch_content_is_auditable():
    report_dict = execute_full_audit()
    assert report_dict["total_claims_audited"] > 0
    assert report_dict["fail_count"] == 0
