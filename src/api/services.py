"""
FastAPI Data Services (Phase 4 Stage 4I)
Loads pre-computed, validated artifacts from data/processed/.
"""

import json
import os
from typing import Dict, Any, List, Optional


def load_json_artifact(filename: str) -> Dict[str, Any]:
    path = os.path.join("data", "processed", filename)
    if not os.path.exists(path):
        return {"error": f"Artifact {filename} not found."}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_canonical_evidence_list() -> List[Dict[str, Any]]:
    path = os.path.join("data", "processed", "policy_evidence_matrix.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_evidence_by_id(evidence_id: str) -> Optional[Dict[str, Any]]:
    records = load_canonical_evidence_list()
    for r in records:
        if r.get("evidence_id", "").lower() == evidence_id.lower():
            return r
    return None
