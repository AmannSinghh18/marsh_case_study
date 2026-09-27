"""
FastAPI REST API Schemas (Phase 4 Stage 4I)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    phase: str = "Phase 4 - Recommendation & Audit Layer"
    canonical_matrix_records: int = 36


class StatusResponse(BaseModel):
    system_status: str
    phase1_2_3_frozen: bool
    canonical_records: int
    eligible_records: int
    indexed_records: int
    faiss_index_type: str
    embedding_dimension: int
    audit_pass_count: int
    audit_fail_count: int
    validation_status: str
