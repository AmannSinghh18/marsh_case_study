import argparse
import json
import logging
from typing import Optional, List
from .config import RetrievalConfig
from .embedder import PolicyEvidenceEmbedder
from .index import FAISSVectorIndex
from .retriever import PolicyEvidenceRetriever
from .schemas import SearchResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def execute_search_query(
    query_text: str,
    top_k: int = 5,
    min_score: float = 0.25,
    insurer: Optional[str] = None,
    policy: Optional[str] = None,
    category: Optional[str] = None,
    claim_type: Optional[str] = None,
    variant: Optional[str] = None,
    is_optional: Optional[bool] = None,
    config: Optional[RetrievalConfig] = None
) -> List[SearchResult]:
    """
    Load vector index, execute query, and return SearchResult list.
    """
    cfg = config or RetrievalConfig()
    embedder = PolicyEvidenceEmbedder(cfg.embedding_model_name)
    index = FAISSVectorIndex(cfg)

    if not index.load():
        logger.error("Failed to load vector index. Building index on the fly...")
        from .build_index import build_retrieval_index
        build_retrieval_index(config=cfg)
        index.load()

    retriever = PolicyEvidenceRetriever(config=cfg, embedder=embedder, index=index)
    results = retriever.search(
        query_text=query_text,
        top_k=top_k,
        min_score=min_score,
        insurer=insurer,
        policy=policy,
        category=category,
        claim_type=claim_type,
        variant=variant,
        is_optional=is_optional
    )
    return results

def print_search_results(results: List[SearchResult]):
    """
    Print retrieval results in clean, unparaphrased terminal output format as required by item 13.
    """
    if not results:
        print("\n[RESULT]: No sufficiently relevant evidence found matching the query criteria.")
        return

    print(f"\n{'='*80}")
    print(f" RETRIEVAL RESULTS ({len(results)} records found)")
    print(f"{'='*80}")

    for r in results:
        flag_str = " [FLAGGED FOR REVIEW]" if r.is_flagged_for_review else ""
        print(f"Rank {r.rank} | Evidence ID: {r.evidence_id} | Similarity Score: {r.score:.4f}{flag_str}")
        print(f"Insurer:        {r.insurer}")
        print(f"Policy:         {r.policy}" + (f" (Variant: {r.variant})" if r.variant else ""))
        print(f"Feature:        {r.feature}")
        print(f"Claim:          {r.claim}")
        print(f"Page:           {r.source_document} Page {r.source_page}")
        print(f"Source Section: {r.source_section}")
        print(f"Review Status:  {r.review_status}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Query Policy Evidence Retrieval Engine")
    parser.add_argument("--query", type=str, required=True, help="Search query string")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum number of evidence results to return")
    parser.add_argument("--min-score", type=float, default=0.25, help="Minimum similarity threshold")
    parser.add_argument("--insurer", type=str, default=None, help="Filter by insurer name")
    parser.add_argument("--policy", type=str, default=None, help="Filter by policy name")
    parser.add_argument("--category", type=str, default=None, help="Filter by evidence category")
    parser.add_argument("--claim-type", type=str, default=None, help="Filter by claim type")
    parser.add_argument("--variant", type=str, default=None, help="Filter by product variant")
    parser.add_argument("--is-optional", action="store_true", default=None, help="Filter for optional add-on benefits")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    results = execute_search_query(
        query_text=args.query,
        top_k=args.top_k,
        min_score=args.min_score,
        insurer=args.insurer,
        policy=args.policy,
        category=args.category,
        claim_type=args.claim_type,
        variant=args.variant,
        is_optional=args.is_optional
    )

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print_search_results(results)

if __name__ == "__main__":
    main()
