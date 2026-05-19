from __future__ import annotations

import argparse
from pathlib import Path

from aasvr.agronomics import (
    AGRONOMIC_RAW,
    AGRONOMIC_TEMPLATE,
    prepare_agronomic_harvest,
    write_agronomic_template,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default=str(ROOT / AGRONOMIC_RAW), help="Per-plant agronomic harvest CSV.")
    parser.add_argument(
        "--write-template",
        action="store_true",
        help="Write the required harvest-sheet template and exit.",
    )
    args = parser.parse_args()
    if args.write_template:
        template = write_agronomic_template(ROOT / AGRONOMIC_TEMPLATE)
        print(f"Wrote {template}")
        return
    outputs = prepare_agronomic_harvest(args.raw)
    print(f"Wrote {outputs.processed_path}")
    print(f"Wrote {outputs.quality_path}")


if __name__ == "__main__":
    main()
