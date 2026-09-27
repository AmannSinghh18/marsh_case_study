"""
Unit and Integration Tests for Recommendation Engine (Phase 4 Stage 4K)
"""

import pytest
import os
import json
from src.recommendation.feature_matching import compute_policy_fit_matrix
from src.recommendation.recommendation import generate_recommendation_artifact
from src.recommendation.requirements import build_risk_requirements, build_assumptions


def test_A_case_profile_supported_facts():
    path = os.path.join("data", "processed", "case_profile.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    assert profile["employee_count"] == 500
    assert profile["source_document"] == "Marsh - Internship Case Study.pdf"


def test_B_unknown_case_facts_not_fabricated():
    path = os.path.join("data", "processed", "case_profile.json")
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    assert profile["existing_benefits"] is None
    assert profile["budget_information"] is None
    assert profile["current_insurance_information"] is None


def test_C_risk_requirements_deterministic():
    reqs1 = build_risk_requirements()
    reqs2 = build_risk_requirements()
    assert reqs1 == reqs2
    assert len(reqs1) == 7


def test_D_all_four_policies_in_comparison():
    fit_results, matrix_export = compute_policy_fit_matrix()
    insurers = [p.insurer for p in fit_results]
    assert len(fit_results) == 4
    assert any("Care Health" in i for i in insurers)
    assert any("HDFC" in i for i in insurers)
    assert any("Aditya Birla" in i for i in insurers)
    assert any("Niva Bupa" in i for i in insurers)


def test_E_important_matches_retain_evidence_ids():
    fit_results, _ = compute_policy_fit_matrix()
    for res in fit_results:
        for match in res.requirement_matches:
            if match.match_status == "MATCH":
                assert len(match.evidence_ids) > 0


def test_H_recommendation_reproducible():
    rec1 = generate_recommendation_artifact()
    rec2 = generate_recommendation_artifact()
    assert rec1["recommended_policy"] == rec2["recommended_policy"]
    assert rec1["total_fit_score"] == rec2["total_fit_score"]


def test_I_recommendation_evidence_ids_exist():
    matrix_path = os.path.join("data", "processed", "policy_evidence_matrix.json")
    with open(matrix_path, "r", encoding="utf-8") as f:
        matrix = json.load(f)
    valid_ids = {r["evidence_id"] for r in matrix}

    rec = generate_recommendation_artifact()
    for eid in rec["evidence_ids"]:
        assert eid in valid_ids, f"Evidence ID {eid} not in canonical matrix"
