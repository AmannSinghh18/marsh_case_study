import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from .config import RetrievalConfig
from .schemas import EvidenceRecord

logger = logging.getLogger(__name__)

class FAISSVectorIndex:
    """
    FAISS-backed vector index manager with metadata sidecar.
    Maintains deterministic mapping between vector positions and canonical evidence records.
    Automatically excludes records with review_status == 'rejected'.
    """
    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        self.index = None
        self.indexed_records: List[EvidenceRecord] = []
        self.dimension: int = self.config.embedding_dimension
        self.excluded_by_status: Dict[str, int] = {}

    def build_from_records(self, records: List[EvidenceRecord], embedder: Any) -> int:
        """
        Build index deterministically from list of EvidenceRecord objects.
        1. Sort records stably by evidence_id.
        2. Exclude rejected records.
        3. Convert records to searchable text strings.
        4. Generate normalized embeddings.
        5. Build FAISS IndexFlatIP (Inner Product = Cosine Similarity for normalized vectors).
        """
        # 1. Deterministic sorting by evidence_id
        sorted_records = sorted(records, key=lambda r: r.evidence_id)
        
        # 2. Status-based filtering (reject records with review_status == 'rejected')
        self.excluded_by_status = {"rejected": 0, "other": 0}
        eligible_records = []
        for r in sorted_records:
            if r.review_status in self.config.excluded_statuses:
                self.excluded_by_status[r.review_status] = self.excluded_by_status.get(r.review_status, 0) + 1
                logger.info(f"Excluding record {r.evidence_id} from vector index due to review_status={r.review_status}")
            else:
                eligible_records.append(r)
                
        self.indexed_records = eligible_records
        
        if not eligible_records:
            logger.warning("No eligible records found to index.")
            return 0

        # 3. Create searchable text
        searchable_texts = [r.to_searchable_text() for r in eligible_records]

        # 4. Generate embeddings
        embeddings = embedder.encode_texts(searchable_texts)
        self.dimension = embeddings.shape[1]

        # 5. Build FAISS index or NumPy fallback index
        try:
            import faiss
            # Inner Product index for unit-normalized vectors equals cosine similarity
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(embeddings)
            logger.info(f"Built FAISS IndexFlatIP with {self.index.ntotal} vectors of dimension {self.dimension}")
        except ImportError:
            logger.warning("faiss-cpu not available. Falling back to NumPy matrix cosine index.")
            self.index = _NumPyCosineIndex(embeddings)

        return len(eligible_records)

    def save(self, index_file: Optional[Path] = None, metadata_file: Optional[Path] = None):
        """
        Persist FAISS index and metadata to disk.
        """
        idx_path = index_file or self.config.index_file
        meta_path = metadata_file or self.config.metadata_file

        idx_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.parent.mkdir(parents=True, exist_ok=True)

        # Save vector index
        if self.index is not None:
            try:
                import faiss
                if isinstance(self.index, faiss.Index):
                    faiss.write_index(self.index, str(idx_path))
                else:
                    self.index.save(idx_path)
            except ImportError:
                if hasattr(self.index, "save"):
                    self.index.save(idx_path)

        # Save metadata sidecar deterministically
        meta_payload = {
            "dimension": self.dimension,
            "record_count": len(self.indexed_records),
            "excluded_by_status": self.excluded_by_status,
            "records": [r.to_dict() for r in self.indexed_records]
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully persisted index to {idx_path} and metadata to {meta_path}")

    def load(self, index_file: Optional[Path] = None, metadata_file: Optional[Path] = None) -> bool:
        """
        Load persisted vector index and metadata from disk.
        """
        idx_path = index_file or self.config.index_file
        meta_path = metadata_file or self.config.metadata_file

        if not meta_path.exists():
            logger.error(f"Metadata file not found: {meta_path}")
            return False

        with open(meta_path, "r", encoding="utf-8") as f:
            meta_payload = json.load(f)

        self.dimension = meta_payload.get("dimension", self.config.embedding_dimension)
        self.excluded_by_status = meta_payload.get("excluded_by_status", {})
        self.indexed_records = [EvidenceRecord.from_dict(r) for r in meta_payload["records"]]

        if idx_path.exists():
            try:
                import faiss
                self.index = faiss.read_index(str(idx_path))
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Could not load FAISS binary index ({e}). Trying NumPy fallback load.")
                self.index = _NumPyCosineIndex.load(idx_path)
        else:
            logger.warning(f"Vector index file missing: {idx_path}")
            return False

        return True

    def search_candidates(self, query_vector: np.ndarray, top_k: int) -> List[Tuple[EvidenceRecord, float]]:
        """
        Search vector index for top_k candidate matches.
        Returns list of (EvidenceRecord, similarity_score) tuples.
        """
        if self.index is None or len(self.indexed_records) == 0:
            return []

        k = min(top_k, len(self.indexed_records))
        if k <= 0:
            return []

        if hasattr(self.index, "search"):
            scores, indices = self.index.search(query_vector.astype(np.float32), k)
            scores_flat = scores[0]
            indices_flat = indices[0]
        else:
            scores_flat, indices_flat = self.index.search(query_vector.astype(np.float32), k)

        results = []
        for score, idx in zip(scores_flat, indices_flat):
            if idx < 0 or idx >= len(self.indexed_records):
                continue
            record = self.indexed_records[idx]
            results.append((record, float(score)))

        return results


class _NumPyCosineIndex:
    """Fallback index using NumPy matrix multiplication when faiss is not installed."""
    def __init__(self, embeddings: np.ndarray):
        self.embeddings = embeddings  # (N, D) normalized vectors
        self.ntotal = len(embeddings)

    def search(self, query_vector: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        # query_vector is (1, D) normalized
        sims = np.dot(self.embeddings, query_vector.T).flatten()  # (N,)
        top_k_idx = np.argsort(-sims)[:k]
        top_k_scores = sims[top_k_idx]
        return np.array([top_k_scores]), np.array([top_k_idx])

    def save(self, path: Path):
        np.save(str(path) + ".npy", self.embeddings)

    @classmethod
    def load(cls, path: Path) -> "_NumPyCosineIndex":
        npy_path = Path(str(path) + ".npy")
        if not npy_path.exists():
            npy_path = path
        embeddings = np.load(str(npy_path))
        return cls(embeddings)
