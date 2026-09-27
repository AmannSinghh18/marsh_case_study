import logging
import numpy as np
from typing import List
from .config import RetrievalConfig

logger = logging.getLogger(__name__)

class PolicyEvidenceEmbedder:
    """
    Wrapper for local sentence embedding generation.
    Uses SentenceTransformer (e.g. all-MiniLM-L6-v2) for CPU-friendly,
    deterministic local vector encoding with unit normalization for Cosine/L2 indexing.
    Includes TF-IDF / SVD fallback for maximum robustness across local environments.
    """
    def __init__(self, model_name: str = RetrievalConfig.embedding_model_name):
        self.model_name = model_name
        self._model = None
        self._fallback_tfidf = None
        self._fallback_svd = None
        self._dimension = RetrievalConfig.embedding_dimension
        self._use_fallback = False

    @property
    def model(self):
        if self._model is None and not self._use_fallback:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
                dim_fn = getattr(self._model, "get_embedding_dimension", None) or getattr(self._model, "get_sentence_embedding_dimension", lambda: 384)
                self._dimension = dim_fn()
            except Exception as e:
                logger.warning(f"SentenceTransformer not available ({e}). Using scikit-learn TF-IDF SVD fallback embedder.")
                self._use_fallback = True
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of text strings into normalized 2D numpy array of shape (N, D).
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        if self.model is not None and not self._use_fallback:
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.astype(np.float32)
        else:
            # TF-IDF + TruncatedSVD fallback
            return self._encode_fallback(texts, is_query=False)

    def encode_query(self, query_text: str) -> np.ndarray:
        """
        Encode a single query string into a normalized 2D numpy array of shape (1, D).
        """
        cleaned_query = " ".join(query_text.split())
        if not cleaned_query:
            return np.zeros((1, self.dimension), dtype=np.float32)

        if self.model is not None and not self._use_fallback:
            embeddings = self.model.encode(
                [cleaned_query],
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.astype(np.float32)
        else:
            return self._encode_fallback([cleaned_query], is_query=True)

    def _encode_fallback(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        if not is_query or self._fallback_tfidf is None:
            self._fallback_tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            tfidf_mat = self._fallback_tfidf.fit_transform(texts)
            n_components = min(self.dimension, tfidf_mat.shape[1] - 1)
            if n_components > 1:
                self._fallback_svd = TruncatedSVD(n_components=n_components, random_state=42)
                dense = self._fallback_svd.fit_transform(tfidf_mat)
            else:
                dense = tfidf_mat.toarray()

            # Pad or truncate to self.dimension
            if dense.shape[1] < self.dimension:
                pad = np.zeros((dense.shape[0], self.dimension - dense.shape[1]), dtype=np.float32)
                dense = np.hstack([dense, pad])
            else:
                dense = dense[:, :self.dimension]
        else:
            tfidf_mat = self._fallback_tfidf.transform(texts)
            if self._fallback_svd is not None:
                dense = self._fallback_svd.transform(tfidf_mat)
            else:
                dense = tfidf_mat.toarray()

            if dense.shape[1] < self.dimension:
                pad = np.zeros((dense.shape[0], self.dimension - dense.shape[1]), dtype=np.float32)
                dense = np.hstack([dense, pad])
            else:
                dense = dense[:, :self.dimension]

        # L2 normalize
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = dense / norms
        return normalized.astype(np.float32)
