"""
End-to-End Integration Tests (Phase 4 Stage 4K, Correction 2 & Correction 3)
"""

import pytest
import os
import json
import hashlib
import random
from pptx import Presentation

from src.recommendation.feature_matching import compute_policy_fit_matrix
from src.recommendation.scoring import sort_policies_with_tie_break
from src.audit.audit_engine import execute_full_audit
from src.pitch_builder import build_pitch_content, generate_pptx_deck


def test_S_ppt_matches_recommendation_json():
    rec_path = os.path.join("data", "processed", "recommendation.json")
    pitch_path = os.path.join("data", "processed", "pitch_content.json")

    with open(rec_path, "r", encoding="utf-8") as f:
        rec = json.load(f)
    with open(pitch_path, "r", encoding="utf-8") as f:
        pitch = json.load(f)

    assert rec["insurer"] in pitch["slides"][3]["bullet_points"][0]


def test_T_ppt_contains_exactly_5_slides():
    pptx_path = os.path.join("outputs", "marsh_case_study_pitch.pptx")
    assert os.path.exists(pptx_path)

    prs = Presentation(pptx_path)
    assert len(prs.slides) == 5


def test_U_phase1_2_3_artifacts_unchanged():
    matrix_path = os.path.join("data", "processed", "policy_evidence_matrix.json")
    pages_path = os.path.join("data", "processed", "policy_pages.json")
    index_path = os.path.join("data", "processed", "retrieval_index", "index.faiss")

    assert os.path.exists(matrix_path)
    assert os.path.exists(pages_path)
    assert os.path.exists(index_path)

    with open(matrix_path, "rb") as f:
        matrix_hash = hashlib.sha256(f.read()).hexdigest()

    # Authoritative canonical matrix SHA-256 hash
    assert matrix_hash == "b6f985146744faed328fd31218607802a5ddd2239e1bcbd892e4c86a0b8f27e5"


def test_V_tie_break_determinism_and_shuffle_invariance():
    res1, _ = compute_policy_fit_matrix()
    winner1 = res1[0].insurer

    # Shuffle the policy list and re-sort with tie-break
    shuffled_res = list(res1)
    random.shuffle(shuffled_res)
    sorted_res = sort_policies_with_tie_break(shuffled_res)
    winner2 = sorted_res[0].insurer

    assert winner1 == winner2
    assert sorted_res[0].overall_rank == 1


def test_W_pipeline_audit_before_ppt_generation_flow():
    pitch_data = build_pitch_content()
    audit_report = execute_full_audit()

    # Ensure claim audit reports 0 fails before PPT deck generation
    assert audit_report["fail_count"] == 0
    assert audit_report["pass_count"] > 0

    ppt_path = generate_pptx_deck(pitch_data)
    assert os.path.exists(ppt_path)
    prs = Presentation(ppt_path)
    assert len(prs.slides) == 5


def test_X_ppt_evidence_ids_resolve_to_canonical_matrix():
    matrix_path = os.path.join("data", "processed", "policy_evidence_matrix.json")
    pitch_path = os.path.join("data", "processed", "pitch_content.json")

    with open(matrix_path, "r", encoding="utf-8") as f:
        matrix = json.load(f)
    with open(pitch_path, "r", encoding="utf-8") as f:
        pitch = json.load(f)

    valid_ids = {r["evidence_id"] for r in matrix}

    for slide in pitch["slides"]:
        for eid in slide["evidence_ids"]:
            assert eid in valid_ids, f"Slide evidence ID {eid} not in canonical matrix"
