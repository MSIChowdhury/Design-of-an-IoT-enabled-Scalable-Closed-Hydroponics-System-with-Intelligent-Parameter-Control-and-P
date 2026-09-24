#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
mock_name="hydro-execution-mock-$run_id"
receiver_name="hydro-execution-receiver-$run_id"
output="results/metrics/instrumented_execution"
runtime="$output/runtime/$run_id"
mkdir -p "$runtime"
cleanup() { docker rm -f "$receiver_name" "$mock_name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
(timedatectl show -p NTPSynchronized -p NTP || true) > "$output/host_ntp_status.txt" 2>&1
docker compose run --rm project-shell python scripts/55_instrumented_execution.py --prepare
docker compose run -d --name "$mock_name" project-shell python scripts/54_instrumented_endpoints.py --role mock --root "$runtime/mock"
docker compose run -d --name "$receiver_name" project-shell python scripts/54_instrumented_endpoints.py --role supervisor --root "$runtime/receiver" --mock-host "$mock_name"
if ! docker compose run --rm project-shell python scripts/55_instrumented_execution.py --receiver "$receiver_name" --mock "$mock_name"; then
    docker logs "$receiver_name"
    docker logs "$mock_name"
    exit 1
fi
docker compose run --rm project-shell python scripts/56_replay_execution_traces.py
docker compose run --rm project-shell python scripts/57_report_instrumented_execution.py
