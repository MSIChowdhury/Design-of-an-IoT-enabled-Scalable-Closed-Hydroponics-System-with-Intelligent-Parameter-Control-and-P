"""Check the current audit submission; the superseded ISA package is opt-in.

Run in Docker. --require-pdfs also requires Poppler and checks both built PDFs.
These checks catch packaging regressions, not scientific validity or layout.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TEXT = ("Nuclear Physics B", "submitted to Nuclear", "P1 P2 P3", "P1 P3 P3")
AUDIT_FORBIDDEN_TEXT = (
    "ISA Transactions",
    "available from the corresponding author on reasonable request",
)
TEXT_CHECK_PATHS = (
    ROOT / "Paper Files/main_audit.tex",
    ROOT / "Paper Files/main_audit_blinded.tex",
    ROOT / "Paper Files/highlights_audit.txt",
)
PDF_CHECK_PATHS = (
    ROOT / "Paper Files/main_audit.pdf",
    ROOT / "Paper Files/main_audit_blinded.pdf",
)
LEGACY_TEXT_PATHS = (
    ROOT / "Paper Files/main_aasvr.tex",
    ROOT / "Paper Files/main_aasvr_blinded.tex",
    ROOT / "Paper Files/elsarticle-template-num.tex",
    ROOT / "Paper Files/MANIFEST.md",
    ROOT / "Paper Files/EDITOR_NOTES.md",
    ROOT / "manuscript/data_availability.md",
    ROOT / "manuscript/submission_checklist.md",
    ROOT / "manuscript/title_page.tex",
)
LEGACY_PDF_PATHS = (
    ROOT / "Paper Files/main_aasvr.pdf",
    ROOT / "Paper Files/main_aasvr_blinded.pdf",
    ROOT / "Paper Files/elsarticle-template-num.pdf",
)


def _scan_text(path: Path, text: str, *, audit: bool = False) -> None:
    needles = FORBIDDEN_TEXT + (AUDIT_FORBIDDEN_TEXT if audit else ())
    normalized = " ".join(text.split())
    for needle in needles:
        if needle in normalized:
            raise SystemExit(f"Forbidden submission text found in {path}: {needle}")


def _check_highlights(path: Path) -> None:
    lines = [line.strip().removeprefix("- ") for line in path.read_text().splitlines()
             if line.strip()]
    if not 3 <= len(lines) <= 5:
        raise SystemExit(f"{path}: highlights must contain 3 to 5 bullets.")
    if any(len(line) > 85 for line in lines):
        raise SystemExit(f"{path}: a highlight exceeds 85 characters.")


def _scan_source_tree(path: Path, seen: set[Path], *, audit: bool) -> None:
    """Include generated result fragments and the architecture diagram in checks."""
    if path in seen:
        return
    if not path.exists():
        raise SystemExit(f"Missing manuscript source: {path}")
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    _scan_text(path, text, audit=audit)
    for include in re.findall(r"\\(?:input|include)\{([^}]+)\}", text):
        if include == "glyphtounicode":  # TeX distribution file, not a local source.
            continue
        child = path.parent / include
        if not child.suffix:
            child = child.with_suffix(".tex")
        _scan_source_tree(child, seen, audit=audit)


def _check_pdf_text(path: Path, text: str, *, audit: bool) -> None:
    _scan_text(path, text, audit=audit)
    journal = "Biosystems Engineering" if audit else "ISA Transactions"
    normalized = " ".join(text.split())
    if f"Preprint submitted to {journal}" not in normalized:
        raise SystemExit(f"{path}: missing {journal} preprint footer.")
    if "??" in text:
        raise SystemExit(f"{path}: unresolved reference or citation in PDF.")
    if audit and "blinded" in path.stem:
        for marker in ("MSIChowdhury", "Sameer Iqbal", "Mikdam-Al-Maad", "Lafifa Jamal"):
            if marker in normalized:
                raise SystemExit(f"{path}: author-identifying text in blinded PDF: {marker}")


def check_package(*, legacy: bool = False, require_pdfs: bool = False) -> None:
    source_paths = LEGACY_TEXT_PATHS if legacy else TEXT_CHECK_PATHS
    pdf_paths = LEGACY_PDF_PATHS if legacy else PDF_CHECK_PATHS
    seen: set[Path] = set()
    for path in source_paths:
        if legacy and not path.exists():
            continue
        _scan_source_tree(path, seen, audit=not legacy)

    highlights = ROOT / ("manuscript/highlights.txt" if legacy else "Paper Files/highlights_audit.txt")
    if highlights.exists():
        _check_highlights(highlights)
    if legacy:
        abstract = ROOT / "manuscript/abstract.txt"
        if abstract.exists() and len(abstract.read_text().split()) > 125:
            raise SystemExit("Historical ISA abstract exceeds the recorded 125-word limit.")
    else:
        main = (ROOT / "Paper Files/main_audit.tex").read_text()
        if r"\journal{Biosystems Engineering}" not in main:
            raise SystemExit("Current manuscript must name Biosystems Engineering.")
        wrapper = (ROOT / "Paper Files/main_audit_blinded.tex").read_text()
        if r"\def\AUDITBLINDED" not in wrapper or not re.search(
                r"\\input\{main_audit(?:\.tex)?\}", wrapper):
            raise SystemExit("Blinded wrapper must enable AUDITBLINDED and include main_audit.")

    pdftotext = shutil.which("pdftotext")
    if require_pdfs and not pdftotext:
        raise SystemExit("PDF checks require Poppler pdftotext in the container.")
    if not pdftotext:
        print("Source checks passed. PDF checks SKIPPED: pdftotext is unavailable.")
        return
    for path in pdf_paths:
        if not path.exists():
            if require_pdfs:
                raise SystemExit(f"Required manuscript PDF is missing: {path}")
            print(f"PDF check SKIPPED: {path.name} is missing.")
            continue
        completed = subprocess.run([pdftotext, str(path), "-"], check=True, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _check_pdf_text(path, completed.stdout, audit=not legacy)
        if require_pdfs and not legacy:
            newest = max(source.stat().st_mtime for source in seen)
            if path.stat().st_mtime < newest:
                raise SystemExit(f"{path}: PDF predates the checked sources; rebuild it.")
    print(f"{'Historical ISA' if legacy else 'Current audit'} manuscript checks passed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", action="store_true", help="Check the historical ISA package.")
    parser.add_argument("--require-pdfs", action="store_true", help="Require both PDFs and Poppler.")
    args = parser.parse_args()
    check_package(legacy=args.legacy, require_pdfs=args.require_pdfs)


if __name__ == "__main__":
    main()
