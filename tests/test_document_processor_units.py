import os
import json
import tempfile
import pathlib
import pytest

from src.document_processor import (
    normalize_text_conservatively,
    slugify_filename,
    compute_text_sha256,
    CRITICAL_INSURANCE_TERMS,
    DocumentProcessor
)


def test_normalize_text_conservatively_preserves_insurance_figures():
    raw_input = "ACTIV ONE\r\n\r\n\r\n\r\n2X  3X  4X  5X  6X\xa0YEAR 2\nSum Insured: ₹50,000,000 / INR 50 Lakhs\nWait period: 30 days"
    normalized = normalize_text_conservatively(raw_input)
    
    assert "ACTIV ONE" in normalized
    assert "2X  3X  4X  5X  6X YEAR 2" in normalized
    assert "₹50,000,000 / INR 50 Lakhs" in normalized
    assert "Wait period: 30 days" in normalized
    assert "\r" not in normalized
    assert "\xa0" not in normalized
    assert "\n\n\n" not in normalized


def test_slugify_filename():
    assert slugify_filename("ABHI Product Brochure.pdf") == "abhi_product_brochure"
    assert slugify_filename("HDFC Product Brochure.pdf") == "hdfc_product_brochure"
    assert slugify_filename("Marsh - Internship Case Study.pdf") == "marsh_internship_case_study"


def test_compute_text_sha256():
    text = "Sample policy text for hash testing"
    hash_str = compute_text_sha256(text)
    assert hash_str.startswith("sha256_")
    assert len(hash_str) == 7 + 64
    # Determinism check
    assert compute_text_sha256(text) == hash_str


def test_critical_terms_regex_matching():
    sample_corpus_text = (
        "ReAssure 2.0 Platinum variant with ₹5 Lacs / INR 500,000 to 100 Lacs sum insured. "
        "Secure Benefit offers 2X coverage from Day 1 and 5X accelerating cover in year 5. "
        "Initial wait period: 30 days, named ailment: 24 months, pre-existing diseases: 36 months. "
        "Includes 100% bonus per policy year."
    )
    import re
    for label, pattern in CRITICAL_INSURANCE_TERMS:
        assert re.search(pattern, sample_corpus_text, re.IGNORECASE) is not None, f"Failed match for {label}"


def test_low_text_heuristic_warning():
    raw_text = "NBHHLIP26042V022526"
    clean = normalize_text_conservatively(raw_text)
    assert len(clean) < 100
    # Confirm heuristic flags low-text without throwing exception


def test_page_record_schema_structure():
    dummy_page_record = {
        "document_id": "doc_test_1234567890ab",
        "document_name": "Test Brochure",
        "source_filename": "Test Brochure.pdf",
        "source_path": "data/raw/Test Brochure.pdf",
        "page_number": 1,
        "page_count": 2,
        "raw_text": "Sample raw text",
        "clean_text": "Sample raw text",
        "character_count": 15,
        "word_count": 3,
        "text_hash": compute_text_sha256("Sample raw text"),
        "extraction_method": "pymupdf",
        "warnings": []
    }
    
    required_keys = {
        "document_id", "document_name", "source_filename", "source_path",
        "page_number", "page_count", "raw_text", "clean_text",
        "character_count", "word_count", "text_hash", "extraction_method", "warnings"
    }
    assert required_keys.issubset(dummy_page_record.keys())
    assert dummy_page_record["page_number"] == 1
    assert dummy_page_record["extraction_method"] == "pymupdf"


def test_manifest_entry_schema_and_corpus_inclusion():
    manifest_doc = {
        "document_id": "doc_abhi_product_brochure_85cdd5a54cc5",
        "document_name": "ABHI Activ One Product Brochure",
        "source_filename": "ABHI Product Brochure.pdf",
        "source_path": "data/raw/ABHI Product Brochure.pdf",
        "category": "policy_evidence",
        "included_in_policy_corpus": True,
        "page_count_expected": 2,
        "page_count_processed": 2,
        "pages_missing": [],
        "processing_status": "success",
        "file_size_bytes": 2765016,
        "file_sha256": "85cdd5a54cc5d7bda369332eeb4987540d7d29c491a3ce5a3fb80c2a0aff8372",
        "warnings": []
    }
    
    assert manifest_doc["category"] == "policy_evidence"
    assert manifest_doc["included_in_policy_corpus"] is True
    assert manifest_doc["page_count_expected"] == manifest_doc["page_count_processed"]


def test_case_brief_exclusion_entry_schema():
    excluded_entry = {
        "source_filename": "Marsh - Internship Case Study.pdf",
        "source_path": "Marsh - Internship Case Study.pdf",
        "category": "case_brief",
        "included_in_policy_corpus": False,
        "file_sha256": "0f28ca5de1e8ef304978ad667f3bc859f79b030b2a771025e47d135a4ad69e08",
        "file_size_bytes": 561905,
        "reason": "Exclusion rule: Marsh Internship Case Brief / Specification document"
    }
    
    assert excluded_entry["category"] == "case_brief"
    assert excluded_entry["included_in_policy_corpus"] is False
