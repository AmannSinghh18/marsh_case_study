import json
import pytest
from pathlib import Path
import numpy as np

from src.retrieval.config import RetrievalConfig
from src.retrieval.schemas import EvidenceRecord, SearchResult, IndexManifest
from src.retrieval.embedder import PolicyEvidenceEmbedder
from src.retrieval.index import FAISSVectorIndex
from src.retrieval.retriever import PolicyEvidenceRetriever
from src.retrieval.build_index import build_retrieval_index

@pytest.fixture(scope="module")
def shared_embedder():
    config = RetrievalConfig()
    return PolicyEvidenceEmbedder(config.embedding_model_name)

@pytest.fixture(scope="module")
def canonical_matrix_data():
    matrix_path = RetrievalConfig.canonical_matrix_path
    with open(matrix_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def canonical_matrix_records(canonical_matrix_data):
    return [EvidenceRecord.from_dict(r) for r in canonical_matrix_data]

@pytest.fixture(scope="module")
def shared_retriever(canonical_matrix_records, shared_embedder):
    config = RetrievalConfig()
    index = FAISSVectorIndex(config)
    index.build_from_records(canonical_matrix_records, shared_embedder)
    return PolicyEvidenceRetriever(config=config, embedder=shared_embedder, index=index)


# A. Index creation succeeds.
def test_A_index_creation_succeeds(tmp_path, shared_embedder):
    config = RetrievalConfig(
        index_file=tmp_path / "index.faiss",
        metadata_file=tmp_path / "metadata.json",
        manifest_file=tmp_path / "index_manifest.json",
        report_file=tmp_path / "report.json"
    )
    report = build_retrieval_index(config=config, embedder=shared_embedder)
    assert report["indexed_record_count"] == 36
    assert config.index_file.exists() or Path(str(config.index_file) + ".npy").exists()
    assert config.metadata_file.exists()
    assert config.manifest_file.exists()


# B. All eligible production evidence records are indexed.
def test_B_all_eligible_records_indexed(canonical_matrix_records, shared_embedder):
    config = RetrievalConfig()
    index = FAISSVectorIndex(config)
    indexed_count = index.build_from_records(canonical_matrix_records, shared_embedder)
    eligible = [r for r in canonical_matrix_records if r.review_status != "rejected"]
    assert indexed_count == len(eligible)
    assert len(index.indexed_records) == len(eligible)


# C. Rejected synthetic test records are excluded.
def test_C_rejected_records_excluded(shared_embedder):
    config = RetrievalConfig()
    records = [
        EvidenceRecord.from_dict({
            "evidence_id": "TEST-001",
            "insurer": "Test Insurer",
            "policy": "Test Policy",
            "category": "coverage",
            "feature": "Test Feature",
            "claim": "Test Claim 1",
            "source_document": "Care Health Product Brochure.pdf",
            "source_page": 1,
            "source_section": "Test",
            "source_text": "Up to 60 days pre-hospitalization and 180 days post-hospitalization coverage",
            "evidence_strength": "direct",
            "review_status": "verified"
        }),
        EvidenceRecord.from_dict({
            "evidence_id": "TEST-REJECTED",
            "insurer": "Test Insurer",
            "policy": "Test Policy",
            "category": "coverage",
            "feature": "Test Feature Rejected",
            "claim": "Test Claim 2",
            "source_document": "Care Health Product Brochure.pdf",
            "source_page": 1,
            "source_section": "Test",
            "source_text": "Rejected claim text assertion",
            "evidence_strength": "direct",
            "review_status": "rejected"
        })
    ]
    index = FAISSVectorIndex(config)
    count = index.build_from_records(records, shared_embedder)
    assert count == 1
    indexed_ids = {r.evidence_id for r in index.indexed_records}
    assert "TEST-REJECTED" not in indexed_ids


# D. Verified synthetic test records are indexed.
def test_D_verified_synthetic_records_indexed(shared_embedder):
    config = RetrievalConfig()
    records = [
        EvidenceRecord.from_dict({
            "evidence_id": "TEST-VERIFIED",
            "insurer": "Test Insurer",
            "policy": "Test Policy",
            "category": "coverage",
            "feature": "Test Feature Verified",
            "claim": "Test Claim Verified",
            "source_document": "Care Health Product Brochure.pdf",
            "source_page": 1,
            "source_section": "Test",
            "source_text": "Up to 60 days pre-hospitalization and 180 days post-hospitalization coverage",
            "evidence_strength": "direct",
            "review_status": "verified"
        })
    ]
    index = FAISSVectorIndex(config)
    count = index.build_from_records(records, shared_embedder)
    assert count == 1
    assert index.indexed_records[0].evidence_id == "TEST-VERIFIED"


# E. Review-required synthetic test records are indexed and remain visibly flagged.
def test_E_review_required_synthetic_records_flagged(shared_embedder):
    config = RetrievalConfig()
    records = [
        EvidenceRecord.from_dict({
            "evidence_id": "TEST-REVIEW",
            "insurer": "Test Insurer",
            "policy": "Test Policy",
            "category": "coverage",
            "feature": "Test Feature Review",
            "claim": "Test Claim Review",
            "source_document": "Care Health Product Brochure.pdf",
            "source_page": 1,
            "source_section": "Test",
            "source_text": "Up to 60 days pre-hospitalization and 180 days post-hospitalization coverage",
            "evidence_strength": "direct",
            "review_status": "review_required",
            "review_notes": "Needs audit"
        })
    ]
    index = FAISSVectorIndex(config)
    index.build_from_records(records, shared_embedder)
    retriever = PolicyEvidenceRetriever(config=config, embedder=shared_embedder, index=index)
    results = retriever.search("hospitalization", top_k=5, min_score=0.0)
    assert len(results) == 1
    assert results[0].evidence_id == "TEST-REVIEW"
    assert results[0].is_flagged_for_review is True
    assert results[0].review_status == "review_required"


# F. Returned evidence IDs exist in canonical matrix.
def test_F_query_returns_valid_evidence_ids(shared_retriever, canonical_matrix_data):
    valid_ids = {r["evidence_id"] for r in canonical_matrix_data}
    results = shared_retriever.search("maternity coverage", top_k=5, min_score=0.0)
    assert len(results) > 0
    for res in results:
        assert res.evidence_id in valid_ids


# G. Returned source_text exactly equals canonical source_text.
def test_G_returned_source_text_exact_match(shared_retriever, canonical_matrix_data):
    matrix_map = {r["evidence_id"]: r["source_text"] for r in canonical_matrix_data}
    results = shared_retriever.search("hospitalization expenses", top_k=5, min_score=0.0)
    for res in results:
        assert res.source_text == matrix_map[res.evidence_id]


# H. Returned source_page exactly equals canonical source_page.
def test_H_returned_source_page_exact_match(shared_retriever, canonical_matrix_data):
    matrix_map = {r["evidence_id"]: r["source_page"] for r in canonical_matrix_data}
    results = shared_retriever.search("health checkup", top_k=5, min_score=0.0)
    for res in results:
        assert res.source_page == matrix_map[res.evidence_id]


# I. Returned source_document exactly equals canonical source_document.
def test_I_returned_source_document_exact_match(shared_retriever, canonical_matrix_data):
    matrix_map = {r["evidence_id"]: r["source_document"] for r in canonical_matrix_data}
    results = shared_retriever.search("ambulance cover", top_k=5, min_score=0.0)
    for res in results:
        assert res.source_document == matrix_map[res.evidence_id]


# J. Returned source_section exactly equals canonical source_section.
def test_J_returned_source_section_exact_match(shared_retriever, canonical_matrix_data):
    matrix_map = {r["evidence_id"]: r.get("source_section", "") for r in canonical_matrix_data}
    results = shared_retriever.search("air ambulance", top_k=5, min_score=0.0)
    for res in results:
        assert res.source_section == matrix_map[res.evidence_id]


# K. Metadata filtering works before top-k selection.
def test_K_metadata_filters_pre_filtering_top_k(shared_retriever):
    # Retrieve top 2 for category="deductible"
    results = shared_retriever.search("hospitalization cover", category="deductible", top_k=2, min_score=0.0)
    assert all(r.category == "deductible" for r in results)


# L. Combined metadata filters work.
def test_L_combined_metadata_filters_work(shared_retriever):
    results = shared_retriever.search("deductible", insurer="HDFC ERGO", claim_type="deductible", min_score=0.0)
    assert len(results) > 0
    assert all(r.insurer == "HDFC ERGO" and r.category == "deductible" for r in results)


# M. Threshold filtering works.
def test_M_threshold_filtering_works(shared_retriever):
    # Setting threshold high filters low relevance results
    results_high = shared_retriever.search("maternity coverage", min_score=0.40)
    results_low = shared_retriever.search("maternity coverage", min_score=0.10)
    assert len(results_high) <= len(results_low)
    assert all(r.score >= 0.40 for r in results_high)


# N. No-result behavior works.
def test_N_threshold_no_result_behavior(shared_retriever):
    results = shared_retriever.search("maternity coverage", min_score=0.999)
    assert results == []


# O. top_k is respected.
def test_O_top_k_respected(shared_retriever):
    results_3 = shared_retriever.search("coverage", top_k=3, min_score=0.0)
    assert len(results_3) <= 3
    results_1 = shared_retriever.search("coverage", top_k=1, min_score=0.0)
    assert len(results_1) <= 1


# P. Empty/whitespace queries are handled safely.
def test_P_empty_whitespace_queries_handled_safely(shared_retriever):
    assert shared_retriever.search("") == []
    assert shared_retriever.search("   ") == []
    assert shared_retriever.search("\n\t") == []


# Q. Duplicate evidence IDs are detected.
def test_Q_duplicate_evidence_ids_detected(tmp_path):
    dup_matrix_path = tmp_path / "dup_matrix.json"
    dup_records = [
        {
            "evidence_id": "DUP-001",
            "insurer": "Test",
            "policy": "Test",
            "category": "coverage",
            "feature": "F1",
            "claim": "C1",
            "source_document": "Care Health Product Brochure.pdf",
            "source_page": 1,
            "source_text": "Up to 60 days pre-hospitalization and 180 days post-hospitalization coverage"
        },
        {
            "evidence_id": "DUP-001",
            "insurer": "Test",
            "policy": "Test",
            "category": "coverage",
            "feature": "F2",
            "claim": "C2",
            "source_document": "Care Health Product Brochure.pdf",
            "source_page": 1,
            "source_text": "Up to 60 days pre-hospitalization and 180 days post-hospitalization coverage"
        }
    ]
    with open(dup_matrix_path, "w", encoding="utf-8") as f:
        json.dump(dup_records, f)

    config = RetrievalConfig(canonical_matrix_path=dup_matrix_path)
    with pytest.raises(ValueError, match="Duplicate evidence IDs found"):
        build_retrieval_index(matrix_path=dup_matrix_path, config=config)


# R. Indexed ID set equals canonical eligible ID set.
def test_R_indexed_id_set_equals_canonical_eligible_set(canonical_matrix_records, shared_embedder):
    config = RetrievalConfig()
    index = FAISSVectorIndex(config)
    index.build_from_records(canonical_matrix_records, shared_embedder)
    
    indexed_set = {r.evidence_id for r in index.indexed_records}
    eligible_set = {r.evidence_id for r in canonical_matrix_records if r.review_status != "rejected"}
    assert indexed_set == eligible_set


# S. Deterministic record ordering is preserved.
def test_S_deterministic_record_ordering_preserved(canonical_matrix_records, shared_embedder):
    config = RetrievalConfig()
    index = FAISSVectorIndex(config)
    index.build_from_records(canonical_matrix_records, shared_embedder)
    
    indexed_ids = [r.evidence_id for r in index.indexed_records]
    sorted_ids = sorted(indexed_ids)
    assert indexed_ids == sorted_ids


# T. Deterministic Rebuild Test: Rebuilding produces equivalent indexed evidence ordering/metadata.
def test_T_deterministic_rebuild(tmp_path, shared_embedder):
    config1 = RetrievalConfig(
        index_file=tmp_path / "b1" / "index.faiss",
        metadata_file=tmp_path / "b1" / "metadata.json",
        manifest_file=tmp_path / "b1" / "index_manifest.json",
        report_file=tmp_path / "b1" / "report.json"
    )
    config2 = RetrievalConfig(
        index_file=tmp_path / "b2" / "index.faiss",
        metadata_file=tmp_path / "b2" / "metadata.json",
        manifest_file=tmp_path / "b2" / "index_manifest.json",
        report_file=tmp_path / "b2" / "report.json"
    )

    build_retrieval_index(config=config1, embedder=shared_embedder)
    build_retrieval_index(config=config2, embedder=shared_embedder)

    with open(config1.manifest_file, "r", encoding="utf-8") as f:
        m1 = json.load(f)
    with open(config2.manifest_file, "r", encoding="utf-8") as f:
        m2 = json.load(f)

    with open(config1.metadata_file, "r", encoding="utf-8") as f:
        meta1 = json.load(f)
    with open(config2.metadata_file, "r", encoding="utf-8") as f:
        meta2 = json.load(f)

    assert m1["ordered_evidence_id_list"] == m2["ordered_evidence_id_list"]
    assert m1["indexed_record_count"] == m2["indexed_record_count"]
    assert meta1["records"] == meta2["records"]


# U. Metric configuration is cosine similarity using normalized vectors.
def test_U_metric_configuration_is_cosine_similarity():
    config = RetrievalConfig()
    assert config.metric == "cosine_similarity"
    assert config.faiss_index_type == "IndexFlatIP"
    assert config.normalized_embeddings is True


# V. Embedding dimension is 384 for the configured model.
def test_V_embedding_dimension_is_384(shared_embedder):
    config = RetrievalConfig()
    assert config.embedding_dimension == 384
    assert shared_embedder.dimension == 384
