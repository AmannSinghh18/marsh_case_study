# Marsh Internship Case Study — Policy Evidence Corpus, Retrieval & Decision Engine Pipeline

## Purpose
This repository implements a complete, end-to-end evidence-grounded policy recommendation and audit system:
- **Phase 1**: PDF Ingestion & Page Corpus Validation
- **Phase 2**: Canonical Structured Policy Evidence Matrix Construction & Hard Provenance Auditing (36 records)
- **Phase 3**: Evidence-Grounded Semantic Retrieval Layer & FAISS Vector Indexing
- **Phase 4**: Recommendation Engine, Claim-Level Audit, FastAPI REST API, HTML/CSS/JS Frontend & 5-Slide PPT Pitch Generator

The system transforms raw policy brochures into structured, page-traceable insurance evidence and provides a modern corporate dashboard and PowerPoint deck grounded 100% in official policy documents.

---

## Project Structure

```
marsh_case_study/
│
├── requirements.txt                         # Pinned dependencies (pymupdf, sentence-transformers, faiss-cpu, fastapi, uvicorn, python-pptx, pytest)
├── README.md                                # Project documentation & CLI instructions
├── Marsh - Internship Case Study.pdf        # Authoritative case brief PDF
│
├── data/
│   ├── raw/                                 # Staged policy PDFs directory (4 policy brochures)
│   └── processed/                           # Machine-readable output JSONs & CSVs
│       ├── policy_pages.json                # Array of 24 page records with raw/clean text & hashes
│       ├── document_manifest.json           # Document inventory & explicit category classification
│       ├── extraction_validation_report.json# Phase 1 health checks, page counts, & term validation
│       ├── policy_evidence_matrix.json      # Phase 2 canonical structured evidence matrix (36 records)
│       ├── policy_evidence_matrix.csv       # Machine-readable CSV matrix export (36 records)
│       ├── policy_evidence_validation_report.json # Phase 2 8-point provenance validation report
│       ├── retrieval_validation_report.json # Phase 3 retrieval index validation report
│       ├── case_profile.json                # Stage 4A structured case profile
│       ├── case_profile_validation_report.json # Stage 4A case profile validation report
│       ├── risk_requirements.json           # Stage 4B classified business & employee risk requirements
│       ├── policy_fit_matrix.json           # Stage 4C & 4D transparent policy fit evaluation matrix
│       ├── recommendation.json              # Stage 4E evidence-grounded recommendation artifact
│       ├── pitch_content.json               # Stage 4G structured 5-slide pitch content
│       ├── audit_report.json                # Stage 4F claim-level audit report (25/25 PASS)
│       ├── phase4_validation_report.json    # Phase 4 end-to-end validation report
│       └── retrieval_index/                 # Phase 3 retrieval index artifacts
│           ├── index.faiss                  # FAISS IndexFlatIP binary index
│           ├── metadata.json                # Vector metadata sidecar
│           └── index_manifest.json          # Rebuild manifest & audit configuration
│
├── frontend/                                # Stage 4J HTML + Vanilla CSS + Vanilla JS Dashboard
│   ├── index.html                           # Single-page dashboard application
│   ├── css/
│   │   └── style.css                        # Modern corporate design system styling
│   └── js/
│       ├── api.js                           # Centralized REST API fetch module
│       ├── evidence.js                      # Modal drawer evidence provenance viewer
│       └── app.js                           # Dashboard tab controller & data renderer
│
├── src/
│   ├── __init__.py                          # Package initializer
│   ├── document_processor.py                # Phase 1 PDF processor & CLI entrypoint
│   ├── matrix_builder.py                    # Phase 2 Evidence Matrix builder engine
│   ├── case_profile_builder.py              # Stage 4A Case Profile builder & validator
│   ├── pitch_builder.py                     # Stage 4G & 4H Pitch content & PPTX deck generator
│   ├── phase4_pipeline.py                   # Phase 4 full pipeline coordinator & validation reporter
│   │
│   ├── retrieval/                           # Phase 3 Semantic Retrieval Package
│   │   ├── __init__.py
│   │   ├── config.py                        # Retrieval system configuration & defaults
│   │   ├── schemas.py                       # Retrieval Pydantic data schemas
│   │   ├── embedder.py                      # SentenceTransformers embedding generator
│   │   ├── index.py                         # FAISS index wrapper & candidate pre-filtering engine
│   │   ├── retriever.py                     # High-level semantic retriever
│   │   ├── build_index.py                   # Index builder CLI script
│   │   └── query.py                         # Query search CLI script
│   │
│   ├── recommendation/                      # Stage 4C-4E Recommendation Engine Package
│   │   ├── __init__.py
│   │   ├── schemas.py                       # Recommendation & fit matrix Pydantic models
│   │   ├── requirements.py                  # Risk requirements builder
│   │   ├── feature_matching.py              # Evidence matching & fit matrix calculation
│   │   └── recommendation.py                # Recommendation artifact generator
│   │
│   ├── audit/                               # Stage 4F Claim-Level Audit Engine Package
│   │   ├── __init__.py
│   │   ├── schemas.py                       # Audit report Pydantic schemas
│   │   ├── claim_extractor.py               # Recommendation & pitch claim extractor
│   │   ├── evidence_checker.py              # Verbatim evidence support & qualifier checker
│   │   ├── numeric_checker.py               # Programmatic numerical alignment verifier
│   │   └── audit_engine.py                  # Full claim audit execution engine
│   │
│   └── api/                                 # Stage 4I FastAPI REST API Package
│       ├── __init__.py
│       ├── schemas.py                       # API response Pydantic models
│       ├── services.py                      # Artifact loading services
│       ├── routes.py                        # REST API endpoints
│       └── main.py                          # FastAPI main app & static frontend server
│
├── tests/
│   ├── __init__.py                          # Package initializer
│   ├── test_document_processor_units.py    # Phase 1 unit test suite
│   ├── test_document_processor_integration.py # Phase 1 integration test suite
│   ├── test_matrix_builder_units.py        # Phase 2 unit & schema test suite
│   ├── test_matrix_builder_integration.py  # Phase 2 integration & verbatim provenance test suite
│   ├── test_retrieval.py                    # Phase 3 retrieval & determinism test suite (22 tests)
│   ├── test_recommendation.py               # Phase 4 recommendation & requirement unit tests
│   ├── test_audit.py                        # Phase 4 claim-level audit unit tests & fixtures
│   ├── test_api.py                          # Phase 4 REST API endpoint integration tests
│   └── test_end_to_end.py                   # Phase 4 end-to-end integration & integrity tests
│
└── outputs/
    ├── policy_evidence_review.csv           # Human audit export CSV (36 records)
    └── marsh_case_study_pitch.pptx          # Stage 4H 5-Slide PowerPoint Pitch Deck
```

