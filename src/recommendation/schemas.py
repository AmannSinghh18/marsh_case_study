"""
Pydantic Schemas for Recommendation Engine & Policy Fit Matrix (Phase 4 Stage 4C-4E)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AssumptionItem(BaseModel):
    assumption_id: str
    assumption: str
    why_needed: str
    effect_on_analysis: str
    confidence: str


class RequirementItem(BaseModel):
    requirement_id: str
    risk_area: str
    requirement: str
    rationale: str
    importance: str  # hard_requirement, important_requirement, preference, informational
    source_type: str = "case_profile"
    source_reference: str
    required_policy_features: List[str]
    preferred_policy_features: List[str]
    hard_constraints: List[str]
    assumptions: List[str] = Field(default_factory=list)
    confidence: str = "high"
    evidence_ids: List[str] = Field(default_factory=list)


class PolicyRequirementMatch(BaseModel):
    requirement_id: str
    risk_area: str
    policy: str
    insurer: str
    match_status: str  # MATCH, PARTIAL, NO_EVIDENCE, CONFLICT, REVIEW
    score_contribution: float
    max_possible_score: float
    evidence_ids: List[str]
    matching_features: List[str]
    qualifiers_and_limitations: List[str]
    match_reasoning: str


class PolicyFitResult(BaseModel):
    insurer: str
    policy: str
    total_fit_score: float
    max_possible_score: float
    percentage_score: float
    requirement_matches: List[PolicyRequirementMatch]
    key_strengths: List[str]
    key_limitations: List[str]
    key_tradeoffs: List[str]
    overall_rank: int


class RecommendationResult(BaseModel):
    recommended_policy: str
    insurer: str
    recommendation_summary: str
    requirement_scores: Dict[str, float]
    total_fit_score: float
    percentage_score: float
    key_strengths: List[str]
    key_tradeoffs: List[str]
    key_limitations: List[str]
    assumptions: List[AssumptionItem]
    evidence_ids: List[str]
    confidence: str
    decision_trace: List[Dict[str, Any]]
    alternative_policy_comparison: List[Dict[str, Any]]
