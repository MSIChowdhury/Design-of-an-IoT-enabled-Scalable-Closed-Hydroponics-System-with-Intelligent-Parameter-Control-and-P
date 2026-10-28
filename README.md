# Hydroponic Sensor Fault-to-Actuation Audit

## Overview

This repository supports a retrospective **fault-to-actuation audit** of a low-cost closed nutrient film technique (NFT) hydroponic system. The current Biosystems Engineering manuscript studies how flagged sensor readings become executable controller commands, compares practical safeguards, and reports the locked LiveGate comparison, including its negative overall result.

The current manuscript is [the audit paper](Paper%20Files/main_audit.pdf), with
[editable source](Paper%20Files/main_audit.tex) and a
[blinded PDF](Paper%20Files/main_audit_blinded.pdf). The AASVR-R manuscript
(`main_aasvr.tex`) and the original root PDF are historical artifacts and should
not be submitted as the current paper.

## Authors

- MD. Sameer Iqbal Chowdhury - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh
- Mikdam-Al-Maad Ronoue - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh

## Supervisors

- Dr. Lafifa Jamal - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh
- Dr. Md Asaduzzaman - Department of Agriculture and Food Technology, Kyoto University of Advanced Sciences

## Current Research Focus

1. A fault inventory and executable-command replay of the 30-day experiment-2 sensor log.
2. Explicit separation of impossible values, heuristic spike flags, full-scale readings, and poor temperature regulation.
3. A frozen retrospective LiveGate comparison, with shared downstream control and validation-selected operating points.
4. A separately labelled follow-up with simple run-length and physical-bound rejection baselines, paired day-cluster intervals, and sensor-wise results.
5. Public measured sensor and harvest data, reproducible Docker workflows, and a synthetic stand-in used only for smoke tests.

Historical AASVR and external benchmark workflows remain available below. The
`hydro_exp1` identifiers and `--hydro-exp1` options are retained for compatibility:
the file `Hydroponics Data First Trial.csv` actually contains **experiment 2**
(27 February--28 March 2024), not the first growing season.

## Reproducible Workflow

Run the current audit and follow-up through Docker (the user flag keeps generated
files editable by the workspace owner):

```bash
docker compose run --rm --user "$(id -u):$(id -g)" project-shell python scripts/02_prepare_datasets.py --hydro-exp1
docker compose run --rm --user "$(id -u):$(id -g)" project-shell make audit-results
docker compose run --rm --user "$(id -u):$(id -g)" project-shell make livegate-followup
docker compose run --rm --user "$(id -u):$(id -g)" project-shell make test manuscript-check
make paper-docker
```

`make paper-docker` is a host launcher for the pinned TeX container; it builds
both current PDFs. `make paper` can instead be run inside a TeX-capable container.
After building, run `make manuscript-pdf-check` in a container with Python and
Poppler (`pdftotext`); this strict check requires both PDFs. Source checks report
explicitly when PDF inspection was skipped. `make paper-legacy` builds the
superseded AASVR package only.

The original [LiveGate protocol](docs/livegate/PROTOCOL.md) and
[locked results](docs/livegate/RESULTS.md) remain separate from the
[follow-up protocol](docs/livegate/FOLLOWUP_PROTOCOL.md) and
[follow-up results](docs/livegate/FOLLOWUP_RESULTS.md). No replay establishes
actual actuator execution, avoided physical damage, or a causal crop benefit.

To run the broader historical pipeline:

```bash
docker compose run --rm project-shell make real
```

Prepare absence-safe templates and status tables for the remaining deployment
evidence limitations:

```bash
docker compose run --rm project-shell make optional-evidence
docker compose run --rm project-shell make water-calibration
docker compose run --rm project-shell make revision-artifacts JOBS=8
```

These commands define the future actuator-state log, independent reference
measurement, and water-level calibration schemas. If the optional local CSV files
are absent, they write explicit status outputs and leave the current benchmark
unchanged.
The revision-artifacts target also writes the historical manuscript's evidence-status
table and AASVR-R replay operating-tradeoff table/figure. Actuator conclusions
remain replay-only unless an independent command/state export is supplied through
the optional evidence schema.

If controller, relay, dashboard, or ThingSpeak exports contain real actuator
command/state records, normalize them before running optional-evidence:

```bash
docker compose run --rm project-shell make reconstruct-actuator-log SOURCE=/path/to/controller_export.csv
docker compose run --rm project-shell make optional-evidence
```

The reconstruction utility requires timestamp, actuator identity, commanded
state, measured or relay-observed state, target sensor, and expected process
direction. It is intentionally not a threshold-crossing detector; commands
should not be inferred from the hydroponic sensor values being evaluated.

Generate the external benchmark acquisition notes and subset protocol without downloading large archives:

```bash
docker compose run --rm project-shell make subset-protocol
```

The locally available hydroponic feed is expected at:

```text
data/raw/hydroponic/Hydroponics Data First Trial.csv
```

Optional local evidence files can be added next to the feed as
`actuator_state_log.csv`, `reference_measurements.csv`, and
`water_level_calibration.csv`.

