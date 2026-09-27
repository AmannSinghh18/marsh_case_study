from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
RETRIEVAL_INDEX_DIR = DATA_PROCESSED_DIR / "retrieval_index"

@dataclass(frozen=True)
class RetrievalConfig:
    canonical_matrix_path: Path = DATA_PROCESSED_DIR / "policy_evidence_matrix.json"
    index_dir: Path = RETRIEVAL_INDEX_DIR
    index_file: Path = RETRIEVAL_INDEX_DIR / "index.faiss"
    metadata_file: Path = RETRIEVAL_INDEX_DIR / "metadata.json"
    manifest_file: Path = RETRIEVAL_INDEX_DIR / "index_manifest.json"
    report_file: Path = DATA_PROCESSED_DIR / "retrieval_validation_report.json"
    
    # Embedding settings
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    normalized_embeddings: bool = True
    
    # Vector store index settings
    metric: str = "cosine_similarity"
    faiss_index_type: str = "IndexFlatIP"
    
    # Default search settings
    default_top_k: int = 5
    default_min_similarity_threshold: float = 0.25
    
    # Review Status Filtering Rules
    excluded_statuses: tuple = ("rejected",)
    flagged_statuses: tuple = ("review_required",)
