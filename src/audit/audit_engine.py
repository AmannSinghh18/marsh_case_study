"""
Audit Engine (Phase 4 Stage 4F)
Audits every material insurance claim against canonical evidence matrix records.
"""

import json
import os
from typing import List, Dict, Any
from src.audit.schemas import ExtractedClaim, AuditResultItem, AuditReport
from src.audit.evidence_checker import load_canonical_evidence_matrix, check_evidence_support
from src.audit.numeric_checker import check_numeric_alignment
from src.audit.claim_extractor import extract_recommendation_claims, extract_pitch_claims


def run_claim_audit(claims: List[ExtractedClaim]) -> AuditReport:
    matrix_map = load_canonical_evidence_matrix()
    audited_items: List[AuditResultItem] = []

    pass_count = 0
    review_count = 0
    fail_count = 0
    unsupported_count = 0

    for claim in claims:
        # Step 1: Evidence support check
        ev_status, ev_reason, qual_passed, details = check_evidence_support(
            claim.evidence_ids, claim.claim_text, claim.claim_type, matrix_map
        )

        # Step 2: Numerical check
        num_passed, num_reason = check_numeric_alignment(claim.claim_text, claim.claim_type, details)

        # Combine checks to determine final status
        if ev_status == "FAIL" or not num_passed:
            final_status = "FAIL"
            final_reason = ev_reason if ev_status == "FAIL" else num_reason
            fail_count += 1
            if ev_status == "FAIL":
                unsupported_count += 1
        elif ev_status == "REVIEW" or not qual_passed:
            final_status = "REVIEW"
            final_reason = ev_reason
            review_count += 1
        else:
            final_status = "PASS"
            final_reason = "100% verified against canonical evidence with exact provenance."
            pass_count += 1

        details_summary = [
            {
                "evidence_id": e["evidence_id"],
                "insurer": e["insurer"],
                "policy": e["policy"],
                "feature": e["feature"],
                "source_document": e["source_document"],
                "source_page": e["source_page"],
                "source_section": e["source_section"],
                "source_text": e["source_text"]
            }
            for e in details
        ]

        audited_items.append(AuditResultItem(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            claim_type=claim.claim_type,
            source_output=claim.source_output,
            evidence_ids=claim.evidence_ids,
            audit_status=final_status,
            audit_reason=final_reason,
            numerical_check_passed=num_passed,
            qualifier_check_passed=qual_passed,
            cited_evidence_details=details_summary
        ))

    overall_status = "PASSED" if fail_count == 0 else "FAILED"
    summary_text = f"Audited {len(claims)} material claims: {pass_count} PASS, {review_count} REVIEW, {fail_count} FAIL."

    return AuditReport(
        total_claims_audited=len(claims),
        pass_count=pass_count,
        review_count=review_count,
        fail_count=fail_count,
        unsupported_claim_count=unsupported_count,
        audited_claims=audited_items,
        audit_summary=summary_text,
        overall_status=overall_status
    )


def execute_full_audit(
    rec_path: str = "data/processed/recommendation.json",
    pitch_path: str = "data/processed/pitch_content.json",
    output_report_path: str = "data/processed/audit_report.json"
) -> Dict[str, Any]:
    claims = []
    claims.extend(extract_recommendation_claims(rec_path))
    claims.extend(extract_pitch_claims(pitch_path))

    report = run_claim_audit(claims)
    report_dict = report.model_dump()

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    print(f"Audit report saved to: {output_report_path}")
    print(f"Audit Summary: {report.audit_summary} (Overall Status: {report.overall_status})")
    return report_dict


def main():
    execute_full_audit()


if __name__ == "__main__":
    main()
