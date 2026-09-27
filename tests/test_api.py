"""
Unit and Integration Tests for FastAPI REST API Endpoints (Phase 4 Stage 4K & Section 56)
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_P_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["canonical_matrix_records"] == 36


def test_P_company_endpoint():
    res = client.get("/api/company")
    assert res.status_code == 200
    data = res.json()
    assert data["employee_count"] == 500
    assert "TechCorp" in data["company_name"]


def test_P_requirements_endpoint():
    res = client.get("/api/requirements")
    assert res.status_code == 200
    data = res.json()
    assert len(data["requirements"]) == 7


def test_P_policies_endpoint():
    res = client.get("/api/policies")
    assert res.status_code == 200
    data = res.json()
    assert len(data["policies"]) == 4


def test_P_recommendation_endpoint():
    res = client.get("/api/recommendation")
    assert res.status_code == 200
    data = res.json()
    assert "Aditya Birla Capital" in data["recommended_policy"]


def test_P_audit_endpoint():
    res = client.get("/api/audit")
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "PASSED"
    assert data["fail_count"] == 0


def test_Q_evidence_endpoint_returns_exact_source_text():
    res = client.get("/api/evidence/CARE-003")
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_id"] == "CARE-003"
    assert "source_text" in data
    assert len(data["source_text"]) > 0


def test_Q_invalid_evidence_id_returns_404():
    res = client.get("/api/evidence/INVALID-999")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
