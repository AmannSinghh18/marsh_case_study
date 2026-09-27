import logging
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from .config import RetrievalConfig
from .schemas import EvidenceRecord, SearchQuery, SearchResult
from .embedder import PolicyEvidenceEmbedder
from .index import FAISSVectorIndex

logger = logging.getLogger(__name__)

class PolicyEvidenceRetriever:
    """
    Metadata-aware, evidence-grounded semantic retriever for policy evidence records.
    Filters candidate records against metadata criteria BEFORE similarity scoring & top-k selection,
    and returns rank-ordered SearchResult objects preserving exact provenance.
    """
    def __init__(
        self,
        config: Optional[RetrievalConfig] = None,
        embedder: Optional[PolicyEvidenceEmbedder] = None,
        index: Optional[FAISSVectorIndex] = None
    ):
        self.config = config or RetrievalConfig()
        self.embedder = embedder or PolicyEvidenceEmbedder(self.config.embedding_model_name)
        self.index = index or FAISSVectorIndex(self.config)

    def load_index(self) -> bool:
        return self.index.load(self.config.index_file, self.config.metadata_file)

    def _matches_filters(self, record: EvidenceRecord, query: SearchQuery) -> bool:
        """
        Check if an evidence record satisfies all metadata filters specified in search query.
        """
        if query.insurer:
            if query.insurer.lower() not in record.insurer.lower():
                return False

        if query.policy:
            if query.policy.lower() not in record.policy.lower():
                return False

        if query.category:
            if query.category.lower() != record.category.lower():
                return False

        if query.claim_type:
            if query.claim_type.lower() != record.claim_type.lower():
                return False

        if query.variant:
            if not record.variant or query.variant.lower() not in record.variant.lower():
                return False

        if query.evidence_strength:
            if query.evidence_strength.lower() != record.evidence_strength.lower():
                return False

        if query.review_status:
            if query.review_status.lower() != record.review_status.lower():
                return False

        if query.is_optional is not None:
            if record.is_optional != query.is_optional:
                return False

        return True

    def search(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        insurer: Optional[str] = None,
        policy: Optional[str] = None,
        category: Optional[str] = None,
        claim_type: Optional[str] = None,
        variant: Optional[str] = None,
        evidence_strength: Optional[str] = None,
        review_status: Optional[str] = None,
        is_optional: Optional[bool] = None
    ) -> List[SearchResult]:
        """
        Execute semantic retrieval over indexed policy evidence records.
        Conceptual Execution Pipeline:
        1. Parse query & metadata filters
        2. Candidate Pre-Filtering (metadata filters applied BEFORE vector top-k)
        3. Vector Embed query & compute similarity scores over filtered candidates
        4. Apply min_score threshold
        5. Select top_k candidate records
        6. Return SearchResult list (or empty list if no candidate passes threshold)
        """
        k = top_k if top_k is not None else self.config.default_top_k
        threshold = min_score if min_score is not None else self.config.default_min_similarity_threshold

        search_query = SearchQuery(
            query_text=query_text,
            top_k=k,
            min_score=threshold,
            insurer=insurer,
            policy=policy,
            category=category,
            claim_type=claim_type,
            variant=variant,
            evidence_strength=evidence_strength,
            review_status=review_status,
            is_optional=is_optional
        )

        cleaned_text = " ".join(query_text.split())
        if not cleaned_text:
            logger.warning("Empty or whitespace search query received.")
            return []

        if not self.index.indexed_records:
            return []

        # 1. PRE-FILTERING: Identify candidate indices that satisfy metadata criteria
        candidate_indices: List[int] = []
        for idx, rec in enumerate(self.index.indexed_records):
            if self._matches_filters(rec, search_query):
                candidate_indices.append(idx)

        if not candidate_indices:
            logger.info("No candidates matched the specified metadata filters.")
            return []

        # 2. VECTOR SIMILARITY: Compute similarity for pre-filtered candidates
        query_vec = self.embedder.encode_query(cleaned_text).astype(np.float32)

        # Retrieve vectors for candidates
        candidate_records = [self.index.indexed_records[i] for i in candidate_indices]
        
        # Calculate cosine similarity scores
        scores_and_records: List[Tuple[EvidenceRecord, float]] = []
        
        # If FAISS index is present, extract vectors or compute cosine similarity
        if hasattr(self.index.index, "reconstruct"):
            # FAISS IndexFlatIP reconstruction
            candidate_vectors = np.array([self.index.index.reconstruct(i) for i in candidate_indices], dtype=np.float32)
            sims = np.dot(candidate_vectors, query_vec.T).flatten()
            for rec, score in zip(candidate_records, sims):
                scores_and_records.append((rec, float(score)))
        elif hasattr(self.index.index, "embeddings"):
            # NumPy index fallback
            candidate_vectors = self.index.index.embeddings[candidate_indices]
            sims = np.dot(candidate_vectors, query_vec.T).flatten()
            for rec, score in zip(candidate_records, sims):
                scores_and_records.append((rec, float(score)))
        else:
            # Fallback using search
            all_candidates = self.index.search_candidates(query_vec, top_k=len(self.index.indexed_records))
            cand_set = set(candidate_indices)
            for rec, score in all_candidates:
                idx = self.index.indexed_records.index(rec)
                if idx in cand_set:
                    scores_and_records.append((rec, score))

        # 3. THRESHOLD & SORT
        scored_candidates = [(rec, s) for rec, s in scores_and_records if s >= threshold]
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 4. TOP-K SELECTION
        top_candidates = scored_candidates[:k]

        # 5. RESULT FORMATTING
        results: List[SearchResult] = []
        for rank, (record, score) in enumerate(top_candidates, 1):
            is_flagged = (record.review_status in self.config.flagged_statuses)

            result = SearchResult(
                rank=rank,
                evidence_id=record.evidence_id,
                score=round(float(score), 4),
                insurer=record.insurer,
                policy=record.policy,
                variant=record.variant,
                category=record.category,
                feature=record.feature,
                claim=record.claim,
                value=record.value,
                unit=record.unit,
                conditions=record.conditions,
                limitations=record.limitations,
                evidence_strength=record.evidence_strength,
                review_status=record.review_status,
                source_document=record.source_document,
                source_page=record.source_page,
                source_section=record.source_section,
                source_text=record.source_text,
                is_flagged_for_review=is_flagged,
                review_notes=record.review_notes
            )
            results.append(result)

        return results
