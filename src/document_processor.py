import os
import sys
import json
import re
import shutil
import pathlib
import hashlib
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple

import pymupdf  # PyMuPDF

# Ensure UTF-8 output encoding for standard streams on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("document_processor")

# Known policy brochure fingerprints
KNOWN_POLICY_CATALOG: Dict[str, str] = {
    "ABHI Product Brochure.pdf": "ABHI Activ One Product Brochure",
    "Care Health Product Brochure.pdf": "Care Supreme Product Brochure",
    "HDFC Product Brochure.pdf": "HDFC ERGO Optima Secure+ Brochure",
    "Niva Bupa Product Brochure.pdf": "Niva Bupa ReAssure 2.0 Brochure"
}

# Mandatory terms for critical insurance coverage validation
CRITICAL_INSURANCE_TERMS: List[Tuple[str, str]] = [
    ("Currency Symbol (₹)", r"₹"),
    ("Currency Code (INR)", r"INR"),
    ("Percentage (%)", r"%"),
    ("Multiplier (2X)", r"2X"),
    ("Multiplier (3X-6X)", r"[3-6]X"),
    ("Day Period (days)", r"\bdays?\b"),
    ("Month Period (months)", r"\bmonths?\b"),
    ("Year Period (years)", r"\byears?\b"),
    ("Waiting Period", r"\bwait(?:ing)?\s+period\b"),
    ("Sum Insured", r"\bsum\s+insured\b")
]