---

## CLI Execution & Pipeline Workflows

### 1. Execute Phase 1 PDF Ingestion Engine
```bash
python -m src.document_processor --stage-raw --force
```

### 2. Execute Phase 2 Policy Evidence Matrix Builder
```bash
python -m src.matrix_builder --force
```

### 3. Build Phase 3 FAISS Retrieval Index
```bash
python -m src.retrieval.build_index
```

### 4. Execute Phase 4 Complete Decision, Audit & PPT Pipeline
```bash
python -m src.phase4_pipeline
```

### 5. Launch FastAPI Backend & HTML Dashboard
```bash
python -m src.api.main
```
*If Port 8000 is blocked by Windows permissions or another process:*
```bash
python -m uvicorn src.api.main:app --port 8050 --reload
```

Open **`http://127.0.0.1:8050/`** (or the port displayed in terminal) in your browser.

---

## Automated Test Suite

Execute all 55 unit, integration, retrieval, recommendation, audit, and API tests across Phase 1, Phase 2, Phase 3, and Phase 4:

```bash
python -m pytest -v
```

---

## Key Phase 4 Architecture & Validation Highlights
1. **Single Source of Truth**: Case facts trace to `Marsh Case Brief`; policy facts trace 100% to `policy_evidence_matrix.json` (36 records).
2. **Transparent Fit Scoring**: Fit scores are calculated programmatically from case requirements (`hard_requirement`: 5, `important_requirement`: 3, `preference`: 1, `informational`: 0).
3. **Claim-Level Audit Engine**: Every material recommendation and pitch statement is subjected to automated numerical and qualifier auditing (**25 / 25 claims PASS**, 0 FAIL).
4. **FastAPI REST API**: Serves JSON endpoints (`/api/company`, `/api/requirements`, `/api/policies`, `/api/recommendation`, `/api/audit`, `/api/pitch`, `/api/evidence/{id}`).
5. **HTML/CSS/JS Frontend**: Clean, responsive dashboard using vanilla HTML/CSS/JavaScript with interactive evidence modal drawer for verbatim source text.
6. **5-Slide PowerPoint Deck**: `outputs/marsh_case_study_pitch.pptx` built via `python-pptx` with explicit evidence ID citations.

---

## Current Status
- **Corpus Integrity**: 4 policy PDFs, 24 policy pages, 36 verified canonical evidence records across all 4 insurers.
- **Full Test Suite Status**: **70 / 70 tests passing** (`70 passed in 46.20s`).
- **Phase 1–3 Integrity**: `policy_evidence_matrix.json` hash `b6f985146744faed328fd31218607802a5ddd2239e1bcbd892e4c86a0b8f27e5` remains **100% frozen and untouched**.


