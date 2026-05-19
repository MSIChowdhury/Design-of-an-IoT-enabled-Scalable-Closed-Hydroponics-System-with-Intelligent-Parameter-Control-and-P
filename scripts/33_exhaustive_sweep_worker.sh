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
SPLIT="${SPLIT:-validation}"
SETTING_SHARDS="${SETTING_SHARDS:-512}"
TRIAL_SHARDS="${TRIAL_SHARDS:-16}"
LOG_DIR="results/run_logs"
mkdir -p "$LOG_DIR" results/metrics/exhaustive

echo "$(date -Is) sweep worker ${WORKER_INDEX}/${WORKER_COUNT} start profile=${PROFILE} split=${SPLIT}"

task_index=0
for trial_shard in $(seq 0 "$((TRIAL_SHARDS - 1))"); do
  for setting_shard in $(seq 0 "$((SETTING_SHARDS - 1))"); do
    if [[ "$((task_index % WORKER_COUNT))" -eq "$WORKER_INDEX" ]]; then
      log_file="$LOG_DIR/exhaustive_sweep_${SPLIT}_s$(printf '%04d' "$setting_shard")-of-$(printf '%04d' "$SETTING_SHARDS")_t$(printf '%02d' "$trial_shard")-of-$(printf '%02d' "$TRIAL_SHARDS").log"
      echo "$(date -Is) worker=${WORKER_INDEX} start setting_shard=${setting_shard}/${SETTING_SHARDS} trial_shard=${trial_shard}/${TRIAL_SHARDS}"
      {
        echo "$(date -Is) start setting_shard=${setting_shard}/${SETTING_SHARDS} trial_shard=${trial_shard}/${TRIAL_SHARDS} worker=${WORKER_INDEX}/${WORKER_COUNT}"
        docker compose run --rm project-shell python scripts/28_sweep_aasvr_exhaustive.py \
          --profile "$PROFILE" \
          --split "$SPLIT" \
          --setting-shard-index "$setting_shard" \
          --setting-shard-count "$SETTING_SHARDS" \
          --trial-shard-index "$trial_shard" \
          --trial-shard-count "$TRIAL_SHARDS"
        echo "$(date -Is) done setting_shard=${setting_shard}/${SETTING_SHARDS} trial_shard=${trial_shard}/${TRIAL_SHARDS} worker=${WORKER_INDEX}/${WORKER_COUNT}"
      } > "$log_file" 2>&1
      echo "$(date -Is) worker=${WORKER_INDEX} done setting_shard=${setting_shard}/${SETTING_SHARDS} trial_shard=${trial_shard}/${TRIAL_SHARDS}"
    fi
    task_index="$((task_index + 1))"
  done
done

echo "$(date -Is) sweep worker ${WORKER_INDEX}/${WORKER_COUNT} complete"