def compute_file_sha256(filepath: pathlib.Path) -> str:
    """Compute SHA-256 digest of a file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_text_sha256(text: str) -> str:
    """Compute deterministic sha256 hash of text content."""
    return f"sha256_{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def slugify_filename(filename: str) -> str:
    """Convert filename to a clean deterministic slug."""
    stem = pathlib.Path(filename).stem
    slug = re.sub(r"[^\w\s-]", "", stem).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)


def normalize_text_conservatively(raw_text: str) -> str:
    """
    Perform loss-minimizing, conservative text normalization.
    Preserves all numbers, currency symbols, multipliers, punctuation, and line breaks.
    """
    if not raw_text:
        return ""
    
    # 1. Standardize line endings CRLF -> LF
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 2. Convert non-breaking space \xa0 to standard space
    text = text.replace("\xa0", " ")
    
    # 3. Strip trailing spaces from each line while keeping indentation
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    
    # 4. Collapse 3+ consecutive newlines down to 2 (preserving paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


class DocumentProcessor:
    """
    Page-aware PDF discovery, extraction, document classification, hashing,
    and validation pipeline.
    """

    def __init__(self, input_dir: pathlib.Path, output_dir: pathlib.Path, force: bool = False):
        self.input_dir = pathlib.Path(input_dir).resolve()
        self.output_dir = pathlib.Path(output_dir).resolve()
        self.force = force
        self.workspace_root = self.input_dir.parent.parent if self.input_dir.name == "raw" else self.input_dir.parent

    def stage_raw_data(self) -> None:
        """
        Explicit helper to stage raw policy PDFs from 'Policy Documents' into 'data/raw'
        if data/raw is missing or empty.
        """
        self.input_dir.mkdir(parents=True, exist_ok=True)
        policy_docs_dir = self.workspace_root / "Policy Documents"
        
        if policy_docs_dir.exists() and policy_docs_dir.is_dir():
            for pdf_file in policy_docs_dir.glob("*.pdf"):
                dest_file = self.input_dir / pdf_file.name
                if not dest_file.exists() or self.force:
                    shutil.copy2(pdf_file, dest_file)
                    logger.info(f"Staged policy brochure: {pdf_file.name} -> {dest_file}")

    def discover_documents(self) -> Tuple[List[pathlib.Path], Optional[pathlib.Path]]:
        """
        Discover all PDF files in input_dir and locate case brief file.
        Returns sorted tuple: (policy_pdf_paths, case_brief_pdf_path)
        """
        pdf_paths = sorted(list(self.input_dir.glob("*.pdf")))
        
        case_brief_path = None
        # Check if case brief is in input_dir or workspace root
        for candidate_dir in [self.input_dir, self.workspace_root]:
            case_brief_candidates = list(candidate_dir.glob("*Case Study*.pdf")) + list(candidate_dir.glob("*Specification*.pdf"))
            if case_brief_candidates:
                case_brief_path = case_brief_candidates[0]
                break
                
        return pdf_paths, case_brief_path

    def process(self) -> bool:
        """
        Execute full PDF discovery, extraction, manifest creation, and validation reporting.
        Returns True if validation status is PASSED, False otherwise.
        """
        logger.info("Starting Marsh PDF Ingestion & Validation Pipeline...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        policy_pdf_paths, case_brief_path = self.discover_documents()

        if not policy_pdf_paths:
            logger.warning(f"No PDFs found in {self.input_dir}. Attempting explicit staging...")
            self.stage_raw_data()
            policy_pdf_paths, case_brief_path = self.discover_documents()

        if not policy_pdf_paths:
            logger.error(f"Critical error: No PDF files discovered under {self.input_dir}")
            return False

        policy_page_records: List[Dict[str, Any]] = []
        manifest_documents: List[Dict[str, Any]] = []
        excluded_documents: List[Dict[str, Any]] = []
        all_warnings: List[str] = []
        all_errors: List[str] = []

        total_discovered_pdfs = len(policy_pdf_paths)
        if case_brief_path and case_brief_path not in policy_pdf_paths:
            total_discovered_pdfs += 1

        # Process Case Brief Exclusion
        if case_brief_path:
            file_hash = compute_file_sha256(case_brief_path)
            excluded_documents.append({
                "source_filename": case_brief_path.name,
                "source_path": str(case_brief_path.relative_to(self.workspace_root) if case_brief_path.is_relative_to(self.workspace_root) else case_brief_path),
                "category": "case_brief",
                "included_in_policy_corpus": False,
                "file_sha256": file_hash,
                "file_size_bytes": case_brief_path.stat().st_size,
                "reason": "Exclusion rule: Marsh Internship Case Brief / Specification document"
            })
            logger.info(f"Categorized non-policy document: {case_brief_path.name} [category: case_brief, included: False]")

        # Process Policy PDF Corpus
        total_policy_pages_processed = 0

        for pdf_path in policy_pdf_paths:
            filename = pdf_path.name
            
            # Check if this PDF is the case brief accidentally placed in input_dir
            if "case study" in filename.lower() or "specification" in filename.lower():
                if not any(e["source_filename"] == filename for e in excluded_documents):
                    file_hash = compute_file_sha256(pdf_path)
                    excluded_documents.append({
                        "source_filename": filename,
                        "source_path": str(pdf_path.relative_to(self.workspace_root) if pdf_path.is_relative_to(self.workspace_root) else pdf_path),
                        "category": "case_brief",
                        "included_in_policy_corpus": False,
                        "file_sha256": file_hash,
                        "file_size_bytes": pdf_path.stat().st_size,
                        "reason": "Exclusion rule: Marsh Internship Case Brief / Specification document"
                    })
                continue

            # Classify Document: Known Policy Brochure vs Unexpected Document
            if filename in KNOWN_POLICY_CATALOG:
                doc_name = KNOWN_POLICY_CATALOG[filename]
                category = "policy_evidence"
                include_in_corpus = True
            else:
                doc_name = f"Unexpected Document ({filename})"
                category = "unexpected"
                include_in_corpus = False
                warning_msg = f"UNEXPECTED_DOCUMENT: {filename} is not in the recognized policy corpus"
                all_warnings.append(warning_msg)
                file_hash = compute_file_sha256(pdf_path)
                excluded_documents.append({
                    "source_filename": filename,
                    "source_path": str(pdf_path.relative_to(self.workspace_root) if pdf_path.is_relative_to(self.workspace_root) else pdf_path),
                    "category": category,
                    "included_in_policy_corpus": False,
                    "file_sha256": file_hash,
                    "file_size_bytes": pdf_path.stat().st_size,
                    "reason": "Unrecognized PDF: Not in known policy evidence catalog"
                })
                logger.warning(warning_msg)
                continue

            file_hash = compute_file_sha256(pdf_path)
            slug = slugify_filename(filename)
            doc_id = f"doc_{slug}_{file_hash[:12]}"

            doc_warnings: List[str] = []

            try:
                fitz_doc = pymupdf.open(pdf_path)
                page_count = len(fitz_doc)
            except Exception as e:
                err_msg = f"CRITICAL_ERROR: Failed to open PDF {filename}: {str(e)}"
                logger.error(err_msg)
                all_errors.append(err_msg)
                manifest_documents.append({
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "source_filename": filename,
                    "source_path": str(pdf_path.relative_to(self.workspace_root) if pdf_path.is_relative_to(self.workspace_root) else pdf_path),
                    "category": category,
                    "included_in_policy_corpus": include_in_corpus,
                    "page_count_expected": 0,
                    "page_count_processed": 0,
                    "pages_missing": [],
                    "processing_status": "failed",
                    "file_size_bytes": pdf_path.stat().st_size,
                    "file_sha256": file_hash,
                    "warnings": [err_msg]
                })
                continue

            processed_pages_count = 0
            missing_pages: List[int] = []

            for page_idx in range(page_count):
                page_num = page_idx + 1  # 1-based page numbering
                page = fitz_doc[page_idx]
                
                try:
                    raw_text = page.get_text("text")
                    clean_text = normalize_text_conservatively(raw_text)
                except Exception as pe:
                    page_err = f"Page {page_num} extraction failed in {filename}: {str(pe)}"
                    logger.error(page_err)
                    all_errors.append(page_err)
                    missing_pages.append(page_num)
                    continue

                processed_pages_count += 1
                total_policy_pages_processed += 1

                char_count = len(clean_text)
                word_count = len(clean_text.split()) if clean_text else 0
                text_hash = compute_text_sha256(clean_text)

                page_warnings: List[str] = []
                # Low-text heuristic warning check (< 100 characters)
                if char_count < 100:
                    warn = f"LOW_TEXT_GRAPHIC_COVER: Page {page_num} in {filename} contains only {char_count} characters"
                    page_warnings.append(warn)
                    doc_warnings.append(warn)
                    all_warnings.append(warn)

                page_record = {
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "source_filename": filename,
                    "source_path": str(pdf_path.relative_to(self.workspace_root) if pdf_path.is_relative_to(self.workspace_root) else pdf_path),
                    "page_number": page_num,
                    "page_count": page_count,
                    "raw_text": raw_text,
                    "clean_text": clean_text,
                    "character_count": char_count,
                    "word_count": word_count,
                    "text_hash": text_hash,
                    "extraction_method": "pymupdf",
                    "warnings": page_warnings
                }

                policy_page_records.append(page_record)

            fitz_doc.close()

            manifest_documents.append({
                "document_id": doc_id,
                "document_name": doc_name,
                "source_filename": filename,
                "source_path": str(pdf_path.relative_to(self.workspace_root) if pdf_path.is_relative_to(self.workspace_root) else pdf_path),
                "category": category,
                "included_in_policy_corpus": include_in_corpus,
                "page_count_expected": page_count,
                "page_count_processed": processed_pages_count,
                "pages_missing": missing_pages,
                "processing_status": "success" if processed_pages_count == page_count else "partial_failure",
                "file_size_bytes": pdf_path.stat().st_size,
                "file_sha256": file_hash,
                "warnings": doc_warnings
            })

            logger.info(f"Processed policy document: {filename} [{processed_pages_count}/{page_count} pages extracted]")

        # Critical Insurance Terms Validation Pass
        combined_corpus_text = " ".join([p["clean_text"] for p in policy_page_records])
        critical_term_results: Dict[str, bool] = {}
        all_critical_terms_present = True

        for label, pattern in CRITICAL_INSURANCE_TERMS:
            found = bool(re.search(pattern, combined_corpus_text, re.IGNORECASE))
            critical_term_results[label] = found
            if not found:
                all_critical_terms_present = False
                all_warnings.append(f"CRITICAL_TERM_MISSING: Could not find match for pattern '{pattern}' ({label})")

        # Duplicate Page Detection Pass
        page_signatures = [f"{p['document_id']}_P{p['page_number']}" for p in policy_page_records]
        total_duplicate_pages = len(page_signatures) - len(set(page_signatures))

        # Empty Page Count Pass
        total_empty_pages = sum(1 for p in policy_page_records if p["character_count"] == 0)

        # Low-Text Page Count Pass
        total_low_text_pages = sum(1 for p in policy_page_records if p["character_count"] < 100)

        # Build Validation Report
        overall_status = "PASSED" if (len(all_errors) == 0 and all_critical_terms_present and total_policy_pages_processed == 24) else "FAILED"

        validation_report = {
            "overall_status": overall_status,
            "total_pdfs_discovered": total_discovered_pdfs,
            "total_policy_documents_processed": len(manifest_documents),
            "total_excluded_documents": len(excluded_documents),
            "total_policy_pages_processed": total_policy_pages_processed,
            "total_missing_pages": sum(len(d["pages_missing"]) for d in manifest_documents),
            "total_duplicate_pages": total_duplicate_pages,
            "total_empty_pages": total_empty_pages,
            "total_suspicious_low_text_pages": total_low_text_pages,
            "critical_term_validation": {
                "status": "PASSED" if all_critical_terms_present else "WARNING",
                "all_terms_detected": all_critical_terms_present,
                "term_details": critical_term_results
            },
            "warnings": all_warnings,
            "errors": all_errors
        }

        manifest = {
            "documents": manifest_documents,
            "excluded_documents": excluded_documents
        }

        # Save JSON Outputs Deterministically
        policy_pages_path = self.output_dir / "policy_pages.json"
        manifest_path = self.output_dir / "document_manifest.json"
        report_path = self.output_dir / "extraction_validation_report.json"

        with open(policy_pages_path, "w", encoding="utf-8") as f:
            json.dump(policy_page_records, f, indent=2, ensure_ascii=False)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(validation_report, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved policy_pages.json -> {policy_pages_path} ({len(policy_page_records)} pages)")
        logger.info(f"Saved document_manifest.json -> {manifest_path} ({len(manifest_documents)} policy docs, {len(excluded_documents)} excluded)")
        logger.info(f"Saved extraction_validation_report.json -> {report_path} [Overall Status: {overall_status}]")

        return overall_status == "PASSED"


def main():
    parser = argparse.ArgumentParser(description="Marsh Insurance Policy PDF Ingestion & Validation CLI (Phase 1)")
    parser.add_argument("--input-dir", type=Path_type, default=pathlib.Path("data/raw"), help="Path to raw input directory")
    parser.add_argument("--output-dir", type=Path_type, default=pathlib.Path("data/processed"), help="Path to output processed JSON directory")
    parser.add_argument("--force", action="store_true", help="Force re-processing of inputs")
    parser.add_argument("--stage-raw", action="store_true", help="Explicitly stage raw policy brochures into data/raw before processing")

    args = parser.parse_args()

    processor = DocumentProcessor(input_dir=args.input_dir, output_dir=args.output_dir, force=args.force)
    
    if args.stage_raw:
        processor.stage_raw_data()

    success = processor.process()
    sys.exit(0 if success else 1)


def Path_type(path_str: str) -> pathlib.Path:
    return pathlib.Path(path_str)


if __name__ == "__main__":
    main()