The measured hydroponic log and author-approved harvest sheets are tracked and
public in this repository. Large generated outputs and raw third-party benchmark
files remain ignored; place external files under their configured
`data/raw/<dataset>/` directories. The [synthetic stand-in](data/standin/README.md)
is for code-level smoke tests only and is never used for reported results.

Run the exhaustive hydroponic stress-test protocol in shards. The `mini` profile
is a smoke test; the `exhaustive` profile defines the historical full factorial
stress-test protocol, which is not the current audit paper's evidence base:

```bash
docker compose run --rm project-shell make exhaustive-mini
docker compose run --rm project-shell make exhaustive-grid
docker compose run --rm project-shell python scripts/27_run_exhaustive_benchmark.py \
  --profile exhaustive --split test --shard-index 0 --shard-count 32
docker compose run --rm project-shell python scripts/29_aggregate_exhaustive_results.py \
  --profile exhaustive --split test
docker compose run --rm project-shell make exhaustive-full-attached EXHAUSTIVE_SHARDS=4096 EXHAUSTIVE_PARALLEL=8
```

The exhaustive profile spans the six primary hydroponic sensors, fourteen fault
classes, four magnitude levels, eight durations, and 50 disjoint insertion
windows per cell for each tune/validation/test split. It produces 403,200
trial descriptors before method expansion and is intentionally shardable so it
can run on a workstation or cluster without changing the protocol.

Large public archives are not downloaded by default. The historical external-benchmark workflow uses the `paper` profile, which documents fixed subset rules for cross-domain validation. These external results are not part of the current audit paper. SKAB is compact enough to clone directly; MetroPT-3 is manageable but still downloaded only when requested. Full TEP/WUR archive download remains an explicit opt-in through `scripts/download_datasets.py --profile full --download`.

## Historical AASVR and External Benchmarks

The superseded AASVR-R manuscript used the synthetic-fault benchmark of the same
experiment-2 log, under historical `hydro_exp1` filenames. Its results remain in
`results/tables/` and `Paper Files/main_aasvr.tex` for reproducibility. Current
audit inputs are `results/tables/deployment_audit.csv`, the locked
`results/metrics/livegate/` outputs, and the separate
`results/metrics/livegate_followup/` outputs.

These results are synthetic-fault benchmark results, not agronomic causality
claims. Crop-yield and dashboard material are retained only as deployment context.
The optional agronomic linkage pipeline uses the per-plant harvest sheet at
`data/raw/hydroponic/Agronomic Data.csv`; for a normalized replacement, generate the template with
`python scripts/22_prepare_agronomic.py --write-template` or copy
`configs/templates/agronomic_harvest_template.csv`.

The current public external benchmark path also supports the HAI `21.03/test1` paper subset. Native HAI attack labels are timestamp-level, so the headline HAI table uses a timestamp-level multivariate score: a timestamp is flagged when at least 30% of sensor streams reject/alert. In the latest local run, AASVR had the highest HAI balanced accuracy among implemented methods, but the result should be framed as cross-domain stress testing rather than a dominance claim.

The SKAB public process-loop benchmark is now supported as the primary easy-access external dataset. Native SKAB labels are also timestamp-level, so the same 30% multivariate aggregation rule is used for the headline comparison. In the latest local run, AASVR had the highest SKAB balanced accuracy among implemented methods, with high recall and a high false-positive rate that should be discussed as a sensitivity/specificity tradeoff.

For native timestamp-label datasets, the pipeline also reports an aggregation-threshold sensitivity analysis. The fixed 30% rule remains the headline protocol, while the sensitivity table shows how recall, specificity, false-positive rate, and balanced accuracy change when the required fraction of rejecting/alerting sensor streams is varied.

## Acknowledgements

We gratefully acknowledge the financial support provided
by the ICT Division under the Ministry of Communications
and Information Technology, People's Republic of Bangladesh. This research was fully funded
under the ICT Innovation Fund arranged by the ICT Division.

### Retrospective authorization reanalysis

A separate compact benchmark uses temporally disjoint source windows, a fixed
surrogate-reference controller, event matching, elapsed-time lockouts, explicit
estimate age, validation-selected coverage targets, and source-day clustered
uncertainty. It includes all six primary channels and audits legacy AASVR-R
recovery without replacing the historical manuscript tables.

```bash
docker compose run --rm -T project-shell make replay-reanalysis
```

See [the protocol](docs/reanalysis/PROTOCOL.md) for metric definitions, controls,
selection rules, limitations, and output paths.

### Decision-preserving telemetry feasibility

The separate telemetry study compares full, periodic, send-on-change,
threshold-plus-heartbeat, edge-command-event, and controller-state-snapshot
reporting. It uses complete chronological validation/evaluation blocks, causal
16-second controller ticks, simulated network impairments, common freshness and
cooldown contracts, locked selection constraints, and a measured two-process
UDP loopback probe.

```bash
docker compose run --rm -T project-shell make telemetry-feasibility
```

