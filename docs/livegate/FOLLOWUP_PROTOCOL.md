# Post-hoc direct-baseline follow-up

This follow-up responds to review of the original locked comparison. It is
retrospective and post-hoc, not an extension of that comparison's preregistered
claim. It preserves all files in `results/metrics/livegate/`, the original
configuration, protocol, and LiveGate implementation.

Run `python scripts/70_livegate_followup.py` in Docker. The wrapper imports the
original runner, adds two gates in memory, and redirects all outputs to
`results/metrics/livegate_followup/` and `results/figures/livegate_followup/`.
All original methods are rerun. Original summary rows, selections, and source
windows must reproduce before the follow-up report is generated.

## Fixed additions

- **Fixed repeat cap:** accept the first R identical in-range finite readings;
  reject further repeats until a change, invalid reading, or logging gap over
  120 seconds. R is selected from {2, 4, 8, 16, 32, 64}. The selected cap is
  shared across channels. This six-value grid is larger than LiveGate's
  three-value epsilon grid and is disclosed rather than presented as equal
  tuning effort. The learned liveness rule is itself a per-sensor run threshold
  at fixed epsilon; this comparator tests whether a simpler global cap suffices,
  not whether all possible per-sensor fixed caps are inferior.
- **Physical-bound rejection:** reject nonfinite and out-of-range readings, and
  readings exactly at either declared physical bound. It has no detector tuning
  parameter.

Both gates use the original persistence options {0, 32, 96} seconds and held-value
maximum ages {64, 320} seconds, the 600-second cooldown, the bidirectional
controlled benchmark, all original 12 scenarios and five sensors, and the same
chronological source windows. Per-method settings are locked on validation by
the original lexicographic objective at coverage targets 0.5, 0.8, and 0.95.
Evaluation cannot change the grid, gates, or selections. Post-hoc status is
retained even though the added settings are selected only on validation.

## Metrics and uncertainty

The original `fault_evidence` counter means a command at a sample labelled as
injected faulty; a held clean estimate can supply that command. It does **not**
prove that the command used a faulty reading. We retain and relabel this metric
for exact reproduction of the original 69%/31% reductions. The
`held_fault_evidence` counter instead attributes the command to its last accepted
source reading. Both are reported, with held-source evidence central to the
follow-up comparison. Neither counter measures physical execution or damage.

Paired percentile 95% intervals use 1000 bootstrap draws of source days, jointly
across sensors, scenarios, and both methods. Evaluation contains eight windows
on seven source-day clusters, not 480 independent deployments. For each selected
method versus persistence-only we report absolute differences in coverage,
undesirable commands per trial, fault-interval commands per trial, and
held-fault-source commands per trial, plus relative reductions for the last two.
Relative reductions are undefined when the reference count is zero; the report
records the number of defined bootstrap draws. Intervals are descriptive and
not corrected for the many secondary comparisons. Sensor-stratified metrics
and intervals accompany pooled results and availability costs.

The selected setting is fixed during bootstrap; intervals do not capture
uncertainty from selecting settings or from reusing previously analysed data.
Existing day clusters are few, so the intervals must not be read as broad
external-validation guarantees.
