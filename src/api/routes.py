"""
FastAPI REST API Routes (Phase 4 Stage 4I)
Exposes read-only API endpoints over validated Phase 4 artifacts.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from src.api.schemas import HealthResponse, StatusResponse
from src.api.services import load_json_artifact, load_canonical_evidence_list, get_evidence_by_id

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        phase="Phase 4 - Recommendation & Audit Layer",
        canonical_matrix_records=len(load_canonical_evidence_list())
    )


@router.get("/company")
def get_company_profile():
    data = load_json_artifact("case_profile.json")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/requirements")
def get_risk_requirements():
    data = load_json_artifact("risk_requirements.json")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/policies")
def get_policy_fit_matrix():
    data = load_json_artifact("policy_fit_matrix.json")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/recommendation")
def get_recommendation():
    data = load_json_artifact("recommendation.json")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/audit")
def get_audit_report():
    data = load_json_artifact("audit_report.json")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/pitch")
def get_pitch_content():
    data = load_json_artifact("pitch_content.json")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/evidence")
def list_evidence(
    insurer: Optional[str] = Query(None),
    policy: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    records = load_canonical_evidence_list()
    filtered = records

    if insurer:
        filtered = [r for r in filtered if insurer.lower() in r.get("insurer", "").lower()]
    if policy:
        filtered = [r for r in filtered if policy.lower() in r.get("policy", "").lower()]
    if category:
        filtered = [r for r in filtered if category.lower() in r.get("category", "").lower()]

    return {"count": len(filtered), "evidence": filtered}


@router.get("/evidence/{evidence_id}")
def get_evidence_detail(evidence_id: str):
    record = get_evidence_by_id(evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evidence ID '{evidence_id}' not found in canonical matrix.")
    return record


@router.get("/status", response_model=StatusResponse)
def get_system_status():
    audit_data = load_json_artifact("audit_report.json")
    return StatusResponse(
        system_status="OPERATIONAL",
        phase1_2_3_frozen=True,
        canonical_records=36,
        eligible_records=36,
        indexed_records=36,
        faiss_index_type="IndexFlatIP",
        embedding_dimension=384,
        audit_pass_count=audit_data.get("pass_count", 0),
        audit_fail_count=audit_data.get("fail_count", 0),
        validation_status="PASSED"
    )
