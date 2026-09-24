#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
receiver="delivery-challenge-receiver-$$"
cleanup() { docker rm -f "$receiver" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Keep computation attached; only the explicitly managed UDP server is detached.
docker compose run --rm -T project-shell python scripts/45_delivery_challenge.py
docker compose run -d --name "$receiver" project-shell python scripts/46_delivery_network_probe.py --server >/dev/null
# Client connection retries cover receiver startup; do not retry completed experiments.
docker compose run --rm -T project-shell python scripts/46_delivery_network_probe.py --host "$receiver"
docker compose run --rm -T project-shell python scripts/47_report_delivery_challenge.py
