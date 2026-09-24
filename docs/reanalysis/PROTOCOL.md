# Retrospective authorization reanalysis

This protocol implements the scoring/recovery audit and compact comparison before any journal rewrite. It does not replace the historical manuscript results or establish closed-loop control improvements.

Run from the repository root:

```bash
docker compose run --rm -T -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 project-shell python -u scripts/38_replay_reanalysis.py
```

Configuration: `configs/experiments/reanalysis.yaml`. Generated outputs: `results/metrics/reanalysis/` and `results/figures/reanalysis/`. The first run copies historical source, method configurations, table CSVs, and author manuscript/PDF into ignored `results/run_metadata/reanalysis_reference/` with SHA-256 checksums and the pre-change commit. No raw data or large generated output is committed.

## Evidence and populations

The input is the existing processed Experiment 1 measurement file. Historical Arduino median filtering has not been independently verified; injection occurs **after acquisition and existing preparation**, so the experiment does not evaluate the complete acquisition chain. The unmodified stored stream is a **surrogate reference**, not calibrated ground truth. Existing errors can remain in it.

All six primary channels (EC, pH, humidity, air temperature, water temperature, CO2) enter the new comparison. Humidity is included because it has a configured control band and actuator mapping; no monitoring-only role is assumed. Water level remains excluded. This is a computational policy comparison, not evidence that all configured devices operated historically.

The timeline is divided by elapsed duration at 40% and 70%. Development precedes validation, which precedes evaluation. Eight deterministic, nonoverlapping 240-sample source windows are distributed through each block. Windows crossing gaps longer than 120 seconds are ineligible. Every sample of context remains inside its block; the script asserts nonoverlap. LOF is fitted only on up to 2,000 evenly spaced development observations per sensor. Other detectors retain checked-in structural parameters and sweep the declared threshold multipliers on validation.

These periods were already available during earlier development. This is a **retrospective blocked reanalysis**, not a claim of newly untouched test data. The compact parameter search does not prove a baseline is globally optimized. No cross-dataset claim is made.

Each validation/evaluation block contains 8 windows × 6 sensors × 11 scenarios = 528 trials. Trials share backgrounds; they are not independent deployments. The scenarios are clean replay, positive/negative one-sample spikes, positive/negative 30-sample bias and drift, exact stuck values, dropout, and positive/negative persistent legitimate shifts. Fault durations in seconds follow the original timestamps. Magnitudes are in sensor units in the YAML. Legitimate changes alter both the surrogate and input; they are not fault-labeled. They are software ambiguity challenges, not verified historical process events. Stuck faults retain labels even where the frozen and original values coincide. The compact experiment has one magnitude per sensor; it is not an exhaustive stress test.

## Common controller and scoring

The reference controller uses a 32-second persistent control-band violation and 600-second cooldown. A positive action increases a low value; a negative action decreases a high value. The same 600-second cooldown applies to every tested policy. The ten-minute value is physically motivated for pH/EC dosing; its use for other channels is a comparison constraint, not a validated actuator-specific requirement.

An episode is a continuous same-direction out-of-band run; return into band, direction reversal, or a gap longer than 120 seconds ends continuity. Reference opportunities recur at the reference cooldown interval during an episode. Thus a long episode does not count as fully served merely because one action was issued.

Each opportunity can match at most one same-direction authorization after eligibility, within the same episode, before the next reference opportunity, and within 60, 180, or 600 seconds. Each authorization matches at most one opportunity. Early correct-direction authorizations are not credited toward a later opportunity. These deadlines are sensitivity settings, not agronomically established tolerances. Matching is based on the fixed surrogate; a replay action never changes the trajectory.

Scoring starts at sample 60. The last 600 seconds are reserved for follow-up and do not generate scored reference opportunities. Opportunity and episode coverage have explicit common denominators. Trials with no opportunities are counted, but cannot contribute an artificial zero or one to coverage. Mean delay is conditional on matched opportunities and must be read alongside coverage.

An unnecessary action occurs while the surrogate is in-band or has no finite reference direction. A wrong-direction action opposes a nonzero reference direction. Their sum is the reported undesirable-action count. A currently fault-labeled authorization and an authorization whose last accepted evidence was fault-labeled are separate metrics; neither necessarily implies a wrong action. Authorizations are discrete pulses, not held command-state samples. Cooldown and controller state run through warm-up.

State age is elapsed time since the last accepted measurement, not since the last numerical rectification. The report includes age, stale fraction, estimate-error numerators by sensor, sample/event detection, and censored recovery. Recovery is the first accepted measurement after fault end, not proof of accurate process recovery. It can be immediate even after undetected faults. Missing initial estimates remain explicitly uninitialized.

## Methods and controlled comparisons

