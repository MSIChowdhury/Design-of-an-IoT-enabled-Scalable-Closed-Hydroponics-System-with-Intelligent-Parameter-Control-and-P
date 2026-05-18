from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATASET_NOTES = {
    "tep": {
        "target": "data/raw/tep",
        "source": "https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936",
        "access": "Public DTU/Figshare page. Download the data package locally; do not commit raw archives.",
        "use": "Repeatable process-fault benchmark with multiple operating modes and repeated simulations.",
    },
    "wur": {
        "target": "data/raw/wur",
        "source": "https://doi.org/10.4121/21960932",
        "access": "Public 4TU/WUR dataset. Full archive is large; download time-series files first.",
        "use": "Domain-adjacent controlled-environment lettuce/greenhouse validation.",
    },
    "hai": {
        "target": "data/raw/hai",
        "source": "https://github.com/icsdataset/hai",
        "access": "Public GitHub dataset. Clone or download locally if optional ICS validation is needed.",
        "use": "Optional industrial-control anomaly benchmark.",
    },
    "swat": {
        "target": "data/raw/swat",
        "source": "https://www.sutd.edu.sg/itrust/itrust-labs/datasets/dataset-characteristics/swat/",
        "access": "Request through iTrust. Do not redistribute raw files.",
        "use": "Closed-loop water-treatment benchmark with sensor/actuator streams and labels.",
    },
    "wadi": {
        "target": "data/raw/wadi",
        "source": "https://www.sutd.edu.sg/itrust/itrust-labs/datasets/dataset-characteristics/wadi/",
        "access": "Request through iTrust. Do not redistribute raw files.",
        "use": "Distributed water-process benchmark with sensor/actuator streams and labels.",
    },
    "damadics": {
        "target": "data/raw/damadics",
        "source": "https://iair.mchtr.pw.edu.pl/Damadics",
        "access": "Use official benchmark files where available; document any mirror provenance.",
        "use": "Industrial actuator-fault benchmark.",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print acquisition plan without writing notes.")
    parser.add_argument("--all-public", action="store_true", help="Prepare notes for TEP, WUR, and HAI.")
    parser.add_argument("--all", action="store_true", help="Prepare notes for every configured external dataset.")
    for name in DATASET_NOTES:
        parser.add_argument(f"--{name}", action="store_true", help=f"Prepare acquisition notes for {name}.")
    args = parser.parse_args()

    selected = []
    if args.all:
        selected = list(DATASET_NOTES)
    elif args.all_public:
        selected = ["tep", "wur", "hai"]
    else:
        selected = [name for name in DATASET_NOTES if getattr(args, name)]
    if not selected:
        selected = list(DATASET_NOTES)

    for name in selected:
        note = DATASET_NOTES[name]
        text = render_note(name, note)
        if args.dry_run:
            print(text)
            continue
        target = ROOT / note["target"]
        target.mkdir(parents=True, exist_ok=True)
        out = target / "DOWNLOAD_NOTES.md"
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")


def render_note(name: str, note: dict[str, str]) -> str:
    return (
        f"# {name} Dataset Acquisition Notes\n\n"
        f"- Source: {note['source']}\n"
        f"- Access: {note['access']}\n"
        f"- Intended use: {note['use']}\n"
        f"- Local target: `{note['target']}`\n\n"
        "Raw files in this directory are intentionally ignored by git. Commit only loaders, "
        "configs, metadata summaries, and reproducible scripts.\n"
    )


if __name__ == "__main__":
    main()

