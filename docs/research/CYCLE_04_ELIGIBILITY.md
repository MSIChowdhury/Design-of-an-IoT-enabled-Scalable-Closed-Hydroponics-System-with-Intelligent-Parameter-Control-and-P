# Independent reference log eligibility screen

Declared 2026-11-12 22:17:13 UTC, before inspecting any numerical sensor or reference
outcomes from the newly located repository. The publication's metadata and
selected methods/data-availability passages have already been read; this is
not a claim of ignorance of its published study. No raw values, gate scores or
authorization outcomes have been inspected. This is a source-eligibility
screen, not an experimental confirmation protocol.

Candidate: Pompeo and colleagues, Frontiers in Plant Science (2024), DOI
10.3389/fpls.2024.1270544, and its linked public repository
https://github.com/JeanPompeo/Hydroponic_Control_System_Chamber_1 .
The current GitHub tree is recorded in `external_reference_candidate.json`.
The methods describe four 2022 chamber trials, 10 s sensor logging, a separate
5 s environmental reference, and a co-located sensor pair. These are a
potentially independent source from the project's 2024 Bangladesh deployment.
Neither independence of errors nor calibration truth follows from that fact.

Inspect firmware/source descriptions and file headers first, with exact commit
and file identifiers. Identify units, sensor identity/location, timestamps,
clock/timezone conventions, raw versus filled values, control setpoints and
actuator directions. Do not fetch the full numerical population or score any
gate during this screen. Download at most small source files and header lines;
all third-party source remains local, with no raw-data redistribution.

Advance only if at least one controlled variable has an identifiable co-located
independent reference, usable time alignment, unfilled sensor observations,
and enough documented measurement information to define a defensible reference
uncertainty region. Controller bands/directions must be fixed from published
source or explicitly declared as counterfactual settings before outcome review.
An undocumented reference, ambiguous clock relation, or imputed truth cannot
be silently treated as ground truth. Logged dosing requests do not establish
delivered volume or relay execution.

If eligible, write a separate timestamped experimental protocol before reading
numerical outcomes. Reserve trial T1 for schema/pilot work and trials T2--T4 as
unopened candidate confirmation data. Freeze the candidate, baselines,
alignment/exclusion rules, outcomes, precision rationale and stopping rule
before those trials are opened. All public-paper facts and metadata seen here
must be disclosed. Do not tune on or repeatedly recycle the three reserved
trials. They share one apparatus and are not independent facilities.

If ineligible, retain the reason and stop this route without constructing a
favorable synthetic replacement. At most 500 MB of local CPU/Docker acquisition
would be considered in a later authorized protocol; no cost, author contact,
private access, or journal submission is authorized or needed for this screen.
