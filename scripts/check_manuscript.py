from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TEXT = (
    "Nuclear Physics B",
    "submitted to Nuclear",
    "P1 P2 P3",
    "P1 P3 P3",
)
TEXT_CHECK_PATHS = (
    ROOT / "Paper Files/main_aasvr.tex",
    ROOT / "Paper Files/main_aasvr_blinded.tex",
    ROOT / "Paper Files/elsarticle-template-num.tex",
    ROOT / "Paper Files/MANIFEST.md",
    ROOT / "Paper Files/EDITOR_NOTES.md",
    ROOT / "manuscript/data_availability.md",
    ROOT / "manuscript/submission_checklist.md",
    ROOT / "manuscript/title_page.tex",
)
PDF_CHECK_PATHS = (
    ROOT / "Paper Files/main_aasvr.pdf",
    ROOT / "Paper Files/main_aasvr_blinded.pdf",
    ROOT / "Paper Files/elsarticle-template-num.pdf",
)


def main() -> None:
    abstract = ROOT / "manuscript/abstract.txt"
    highlights = ROOT / "manuscript/highlights.txt"
    if abstract.exists():
        words = abstract.read_text(encoding="utf-8").split()
        if len(words) > 125:
            raise SystemExit(f"Abstract has {len(words)} words; ISA limit is 125.")
    if highlights.exists():
        lines = [line.strip("- ").strip() for line in highlights.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not 3 <= len(lines) <= 5:
            raise SystemExit("Highlights must contain 3 to 5 bullets.")
        too_long = [line for line in lines if len(line) > 85]
        if too_long:
            raise SystemExit(f"Highlight exceeds 85 characters: {too_long[0]}")
    _check_forbidden_text()
    print("Manuscript checks passed.")


def _check_forbidden_text() -> None:
    for path in TEXT_CHECK_PATHS:
        if path.exists():
            _scan_text(path, path.read_text(encoding="utf-8", errors="replace"))

    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return
    for path in PDF_CHECK_PATHS:
        if not path.exists():
            continue
        completed = subprocess.run(
            [pdftotext, str(path), "-"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _scan_text(path, completed.stdout)
        if path.name in {"main_aasvr.pdf", "main_aasvr_blinded.pdf"} and "Preprint submitted to ISA Transactions" not in completed.stdout:
            raise SystemExit(f"{path} is missing the ISA Transactions preprint footer.")


def _scan_text(path: Path, text: str) -> None:
    for needle in FORBIDDEN_TEXT:
        if needle in text:
            raise SystemExit(f"Forbidden submission text found in {path}: {needle}")


if __name__ == "__main__":
    main()
