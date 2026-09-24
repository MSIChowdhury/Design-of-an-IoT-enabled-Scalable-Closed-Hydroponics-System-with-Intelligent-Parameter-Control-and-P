#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose run --rm project-shell python scripts/60_reconciliation_benchmark.py --freeze
docker compose run --rm project-shell python scripts/59_reconciliation_local.py
docker compose run --rm project-shell python scripts/60_reconciliation_benchmark.py
docker compose run --rm project-shell python scripts/61_report_reconciliation.py
