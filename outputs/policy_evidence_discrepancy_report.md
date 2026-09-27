# Phase 2 Policy Evidence Matrix — Provenance Audit & Discrepancy Report

## Executive Summary
This report documents the structural re-alignment and hard provenance audit executed on the Phase 2 Policy Evidence Matrix. Every material assertion across all structured fields (`claim`, `conditions`, `limitations`, `eligibility`, `waiting_period`, `variant`, `value`, `unit`, `addon_name`) has been audited and strictly matched against verbatim contiguous `source_text` excerpts from `data/processed/policy_pages.json`.

---

## Key Metrics
- **Initial Record Count**: 31 records
- **Final Record Count**: **36 records**
- **Records Split**: **5 records** (split into 10 distinct records)
- **Records Source Text Expanded**: **11 records**
- **Records Rejected**: **0 records**
- **Final Verification Status**: **100% verified (36/36 records)**

---

## 1. Records Split
The following records contained multiple distinct brochure assertions that could not be supported by a single contiguous source excerpt:
- **`ABHI-003`** -> Split into `ABHI-003A` (Out-of-pocket 100% claim on Page 1) and `ABHI-003B` (Annexure I List 1-4 footnote on Page 2).
- **`ABHI-007`** -> Split into `ABHI-007A` (Sum Insured range 5L-6 Cr) and `ABHI-007B` (Maternity limits footnote %).
- **`ABHI-008`** -> Split into `ABHI-008A` (SAVR Plan Section 80D Tax Savings) and `ABHI-008B` (SAVR Plan Hospi Cash).
- **`CARE-001`** -> Split into `CARE-001A` (Base Cumulative Bonus 50%) and `CARE-001B` (Add-on Cumulative Bonus Super 100%).
- **`NIVA-007`** -> Split into `NIVA-007A` (30 Mins Cashless Pre-Auth Commitment) and `NIVA-007B` (10,000+ Network Hospitals Footprint).

---

## 2. Records with Expanded Source Text
The following records had their `source_text` expanded to include exact, contiguous verbatim blocks from the PDF page clean text:
- **`ABHI-003A`** (Page 1): Added exact block covering out-of-pocket non-medical expenses.
- **`ABHI-004`** (Page 1): Added exact block covering 10,000 steps/day and 300 calories/session.
- **`ABHI-005`** (Page 2): Added exact block listing all 7 chronic conditions.
- **`CARE-003`** (Page 2): Added exact table block covering Unlimited Automatic Recharge.
- **`CARE-005`** (Page 3): Added exact block listing all pre-existing conditions for Instant Cover.
- **`CARE-007`** (Page 3): Added exact block covering GP and Specialist consultation sub-limits.
- **`CARE-008`** (Page 2): Added exact Eligibility Criteria table covering ages, floater rules, and Zones 1-7.
- **`HDFC-007`** (Page 5): Added exact table covering Individual and Floater check-up sub-limits.
- **`HDFC-008`** (Page 7): Added exact table covering deductible amounts 25,000 to 5,00,000.
- **`NIVA-002`** (Page 2): Added table header variant tokens for Titanium+.
- **`NIVA-003`** (Page 2): Added table header variant tokens for Platinum.

---

## 3. Strict 8-Point Provenance Verification Result
All **36 evidence records** passed strict 8-point automated validation with zero missing tokens, zero paraphrased assertions, and zero fact manufacturing.
