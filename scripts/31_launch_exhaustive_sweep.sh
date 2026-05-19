#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="results/run_logs"
mkdir -p "$LOG_DIR" results/metrics/exhaustive

PROFILE="${PROFILE:-exhaustive}"
SPLIT="${SPLIT:-validation}"
SETTING_SHARDS="${SETTING_SHARDS:-512}"
TRIAL_SHARDS="${TRIAL_SHARDS:-16}"
PARALLEL="${PARALLEL:-4}"

echo "$(date -Is) starting exhaustive sweep profile=${PROFILE} split=${SPLIT} setting_shards=${SETTING_SHARDS} trial_shards=${TRIAL_SHARDS} parallel=${PARALLEL}"

run_one() {
  local setting_shard="$1"
  local trial_shard="$2"
  local log_file="$LOG_DIR/exhaustive_sweep_${SPLIT}_s$(printf '%04d' "$setting_shard")-of-$(printf '%04d' "$SETTING_SHARDS")_t$(printf '%02d' "$trial_shard")-of-$(printf '%02d' "$TRIAL_SHARDS").log"
  {
    echo "$(date -Is) start setting_shard=${setting_shard}/${SETTING_SHARDS} trial_shard=${trial_shard}/${TRIAL_SHARDS}"
    docker compose run --rm project-shell python scripts/28_sweep_aasvr_exhaustive.py \
      --profile "$PROFILE" \
      --split "$SPLIT" \
      --setting-shard-index "$setting_shard" \
      --setting-shard-count "$SETTING_SHARDS" \
      --trial-shard-index "$trial_shard" \
      --trial-shard-count "$TRIAL_SHARDS"
    echo "$(date -Is) done setting_shard=${setting_shard}/${SETTING_SHARDS} trial_shard=${trial_shard}/${TRIAL_SHARDS}"
  } > "$log_file" 2>&1
}

if [[ "${1:-}" == "--one" ]]; then
  run_one "$2" "$3"
  exit 0
fi

for trial_shard in $(seq 0 "$((TRIAL_SHARDS - 1))"); do
  echo "$(date -Is) launching trial_shard=${trial_shard}/${TRIAL_SHARDS}"
  seq 0 "$((SETTING_SHARDS - 1))" | xargs -I{} -P "$PARALLEL" bash scripts/31_launch_exhaustive_sweep.sh --one {} "$trial_shard"
  echo "$(date -Is) completed trial_shard=${trial_shard}/${TRIAL_SHARDS}"
done

echo "$(date -Is) exhaustive sweep complete"
