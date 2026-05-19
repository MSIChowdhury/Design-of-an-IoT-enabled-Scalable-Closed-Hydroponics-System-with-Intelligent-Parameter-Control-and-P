#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE="${PROFILE:-exhaustive}"
WORKER_COUNT="${WORKER_COUNT:-8}"
LOG_DIR="results/run_logs"
PID_DIR="$LOG_DIR/exhaustive_benchmark_workers"
mkdir -p "$LOG_DIR"

echo "$(date -Is) benchmark monitor waiting for ${WORKER_COUNT} workers"
while true; do
  alive=0
  for worker in $(seq 0 "$((WORKER_COUNT - 1))"); do
    pid_file="$PID_DIR/worker_${worker}.pid"
    if [[ -s "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
      alive="$((alive + 1))"
    fi
  done
  echo "$(date -Is) benchmark monitor alive_workers=${alive}/${WORKER_COUNT}"
  if [[ "$alive" -eq 0 ]]; then
    break
  fi
  sleep 300
done

for split in tune validation test; do
  echo "$(date -Is) aggregating split=${split}"
  docker compose run --rm project-shell python scripts/29_aggregate_exhaustive_results.py \
    --profile "$PROFILE" \
    --split "$split" \
    --bootstrap 1000 \
    > "$LOG_DIR/exhaustive_${split}_aggregate.log" 2>&1
  echo "$(date -Is) aggregated split=${split}"
done

echo "$(date -Is) benchmark monitor complete"
