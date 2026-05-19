#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "$#" -ne 2 ]]; then
  echo "Usage: $0 WORKER_INDEX WORKER_COUNT" >&2
  exit 2
fi

WORKER_INDEX="$1"
WORKER_COUNT="$2"
PROFILE="${PROFILE:-exhaustive}"
SHARDS="${SHARDS:-128}"
SPLITS="${SPLITS:-tune validation test}"
METHODS="${METHODS:-aasvr_r,aasvr_no_response,no_cusum,lockout_only,cusum_only,raw_threshold,moving_average,moving_median,hampel,kalman,ewma,cusum,glr,recursive_pca,isolation_forest,one_class_svm,local_outlier_factor}"
LOG_DIR="results/run_logs"
mkdir -p "$LOG_DIR" results/metrics/exhaustive

echo "$(date -Is) benchmark worker ${WORKER_INDEX}/${WORKER_COUNT} start profile=${PROFILE}"

for split in $SPLITS; do
  for shard in $(seq "$WORKER_INDEX" "$WORKER_COUNT" "$((SHARDS - 1))"); do
    log_file="$LOG_DIR/exhaustive_${split}_shard$(printf '%04d' "$shard")-of-$(printf '%04d' "$SHARDS").log"
    echo "$(date -Is) worker=${WORKER_INDEX} start split=${split} shard=${shard}/${SHARDS}"
    {
      echo "$(date -Is) start split=${split} shard=${shard}/${SHARDS} worker=${WORKER_INDEX}/${WORKER_COUNT}"
      docker compose run --rm project-shell python scripts/27_run_exhaustive_benchmark.py \
        --profile "$PROFILE" \
        --split "$split" \
        --shard-index "$shard" \
        --shard-count "$SHARDS" \
        --methods "$METHODS"
      echo "$(date -Is) done split=${split} shard=${shard}/${SHARDS} worker=${WORKER_INDEX}/${WORKER_COUNT}"
    } > "$log_file" 2>&1
    echo "$(date -Is) worker=${WORKER_INDEX} done split=${split} shard=${shard}/${SHARDS}"
  done
done

echo "$(date -Is) benchmark worker ${WORKER_INDEX}/${WORKER_COUNT} complete"