See [protocol](docs/telemetry/PROTOCOL.md) and [results](docs/telemetry/RESULTS.md).
Communication fidelity does not imply measured plant-control improvement.

### Reliable command-event delivery

The follow-up adds bounded retries, original command expiry, cancellation revisions,
idempotent output, and impaired receipt ACKs. It compares variants without ACKs
or cancellation using the original coverage/error requirements and counts traffic
in both directions. Existing telemetry results are preserved.

```bash
docker compose run --rm -T project-shell make reliable-events
```

See [protocol](docs/reliable_events/PROTOCOL.md) and
[results](docs/reliable_events/RESULTS.md). This is retrospective computational
fidelity evidence, not a measured actuator-response or physical safety claim.

### Frozen command-delivery challenge

Run the fixed candidate against same-receiver plain repetition and an acknowledged
variant, using new network seeds, outage phases, correlated loss, clock offsets,
and restart challenges. The launcher also executes historical windows through
real UDP sockets in two separate Docker containers with a delay/loss relay:

```bash
scripts/48_run_delivery_challenge.sh
```

Settings are frozen before execution; the existing sensor periods remain
retrospectively reused. See the [protocol](docs/delivery_challenge/PROTOCOL.md)
and [generated results](docs/delivery_challenge/RESULTS.md). Outputs are written
to `results/metrics/delivery_challenge/` and `results/figures/delivery_challenge/`.
The launcher removes its own receiver container when finished.
Read the [assessment](docs/delivery_challenge/ASSESSMENT.md) for the publication
implications, including restart/clock failures that coverage metrics alone miss.

### Durable recovery-contract version

Run a separate recovery-aware receiver with durable output reservations,
clock-uncertainty checks, fresh-evidence recovery, and explicit blocking of
unknown execution outcomes:

```bash
docker compose run --rm -T project-shell make recovery-contract
```

This runs a three-policy historical comparison on new fault schedules, actual
SIGKILL/reopen tests against disk-backed SQLite journals, and a generated report.
See the [contract and assumptions](docs/recovery_contract/PROTOCOL.md) and
[results](docs/recovery_contract/RESULTS.md). Structural correctness is reported
separately from lost availability and additional heartbeat traffic. No physical
exactly-once guarantee or automatic reset of uncertain execution is claimed.
The [assessment](docs/recovery_contract/ASSESSMENT.md) explains the substantial
availability/traffic costs and the failure outside the declared clock bound.

### Timing feasibility and component isolation

Run the fixed-clock component ablations and deadline-aware output scheduling
study, including per-command admissible intervals and missed-command explanations:

```bash
docker compose run --rm -T project-shell make timing-feasibility
```

The study preserves 16-second sensing and packet intake, varies assumed clock
bounds explicitly, and selects no deployment setting. See the
[protocol](docs/timing_feasibility/PROTOCOL.md) and
[results](docs/timing_feasibility/RESULTS.md). Compressed command ledgers, paired
intervals, selected timelines, and the empirical frontier are generated under
`results/metrics/timing_feasibility/` and `results/figures/timing_feasibility/`.
Clock bounds remain sensitivity assumptions until independently measured.
Read the [assessment](docs/timing_feasibility/ASSESSMENT.md) for the isolated
persistence cost, recovered scheduling opportunities, and remaining infeasibility.

### Instrumented local execution with a mock actuator

Run the local, three-container timing and actual process-crash experiment, then
replay its measured traces through five fixed receiver/scheduling candidates:

```bash
scripts/58_run_instrumented_execution.sh
```

The host launcher executes all collection and analysis inside Docker and removes
its own containers afterward. See the [frozen protocol](docs/instrumented_execution/PROTOCOL.md)
and [results](docs/instrumented_execution/RESULTS.md). Raw timing records, journals,
source-day intervals, and replay command ledgers remain local under
`results/metrics/instrumented_execution/`. Independent mock-output lookup distinguishes
lost acknowledgments from absent recorded effects; unresolved outcomes remain blocked.
Same-host clocks and short repeated traces do not establish independent-device clock
accuracy, worst-case timing, physical actuation, or closed-loop safety.

### Bounded reconciliation after uncertain execution

Use the existing instrumented-execution measurements to compare the blocking
receiver with terminal-evidence recovery, without retuning the controller:

```bash
scripts/62_run_reconciliation.sh
```

Run the instrumented-execution launcher first if its local measurements are absent.
The reconciliation launcher freezes inputs, runs real UDP and process-kill cases
inside Docker, reproduces every prior baseline row, and evaluates available,
delayed, unavailable, mismatched, and contradictory lookup evidence. Read the
[contract](docs/reconciliation/PROTOCOL.md) and [results](docs/reconciliation/RESULTS.md).
The mock supports permanent cancellation tombstones so a delayed old command
cannot execute after cancellation. Not-found or exhausted lookup attempts never
restore authority; confirmed completion preserves cooldown and requires new
measurement evidence. Physical actuators must provide a defensible execution/fencing
interface before this software contract can be claimed for deployed pumps.
