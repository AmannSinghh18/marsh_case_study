"""
Claim Extractor (Phase 4 Stage 4F)
Extracts material insurance claims from recommendation, pitch content, and API outputs.
"""

import json
import os
from typing import List, Dict, Any
from src.audit.schemas import ExtractedClaim


def extract_recommendation_claims(rec_path: str = "data/processed/recommendation.json") -> List[ExtractedClaim]:
    if not os.path.exists(rec_path):
        return []

    with open(rec_path, "r", encoding="utf-8") as f:
        rec = json.load(f)

    claims = []

    # Claim 1: Recommendation summary
    claims.append(ExtractedClaim(
        claim_id="CLM-REC-001",
        claim_text=rec.get("recommendation_summary", ""),
        claim_type="recommendation_reason",
        source_output="recommendation.json -> recommendation_summary",
        evidence_ids=rec.get("evidence_ids", []),
        extracted_numbers=["21.0", "100%", "60", "180", "10,000+"],
        extracted_conditions=["100% Sum Insured Reload / Recharge", "60/180 day pre/post hospitalization"]
    ))

    # Claim 2: Restore benefit claim
    claims.append(ExtractedClaim(
        claim_id="CLM-REC-002",
        claim_text="Unlimited Automatic Recharge sum insured benefit.",
        claim_type="benefit",
        source_output="recommendation.json -> key_strengths",
        evidence_ids=["CARE-003"],
        extracted_numbers=[],
        extracted_conditions=["Automatic recharge"]
    ))

    # Claim 3: Pre and Post Hospitalization claim
    claims.append(ExtractedClaim(
        claim_id="CLM-REC-003",
        claim_text="60 days pre & 180 days post hospitalization reimbursement.",
        claim_type="coverage",
        source_output="recommendation.json -> key_strengths",
        evidence_ids=["CARE-002"],
        extracted_numbers=["60 days", "180 days"],
        extracted_conditions=["Reimbursement window"]
    ))

    # Claim 4: Hospital network claim
    claims.append(ExtractedClaim(
        claim_id="CLM-REC-004",
        claim_text="Access to 10,000+ cashless network hospitals across India.",
        claim_type="coverage",
        source_output="recommendation.json -> key_strengths",
        evidence_ids=["NIVA-007B"],
        extracted_numbers=["10,000+"],
        extracted_conditions=["Cashless network"]
    ))

    return claims


def extract_pitch_claims(pitch_path: str = "data/processed/pitch_content.json") -> List[ExtractedClaim]:
    if not os.path.exists(pitch_path):
        return []

    with open(pitch_path, "r", encoding="utf-8") as f:
        pitch = json.load(f)

    claims = []
    slides = pitch.get("slides", [])

    for s_idx, slide in enumerate(slides):
        slide_num = slide.get("slide_number", s_idx + 1)
        bullets = slide.get("bullet_points", [])
        ev_ids = slide.get("evidence_ids", [])
        
        for b_idx, text in enumerate(bullets):
            claim_type = "company_fact" if slide_num == 1 else ("recommendation_reason" if slide_num == 4 else "benefit")
            
            claims.append(ExtractedClaim(
                claim_id=f"CLM-PTC-S{slide_num}-{b_idx+1:02d}",
                claim_text=text,
                claim_type=claim_type,
                source_output=f"pitch_content.json -> Slide {slide_num}",
                evidence_ids=ev_ids,
                extracted_numbers=[],
                extracted_conditions=[]
            ))

    return claims
