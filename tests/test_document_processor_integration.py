import os
import json
import pathlib
import pytest
from src.document_processor import DocumentProcessor

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = WORKSPACE_ROOT / "data" / "raw"
PROCESSED_DIR = WORKSPACE_ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def processed_corpus():
    """Run processor pipeline against real corpus and yield processed results."""
    processor = DocumentProcessor(input_dir=RAW_DIR, output_dir=PROCESSED_DIR, force=True)
    processor.stage_raw_data()
    success = processor.process()
    assert success is True, "DocumentProcessor pipeline failed during integration test setup!"
    
    with open(PROCESSED_DIR / "policy_pages.json", "r", encoding="utf-8") as f:
        pages = json.load(f)
        
    with open(PROCESSED_DIR / "document_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(PROCESSED_DIR / "extraction_validation_report.json", "r", encoding="utf-8") as f:
        report = json.load(f)
        
    return {
        "pages": pages,
        "manifest": manifest,
        "report": report
    }


def test_end_to_end_policy_corpus_ingestion(processed_corpus):
    pages = processed_corpus["pages"]
    manifest = processed_corpus["manifest"]
    report = processed_corpus["report"]

    # 1. Overall Validation Status
    assert report["overall_status"] == "PASSED"
    assert report["total_policy_documents_processed"] == 4
    assert report["total_policy_pages_processed"] == 24
    assert report["total_missing_pages"] == 0
    assert report["total_duplicate_pages"] == 0
    assert report["total_empty_pages"] == 0
    assert report["total_suspicious_low_text_pages"] == 2

    # 2. Critical Terms Validation Check
    assert report["critical_term_validation"]["all_terms_detected"] is True

    # 3. Manifest Verification
    policy_docs = manifest["documents"]
    excluded_docs = manifest["excluded_documents"]

    assert len(policy_docs) == 4
    for doc in policy_docs:
        assert doc["category"] == "policy_evidence"
        assert doc["included_in_policy_corpus"] is True
        assert doc["processing_status"] == "success"
        assert doc["page_count_expected"] == doc["page_count_processed"]

    # Case brief exclusion check
    assert len(excluded_docs) >= 1
    case_brief_entries = [d for d in excluded_docs if d["category"] == "case_brief"]
    assert len(case_brief_entries) == 1
    assert case_brief_entries[0]["included_in_policy_corpus"] is False
    assert "Case Study" in case_brief_entries[0]["source_filename"]

    # 4. Page Extraction Integrity & 1-Based Numbering
    assert len(pages) == 24
    for page in pages:
        assert page["page_number"] >= 1
        assert page["page_number"] <= page["page_count"]
        assert len(page["text_hash"]) > 0
        assert len(page["source_filename"]) > 0
        assert page["extraction_method"] == "pymupdf"


def test_mandatory_representative_pages_content(processed_corpus):
    """
    HARD ACCEPTANCE TEST:
    Manually inspect and verify extracted content from representative pages of ALL 4 brochures
    against rendered PDF contents.
    """
    pages = processed_corpus["pages"]

    # Helper function to find a specific page record
    def get_page(filename_substr: str, page_num: int):
        for p in pages:
            if filename_substr.lower() in p["source_filename"].lower() and p["page_number"] == page_num:
                return p
        raise AssertionError(f"Could not find page {page_num} for brochure matching '{filename_substr}'")

    # 1. ABHI Product Brochure.pdf — Page 2 (Accelerating cover values 2X, 3X, 4X, 5X, 6X)
    abhi_p2 = get_page("ABHI", 2)
    assert "2X" in abhi_p2["clean_text"]
    assert "3X" in abhi_p2["clean_text"]
    assert "4X" in abhi_p2["clean_text"]
    assert "5X" in abhi_p2["clean_text"]
    assert "6X" in abhi_p2["clean_text"]
    assert "INFLATION-PROOF" in abhi_p2["clean_text"]
    assert "HEALTH INSURANCE PLAN" in abhi_p2["clean_text"]

    # 2. Care Health Product Brochure.pdf — Page 4 (Wait periods: 30 days, 24 months, 36 months)
    care_p4 = get_page("Care", 4)
    assert "30 days" in care_p4["clean_text"]
    assert "24 months" in care_p4["clean_text"]
    assert "36 months" in care_p4["clean_text"]
    assert "Wait Periods" in care_p4["clean_text"] or "Wait Period" in care_p4["clean_text"]

    # 3. HDFC Product Brochure.pdf — Page 2 & Page 11 (Secure Benefit 2X, Sum Insured options)
    hdfc_p2 = get_page("HDFC", 2)
    assert "Secure" in hdfc_p2["clean_text"]
    assert "2X" in hdfc_p2["clean_text"]
    assert "100%" in hdfc_p2["clean_text"]

    hdfc_p11 = get_page("HDFC", 11)
    assert "Optima Secure+" in hdfc_p11["clean_text"]
    assert "Base Sum Insured" in hdfc_p11["clean_text"]
    assert "10/15/20/25/50/100/200" in hdfc_p11["clean_text"]

    # 4. Niva Bupa Product Brochure.pdf — Page 1 (Graphic cover, UIN) & Page 2 (Benefit table)
    niva_p1 = get_page("Niva Bupa", 1)
    assert "NBHHLIP26042V022526" in niva_p1["clean_text"]
    assert niva_p1["character_count"] < 100
    assert len(niva_p1["warnings"]) > 0
    assert "LOW_TEXT_GRAPHIC_COVER" in niva_p1["warnings"][0]

    niva_p2 = get_page("Niva Bupa", 2)
    assert "ReAssure 2.0" in niva_p2["clean_text"]
    assert "Platinum" in niva_p2["clean_text"]
    assert "5 Lacs" in niva_p2["clean_text"]
    assert "Product Bene" in niva_p2["clean_text"] or "Product Benefit" in niva_p2["clean_text"]
