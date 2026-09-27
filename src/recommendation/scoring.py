"""
Transparent Fit Scoring & Tie-Break Engine (Phase 4 Correction 2)
Computes deterministic policy fit scores and executes transparent 5-step tie-break hierarchy.
"""

from typing import List, Dict, Any, Tuple
from src.recommendation.schemas import PolicyRequirementMatch, PolicyFitResult


IMPORTANCE_WEIGHTS = {
    "hard_requirement": 5.0,
    "important_requirement": 3.0,
    "preference": 1.0,
    "informational": 0.0
}

MATCH_MULTIPLIERS = {
    "MATCH": 1.0,
    "PARTIAL": 0.5,
    "NO_EVIDENCE": 0.0,
    "CONFLICT": -0.5,
    "REVIEW": 0.25
}


def calculate_tie_break_metrics(
    insurer: str,
    policy: str,
    requirement_matches: List[PolicyRequirementMatch]
) -> Dict[str, Any]:
    """
    Computes tie-break metrics according to defined hierarchy:
    1. Total Fit Score
    2. Hard Requirement Score (REQ-001, REQ-002)
    3. Important Requirement Score (REQ-003, REQ-004, REQ-005)
    4. Direct Evidence Specificity Count
    5. Alphabetical Insurer Name
    """
    total_fit_score = sum(m.score_contribution for m in requirement_matches)
    
    hard_req_score = sum(
        m.score_contribution for m in requirement_matches
        if m.requirement_id in ["REQ-001", "REQ-002"]
    )
    
    important_req_score = sum(
        m.score_contribution for m in requirement_matches
        if m.requirement_id in ["REQ-003", "REQ-004", "REQ-005"]
    )
    
    # Direct evidence specificity: count of direct non-empty evidence IDs supporting hard requirements
    direct_evidence_count = sum(
        len(m.evidence_ids) for m in requirement_matches
        if m.requirement_id in ["REQ-001", "REQ-002"] and m.match_status == "MATCH"
    )
    
    return {
        "total_fit_score": round(total_fit_score, 2),
        "hard_req_score": round(hard_req_score, 2),
        "important_req_score": round(important_req_score, 2),
        "direct_evidence_count": direct_evidence_count,
        "insurer_name": insurer
    }


def sort_policies_with_tie_break(
    policy_fit_results: List[PolicyFitResult]
) -> List[PolicyFitResult]:
    """
    Sorts policy fit results deterministically using the 5-step tie-break key.
    Sorting Key (descending for scores, ascending for insurer name):
    (-total_fit_score, -hard_req_score, -important_req_score, -direct_evidence_count, insurer_name)
    """
    def sorting_key(result: PolicyFitResult):
        metrics = calculate_tie_break_metrics(
            result.insurer, result.policy, result.requirement_matches
        )
        return (
            -metrics["total_fit_score"],
            -metrics["hard_req_score"],
            -metrics["important_req_score"],
            -metrics["direct_evidence_count"],
            metrics["insurer_name"]
        )

    sorted_results = sorted(policy_fit_results, key=sorting_key)
    
    # Assign deterministic overall ranks
    for idx, r in enumerate(sorted_results):
        r.overall_rank = idx + 1
        
    return sorted_results
