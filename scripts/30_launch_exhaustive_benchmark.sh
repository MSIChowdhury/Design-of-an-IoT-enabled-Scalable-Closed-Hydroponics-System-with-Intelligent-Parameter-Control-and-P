#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="results/run_logs"
mkdir -p "$LOG_DIR" results/metrics/exhaustive

METHODS="${METHODS:-aasvr_r,aasvr_no_response,no_cusum,lockout_only,cusum_only,raw_threshold,moving_average,moving_median,hampel,kalman,ewma,cusum,glr,recursive_pca,isolation_forest,one_class_svm,local_outlier_factor}"
SHARDS="${SHARDS:-128}"
PARALLEL="${PARALLEL:-8}"
PROFILE="${PROFILE:-exhaustive}"
SPLITS="${SPLITS:-tune validation test}"

echo "$(date -Is) starting exhaustive benchmark profile=${PROFILE} shards=${SHARDS} parallel=${PARALLEL}"

run_one() {
  local split="$1"
  local shard="$2"
  local log_file="$LOG_DIR/exhaustive_${split}_shard$(printf '%04d' "$shard")-of-$(printf '%04d' "$SHARDS").log"
  {
    echo "$(date -Is) start split=${split} shard=${shard}/${SHARDS}"
    docker compose run --rm project-shell python scripts/27_run_exhaustive_benchmark.py \
      --profile "$PROFILE" \
      --split "$split" \
      --shard-index "$shard" \
      --shard-count "$SHARDS" \
      --methods "$METHODS"
    echo "$(date -Is) done split=${split} shard=${shard}/${SHARDS}"
  } > "$log_file" 2>&1
}

if [[ "${1:-}" == "--one" ]]; then
  run_one "$2" "$3"
  exit 0
fi

for split in $SPLITS; do
  echo "$(date -Is) launching split=${split}"
  seq 0 "$((SHARDS - 1))" | xargs -I{} -P "$PARALLEL" bash scripts/30_launch_exhaustive_benchmark.sh --one "$split" {}
  echo "$(date -Is) aggregating split=${split}"
  docker compose run --rm project-shell python scripts/29_aggregate_exhaustive_results.py \
    --profile "$PROFILE" \
    --split "$split" \
    --bootstrap 1000 \
    > "$LOG_DIR/exhaustive_${split}_aggregate.log" 2>&1
  echo "$(date -Is) completed split=${split}"
done

echo "$(date -Is) exhaustive benchmark complete"
