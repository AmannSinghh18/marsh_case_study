from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any

@dataclass
class EvidenceRecord:
    evidence_id: str
    insurer: str
    policy: str
    variant: Optional[str]
    category: str
    feature: str
    claim: str
    value: Optional[str]
    unit: Optional[str]
    conditions: Optional[str]
    limitations: Optional[str]
    eligibility: Optional[str]
    waiting_period: Optional[str]
    is_optional: bool
    addon_name: Optional[str]
    claim_type: str
    source_document: str
    source_page: int
    source_section: str
    source_text: str
    evidence_strength: str
    review_status: str
    review_notes: Optional[str] = None
    derived_from: Optional[List[str]] = None
    derivation: Optional[str] = None
    included_in_canonical_corpus: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["retrieval_text"] = self.to_searchable_text()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRecord":
        return cls(
            evidence_id=data["evidence_id"],
            insurer=data["insurer"],
            policy=data["policy"],
            variant=data.get("variant"),
            category=data["category"],
            feature=data["feature"],
            claim=data["claim"],
            value=data.get("value"),
            unit=data.get("unit"),
            conditions=data.get("conditions"),
            limitations=data.get("limitations"),
            eligibility=data.get("eligibility"),
            waiting_period=data.get("waiting_period"),
            is_optional=data.get("is_optional", False),
            addon_name=data.get("addon_name"),
            claim_type=data.get("claim_type", "direct_benefit"),
            source_document=data["source_document"],
            source_page=int(data["source_page"]),
            source_section=data.get("source_section", ""),
            source_text=data["source_text"],
            evidence_strength=data.get("evidence_strength", "direct"),
            review_status=data.get("review_status", "verified"),
            review_notes=data.get("review_notes"),
            derived_from=data.get("derived_from"),
            derivation=data.get("derivation"),
            included_in_canonical_corpus=data.get("included_in_canonical_corpus", True)
        )

    def to_searchable_text(self) -> str:
        """
        Create a deterministic searchable representation of the evidence record.
        Empty / None fields are strictly omitted.
        """
        parts = [
            f"Insurer: {self.insurer}",
            f"Policy: {self.policy}"
        ]
        if self.variant:
            parts.append(f"Variant: {self.variant}")
        parts.append(f"Category: {self.category}")
        parts.append(f"Feature: {self.feature}")
        parts.append(f"Claim: {self.claim}")
        if self.value:
            parts.append(f"Value: {self.value}")
        if self.unit:
            parts.append(f"Unit: {self.unit}")
        if self.conditions:
            parts.append(f"Conditions: {self.conditions}")
        if self.limitations:
            parts.append(f"Limitations: {self.limitations}")
        if self.eligibility:
            parts.append(f"Eligibility: {self.eligibility}")
        if self.waiting_period:
            parts.append(f"Waiting period: {self.waiting_period}")
        if self.is_optional:
            parts.append("Optional: Yes")
        if self.addon_name:
            parts.append(f"Add-on: {self.addon_name}")
        parts.append(f"Claim type: {self.claim_type}")
        parts.append(f"Evidence strength: {self.evidence_strength}")

        return "\n".join(parts)


@dataclass
class SearchQuery:
    query_text: str
    top_k: int = 5
    min_score: float = 0.25
    insurer: Optional[str] = None
    policy: Optional[str] = None
    category: Optional[str] = None
    claim_type: Optional[str] = None
    variant: Optional[str] = None
    evidence_strength: Optional[str] = None
    review_status: Optional[str] = None
    is_optional: Optional[bool] = None


@dataclass
class SearchResult:
    rank: int
    evidence_id: str
    score: float
    insurer: str
    policy: str
    variant: Optional[str]
    category: str
    feature: str
    claim: str
    value: Optional[str]
    unit: Optional[str]
    conditions: Optional[str]
    limitations: Optional[str]
    evidence_strength: str
    review_status: str
    source_document: str
    source_page: int
    source_section: str
    source_text: str
    is_flagged_for_review: bool = False
    review_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IndexManifest:
    schema_version: str
    embedding_model: str
    embedding_dimension: int
    normalized_embeddings: bool
    metric: str
    faiss_index_type: str
    source_matrix_path: str
    canonical_record_count: int
    eligible_record_count: int
    indexed_record_count: int
    excluded_record_count: int
    excluded_by_status: Dict[str, int]
    ordered_evidence_id_list: List[str]
    retrieval_config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalValidationReport:
    canonical_record_count: int
    eligible_record_count: int
    indexed_record_count: int
    excluded_record_count: int
    excluded_by_status: Dict[str, int]
    duplicate_evidence_ids: int
    missing_indexed_ids: int
    unexpected_indexed_ids: int
    embedding_model: str
    embedding_dimension: int
    normalized_embeddings: bool
    metric: str
    faiss_index_type: str
    top_k_default: int
    min_similarity_threshold_default: float
    test_count: int
    passed_tests: int
    failed_tests: int
    deterministic_rebuild_status: str
    representative_query_status: str
    validation_status: str
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
