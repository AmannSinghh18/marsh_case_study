import os
import json
import pytest
from src.matrix_builder import (
    verify_numeric_tokens,
    verify_record_provenance,
    VALID_CATEGORIES,
    VALID_CLAIM_TYPES,
    VALID_EVIDENCE_STRENGTHS,
    VALID_REVIEW_STATUSES
)


def test_schema_controlled_vocabularies():
    assert "coverage" in VALID_CATEGORIES
    assert "recharge_restore" in VALID_CATEGORIES
    assert "waiting_period" in VALID_CATEGORIES
    assert "direct_benefit" in VALID_CLAIM_TYPES
    assert "optional_addon" in VALID_CLAIM_TYPES
    assert "direct" in VALID_EVIDENCE_STRENGTHS
    assert "verified" in VALID_REVIEW_STATUSES
    assert "review_required" in VALID_REVIEW_STATUSES
    assert "rejected" in VALID_REVIEW_STATUSES


def test_numeric_token_verification_pass():
    record = {
        "value": "2X",
        "waiting_period": "30 days",
        "variant": "VIP+",
        "source_text": "Presenting Activ One VIP+ plan with 2X coverage and initial wait period of 30 days."
    }
    ok, issues = verify_numeric_tokens(record)
    assert ok is True
    assert len(issues) == 0


def test_numeric_token_verification_fail_when_missing():
    record = {
        "value": "10X",
        "waiting_period": "36 months",
        "source_text": "Covered up to 2X with initial wait period of 30 days."
    }
    ok, issues = verify_numeric_tokens(record)
    assert ok is False
    assert any("10X" in i for i in issues)
    assert any("36 months" in i for i in issues)


def test_hard_provenance_verification_pass():
    page_map = {
        ("HDFC Product Brochure.pdf", 2): "Secure Beneﬁt 2X coverage from Day 1 Your base cover doubles instantly, at no extra cost"
    }
    record = {
        "source_document": "HDFC Product Brochure.pdf",
        "source_page": 2,
        "source_text": "Secure Beneﬁt 2X coverage from Day 1 Your base cover doubles instantly, at no extra cost",
        "value": "2X",
        "is_optional": False,
        "addon_name": None
    }
    ok, issues = verify_record_provenance(record, page_map)
    assert ok is True
    assert len(issues) == 0


def test_hard_provenance_verification_fail_on_text_mismatch():
    page_map = {
        ("HDFC Product Brochure.pdf", 2): "Secure Beneﬁt 2X coverage from Day 1"
    }
    record = {
        "source_document": "HDFC Product Brochure.pdf",
        "source_page": 2,
        "source_text": "Fabricated non-existent quotation text not in brochure",
        "value": "2X",
        "is_optional": False,
        "addon_name": None
    }
    ok, issues = verify_record_provenance(record, page_map)
    assert ok is False
    assert any("verbatim match" in i for i in issues)


def test_derived_evidence_rules_enforcement():
    page_map = {
        ("HDFC Product Brochure.pdf", 2): "Secure Beneﬁt 2X coverage from Day 1"
    }
    # Derived record without derived_from/derivation should fail provenance check
    record = {
        "source_document": "HDFC Product Brochure.pdf",
        "source_page": 2,
        "source_text": "Secure Beneﬁt 2X coverage from Day 1",
        "evidence_strength": "derived",
        "derived_from": None,
        "derivation": None,
        "is_optional": False,
        "addon_name": None
    }
    ok, issues = verify_record_provenance(record, page_map)
    assert ok is False
    assert any("derived" in i for i in issues)


def test_optional_addon_schema_enforcement():
    page_map = {
        ("Care Health Product Brochure.pdf", 3): "Care OPD 1. Max 4 physical consultations"
    }
    record = {
        "source_document": "Care Health Product Brochure.pdf",
        "source_page": 3,
        "source_text": "Care OPD 1. Max 4 physical consultations",
        "is_optional": True,
        "addon_name": None  # Missing addon_name
    }
    ok, issues = verify_record_provenance(record, page_map)
    assert ok is False
    assert any("addon_name" in i for i in issues)
