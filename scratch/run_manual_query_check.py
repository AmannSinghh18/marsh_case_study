import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from src.retrieval.config import RetrievalConfig
from src.retrieval.embedder import PolicyEvidenceEmbedder
from src.retrieval.index import FAISSVectorIndex
from src.retrieval.retriever import PolicyEvidenceRetriever
from src.retrieval.query import print_search_results

def run_all_checks():
    config = RetrievalConfig()
    embedder = PolicyEvidenceEmbedder(config.embedding_model_name)
    index = FAISSVectorIndex(config)
    index.load()

    retriever = PolicyEvidenceRetriever(config=config, embedder=embedder, index=index)

    queries = [
        "maternity coverage and waiting period",
        "restore or refill of sum insured",
        "room rent or room category restrictions",
        "network hospital availability",
        "health-related rewards or wellness benefits",
        "pre and post hospitalization coverage"
    ]

    for idx, q in enumerate(queries, 1):
        print(f"\n================================================================================")
        print(f" MANDATORY QUERY {idx}: \"{q}\"")
        print(f"================================================================================")
        results = retriever.search(q, top_k=3, min_score=0.20)
        print_search_results(results)

if __name__ == "__main__":
    run_all_checks()
