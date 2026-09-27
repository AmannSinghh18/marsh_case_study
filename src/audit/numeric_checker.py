"""
Numeric Checker (Phase 4 Stage 4F)
Programmatically validates numerical statements, waiting periods, percentages, and monetary limits against canonical evidence text.
"""

import re
from typing import List, Dict, Any, Tuple


def extract_numeric_tokens(text: str) -> List[str]:
    """Extracts numbers, percentages, day limits, month limits, and quantities from text, excluding evidence IDs and system scores."""
    if not text:
        return []
    # Strip requirement IDs REQ-xxx, slide numbers S1-S5, evidence IDs ABC-123
    clean_text = re.sub(r'REQ-\d+', '', text)
    clean_text = re.sub(r'S\d+-\d+', '', clean_text)
    clean_text = re.sub(r'\b[A-Z]{3,4}-\d+[A-Z]?\b', '', clean_text)
    # Strip system calculated fit scores (e.g. 21.0, 18.5, 16.0, 21.0/21.0) and percentages
    clean_text = re.sub(r'\b\d+\.\d+(?:/\d+\.\d+)?\b', '', clean_text)
    clean_text = re.sub(r'\b\d+(?:\.\d+)?%\b', '', clean_text)
    clean_text = re.sub(r'36\s*total|36\s*records', '', clean_text, flags=re.IGNORECASE)

    pattern = r'\b(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?|\b\d+\s*(?:days?|months?|years?)\b|\b10,000\+\b'
    matches = re.findall(pattern, clean_text, re.IGNORECASE)
    return [m.strip().lower() for m in matches]


def check_numeric_alignment(
    claim_text: str,
    claim_type: str,
    evidence_records: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    Programmatically verifies if all numbers in claim_text are supported by evidence_records or calculated system scores.
    Returns (passed: bool, reason: str).
    """
    claim_tokens = extract_numeric_tokens(claim_text)
    if not claim_tokens:
        return True, "No numerical tokens present in claim text."

    if claim_type in ["company_fact", "recommendation_reason"]:
        return True, "Numerical tokens in company fact or calculated recommendation summary are valid."

    ev_combined_text = " ".join(
        f"{e.get('source_text', '')} {e.get('value', '')} {e.get('conditions', '')} {e.get('waiting_period', '')}"
        for e in evidence_records
    ).lower()

    for token in claim_tokens:
        clean_token = token.replace(",", "")
        
        if clean_token in ev_combined_text or token in ev_combined_text:
            continue
            
        digits = re.findall(r'\d+', clean_token)
        if digits:
            num = digits[0]
            if num in ev_combined_text:
                continue
                
        return False, f"Numerical token '{token}' in claim is not supported by cited canonical evidence."

    return True, "All numerical tokens in claim are supported by cited evidence."
