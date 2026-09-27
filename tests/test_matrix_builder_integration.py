import os
import json
import csv
import pathlib
import pytest
from src.matrix_builder import MatrixBuilder

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROCESSED_DIR = WORKSPACE_ROOT / "data" / "processed"
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"


@pytest.fixture(scope="module")
def matrix_results():
    """Run matrix builder engine and return generated outputs."""
    builder = MatrixBuilder(processed_dir=PROCESSED_DIR, output_dir=OUTPUTS_DIR, force=True)
    success = builder.process()
    assert success is True, "MatrixBuilder pipeline failed during setup!"

    with open(PROCESSED_DIR / "policy_evidence_matrix.json", "r", encoding="utf-8") as f:
        records = json.load(f)

    with open(PROCESSED_DIR / "policy_evidence_validation_report.json", "r", encoding="utf-8") as f:
        report = json.load(f)

    return {
        "records": records,
        "report": report
    }


def test_matrix_builder_end_to_end_generation(matrix_results):
    records = matrix_results["records"]
    report = matrix_results["report"]

    # 1. Validation Report Status
    assert report["overall_status"] == "PASSED"
    assert report["checklists_status"] == "PASSED"
    assert len(report["errors"]) == 0
    assert report["total_records"] > 0
    assert report["total_canonical_corpus_records"] == report["total_records"]

    # 2. Insurer Representation (All 4 present)
    insurers = set(r["insurer"] for r in records)
    assert "Aditya Birla Capital" in insurers
    assert "Care Health Insurance" in insurers
    assert "HDFC ERGO" in insurers
    assert "Niva Bupa" in insurers

    # 3. Case Brief Exclusion Check (Zero records)
    case_brief_records = [r for r in records if "case study" in r["source_document"].lower()]
    assert len(case_brief_records) == 0


def test_hard_provenance_verbatim_match_pass(matrix_results):
    """
    HARD PROVENANCE TEST:
    Assert that 100% of evidence records have a verbatim source_text substring match on their
    specified page in policy_pages.json.
    """
    records = matrix_results["records"]
    with open(PROCESSED_DIR / "policy_pages.json", "r", encoding="utf-8") as f:
        pages = json.load(f)

    page_map = {(p["source_filename"], p["page_number"]): p["clean_text"] for p in pages}

    for r in records:
        key = (r["source_document"], r["source_page"])
        assert key in page_map, f"Record {r['evidence_id']} specifies invalid page key {key}"
        
        page_clean_text = page_map[key]
        source_text = r["source_text"]
        
        norm_source = " ".join(source_text.split())
        norm_page = " ".join(page_clean_text.split())
        
        assert norm_source in norm_page, (
            f"Record {r['evidence_id']} source_text not found on page {r['source_page']} of {r['source_document']}.\n"
            f"Expected: {source_text[:100]}..."
        )


def test_mandatory_representative_records_verification(matrix_results):
    """
    HARD ACCEPTANCE TEST:
    Verify specific representative evidence items from all 4 brochures.
    """
    records = matrix_results["records"]

    def find_record(rec_id: str):
        for r in records:
            if r["evidence_id"] == rec_id:
                return r
        raise AssertionError(f"Record {rec_id} not found in matrix!")

    # 1. ABHI Super Credit (ABHI-001)
    abhi_001 = find_record("ABHI-001")
    assert abhi_001["value"] == "6X"
    assert abhi_001["source_page"] == 2
    assert "2X 3X 4X 5X 6X" in abhi_001["source_text"]

    # 2. Care Supreme Waiting Periods (CARE-006)
    care_006 = find_record("CARE-006")
    assert care_006["source_page"] == 4
    assert "30 days" in care_006["source_text"]
    assert "24 months" in care_006["source_text"]
    assert "36 months" in care_006["source_text"]

    # 3. HDFC Secure Benefit (HDFC-001)
    hdfc_001 = find_record("HDFC-001")
    assert hdfc_001["value"] == "2X"
    assert hdfc_001["source_page"] == 2
    assert "Secure Beneﬁt\n2X coverage from Day 1" in hdfc_001["source_text"]

    # 4. Niva Bupa ReAssure+ (NIVA-001)
    niva_001 = find_record("NIVA-001")
    assert niva_001["source_page"] == 2
    assert "ReAssure+" in niva_001["source_text"]
    assert "1 claim triggers ReAssure+, forever" in niva_001["source_text"]


def test_matrix_determinism(matrix_results):
    """Verify that building the matrix twice generates identical JSON and CSV outputs."""
    builder = MatrixBuilder(processed_dir=PROCESSED_DIR, output_dir=OUTPUTS_DIR, force=True)
    builder.process()

    with open(PROCESSED_DIR / "policy_evidence_matrix.json", "r", encoding="utf-8") as f:
        records_run2 = json.load(f)

    assert matrix_results["records"] == records_run2
