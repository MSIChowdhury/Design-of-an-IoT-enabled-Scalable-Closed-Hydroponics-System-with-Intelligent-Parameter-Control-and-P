from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    print("Manuscript checks passed.")


if __name__ == "__main__":
    main()