- `always_deny`: suppress every action; expected zero coverage, irrespective of its zero undesirable actions.
- `persistence_only`: finite measurements, hold for missing inputs, then the common controller.
- `hampel`, `cusum`: existing streaming detectors; accept raw values on gate pass, otherwise hold. Their internally filtered estimates and authorizations are not used.
- `lof`: development-fitted univariate novelty detector; the same accept/hold/controller wrapper.
- `aasvr_hold_only`: AASVR measurement gates with the same hold/controller wrapper as the other detectors.
- `aasvr_measurement`: identical AASVR gates and wrapper, plus a requirement that the current gate pass to authorize. This pair isolates the additional authorization veto.
- `aasvr_no_cusum`: supervisor arm with the CUSUM component removed.

Response-memory and actuator-dependent uncommanded-trend gates are disabled in all main AASVR arms because actuator activity is unknown. The existing trust score is retained internally as an audit calculation, not an independently claimed source of decision improvement. Legacy code is not silently patched or its old tables relabeled. The main arms use actual inter-sample intervals for rate gates; the common controller handles persistence, cooldown, and estimate age in seconds.

Common wrapper transition rules:

| Condition | Estimate and age | Persistence | Authorization |
|---|---|---|---|
| Startup without accepted input | Uninitialized | Reset | Deny |
| Finite accepted measurement | Replace held estimate; age zero | Accumulate if eligible, same-direction out-of-band | Pulse when persistence met and cooldown expired |
| Rejected/missing measurement | Hold; age increases | Continue only if held evidence remains eligible | Hold-only arms may authorize within age limit; supervisor arms veto |
| Age exceeds limit | Held estimate remains diagnostic | Reset | Deny |
| In-band estimate or direction change | Retain accepted-state rules | Reset/restart | Deny until eligibility/persistence |
| Long timestamp gap | Invalidate held value; require new acceptance | Reset; preserve outstanding cooldown | Deny until eligibility/persistence |
| Authorization pulse | No causal change to historical trajectory | Continues while eligible | Next pulse no earlier than cooldown expiry |

The underlying AASVR gates and state implementation remain in `src/aasvr/core.py`. This compact study does not claim to have solved genuine-shift or stuck-value identifiability.

## Selection and uncertainty

Threshold multipliers (0.75, 1, 1.5), persistence (0, 32, 96 seconds), and maximum evidence age (64, 320 seconds) are declared before execution. At each minimum validation coverage target (50%, 80%, 95%), choose the lowest undesirable-action rate, breaking ties by current fault-evidence authorization, higher coverage, and setting identifier. A method unable to meet a target is explicitly infeasible. Always-deny remains an unconditional diagnostic comparator.

Selections are written before evaluation scoring. Evaluation coverage need not equal validation targets: a failure to transfer is reported, not retuned. Multiple targets may choose the same setting; they do not create independent replications. Evaluation compares these locked operating points, not an interpolated claim of exactly equal coverage.

Paired effect differences against persistence-only use identical trials and a source-day cluster bootstrap: resample days jointly across all their windows, sensors, and scenarios for both methods. Report two-sided percentile 95% intervals and the number of days. A small number of days and only one chronological split limit inference. The script does not claim equivalence from overlapping intervals and does not perform an uncorrected collection of significance tests.

## Recovery and computation

`legacy_recovery_traces.csv` and its summary document AASVR-R on deterministic failed-response, no-command, missing-response-window, legitimate-shift, fault-exit, and long-gap cases. They are regression/audit evidence, not plant experiments. Healthy measurements alone do not necessarily restore response authority. No time-only reliability reset is introduced.

Runtime measurements use the available host inside Docker, single-thread environment settings, and serial interleaving of 1, 8, and 32 software streams. They report initialization separately from streaming latency and Python allocations. They do not establish Raspberry Pi performance, hard real-time bounds, physical hydroponic scalability, or total-device memory use.

## Decision rule

Proceed to a manuscript rebuild only if the locked temporal evaluation supports a useful, reproducible advantage over simpler policies at comparable coverage. Otherwise simplify the supervisor or narrow the paper. These outputs must not be substituted into the existing manuscript without changing its populations, definitions, and conclusions.

### Diagnostic follow-up and compact-study stopping point

When a supervisor fails every declared coverage target, `scripts/40_reanalysis_diagnostics.py` selects its highest-coverage **validation** setting, saves that choice, and runs a separately labeled evaluation. This does not make an infeasible method eligible for the primary comparison. `scripts/39_report_reanalysis.py` generates the report and figures. The Make target runs all three scripts in order.

The completed compact run produced no wrong-direction authorizations. Its fixed-onset, single-magnitude injections were not selected specifically near control thresholds. This limits that endpoint and must remain visible; more injections of the same design would not remove the limitation. The observed coverage deficit is a reason to pause the manuscript rebuild and narrow the contribution, rather than choose easier targets after inspecting results.
