"""Submission checks must inspect the current package and fail visibly."""
from pathlib import Path

import pytest

from scripts.check_manuscript import _check_pdf_text, _scan_source_tree


def test_current_pdf_rejects_wrong_journal_and_unresolved_references():
    path = Path("main_audit.pdf")
    with pytest.raises(SystemExit, match="ISA Transactions"):
        _check_pdf_text(path, "Preprint submitted to ISA Transactions", audit=True)
    with pytest.raises(SystemExit, match="unresolved reference"):
        _check_pdf_text(path, "Preprint submitted to Biosystems Engineering Figure ??", audit=True)


def test_blinded_pdf_rejects_author_or_repository_identifier():
    text = "Preprint submitted to Biosystems Engineering github.com/MSIChowdhury/project"
    with pytest.raises(SystemExit, match="author-identifying"):
        _check_pdf_text(Path("main_audit_blinded.pdf"), text, audit=True)
    _check_pdf_text(Path("main_audit.pdf"), text, audit=True)


def test_generated_fragment_is_checked_and_missing_input_fails(tmp_path):
    main = tmp_path / "main_audit.tex"
    main.write_text(r"\input{results}")
    with pytest.raises(SystemExit, match="Missing manuscript source"):
        _scan_source_tree(main, set(), audit=True)
    (tmp_path / "results.tex").write_text(
        "Measured data are available from the corresponding author\non reasonable request."
    )
    with pytest.raises(SystemExit, match="reasonable request"):
        _scan_source_tree(main, set(), audit=True)
