# Cycle 3: isolated controlled-comparison reproduction

Declared 2026-11-12 21:51:43 UTC, before this rerun. This closes a package
reproducibility gap; it is not a new hypothesis test or independent validation.

Use the existing follow-up wrapper and its unchanged configuration to rerun all
original methods and the two post-hoc direct baselines. Redirect only output
paths to `results/metrics/research_reproduction_controlled/` and its figure/table
directories. Do not call the manuscript report writer. No original configuration,
source window, selection rule, method or synthetic scenario may change.

Primary endpoints: original summary, selections and windows reproduce under the
existing check at relative/absolute tolerance 1e-12; all eight follow-up summary
CSV files reproduce to the same tolerance; and the independently recomputed
paired source-day interval and sensor tables reproduce. Compressed detail bytes
need not match because gzip embeds timestamps; numerical CSV content is the
endpoint. Fingerprint original locked/follow-up outputs, configurations and
method files before/after. A mismatch stops completion and is retained; no
parameter search or result-dependent repair is allowed.

All original windows, channels, scenarios, deadlines and 1000 bootstrap draws
are included, with their existing seeds and seven evaluation-day clusters.
There is no new sample-size claim or statistical test. This rerun cannot make
the revealed evaluation independent, improve novelty, or restore a rejected
superiority claim. Current 178 passing tests and the complete-log preprocessing
reproduction are the low-cost execution pilot; the runner prints each completed
window so unexpectedly slow execution can be inspected without detaching it.

Use the existing local Docker image, one BLAS thread, no downloads or paid
compute. Limit execution to 20 minutes; preserve logs on failure or timeout.
Retain all failed attempts and output hashes. Large per-trial outputs remain
ignored; commit code, protocol, console log and compact comparison report only.
