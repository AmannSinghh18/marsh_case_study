"""
Pydantic Schemas for Claim-Level Audit Engine (Phase 4 Stage 4F)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExtractedClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str  # numeric, benefit, coverage, limitation, eligibility, waiting_period, comparison, recommendation_reason, company_fact
    source_output: str  # e.g., recommendation.json, pitch_content.json, slide_1
    evidence_ids: List[str] = Field(default_factory=list)
    extracted_numbers: List[str] = Field(default_factory=list)
    extracted_conditions: List[str] = Field(default_factory=list)


class AuditResultItem(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str
    source_output: str
    evidence_ids: List[str]
    audit_status: str  # PASS, REVIEW, FAIL
    audit_reason: str
    numerical_check_passed: bool
    qualifier_check_passed: bool
    cited_evidence_details: List[Dict[str, Any]] = Field(default_factory=list)


class AuditReport(BaseModel):
    total_claims_audited: int
    pass_count: int
    review_count: int
    fail_count: int
    unsupported_claim_count: int
    audited_claims: List[AuditResultItem]
    audit_summary: str
    overall_status: str  # PASSED, FAILED
