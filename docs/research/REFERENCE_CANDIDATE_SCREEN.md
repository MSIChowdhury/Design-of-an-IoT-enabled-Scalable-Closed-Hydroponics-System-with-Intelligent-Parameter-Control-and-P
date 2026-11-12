# Independent chamber reference log screen

The newly located public chamber repository is a real, potentially independent
data source. It is **not yet eligible for a reference-truth confirmation test**
under the declared [screening rules](CYCLE_04_ELIGIBILITY.md). Numerical sensor
and reference outcomes were not opened or scored. This decision concerns the
present evidence contract, not the usefulness or overall quality of the dataset.

## What is established

The [2024 primary study](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1270544/full)
describes four 2022 chamber trials, low-cost and reference sensing at different
rates, co-located environmental sensors, and logged dosing requests. Its
linked repository contains about 345 MB of uncompressed files. The checked
source/header records are pinned to an exact commit in
`reference_schema_screen.json`; the complete file tree is recorded separately
in `external_reference_candidate.json`. The repository has no declared license
in its GitHub metadata. No raw data or third-party source is redistributed here.

Three small firmware sources were read completely. Two trial-T1 log headers
and one T1 reference header were read; no measurement row was read. The checked
Python logger expressions timestamp low-cost streams using naive computer
local time. Database connection/configuration content was excluded. Trials
T2--T4 remain unopened, and T1 has not been used for numerical pilot work.

The reference CSV header supplies date, time, CO2, air temperature and relative
humidity. It does not supply an independent pH or EC reference. The low-cost
header includes `CO2_Tank` and chemical-dosing fields. Firmware prints requested
states/quantities; these are not independently measured relay state, delivered
volume or evidence of successful physical execution. The CO2 controller uses
the average of canopy sensors, while the co-located comparison sensor is a
different channel; those roles must not be conflated.

## Why confirmation has not advanced

The inspected methods, headers and timestamp expressions do not establish an
independent bound on reference-versus-computer clock offset/drift or document
the study reference's calibration uncertainty. The manufacturer product page
locates the model but was not sufficient to verify those study-specific facts.
The paper's use of a reference and matched calendar times does not by itself
establish alignment to the seconds-scale supervisor studied in our manuscript.
This is an unresolved requirement, not proof that the authors' clocks were wrong.

Schema and source provenance also require care before any numerical pilot:
the two T1 headers differ, and the CO2 serializer can print a reading followed
by an additional missing-value marker under an out-of-range condition. Its
literal integer conversion also needs checking against sensor configuration.
These are source-level inspection findings, not diagnoses of faults in the
unopened logs or proof that this source was the exact historical firmware.
Silently repairing or excluding rows after seeing favorable gate outcomes would
be inappropriate.

The screen therefore stops before a gate comparison. No reference-alignment
offset was fitted from reserved outcomes, no healthy/fault labels were invented,
and no new held-out confirmation is claimed. The original public-data audit
and frozen method results are unchanged.

## Minimum information to unlock this route

Obtain the independent logger's clock configuration/synchronization history or
an externally justified alignment bound, the reference calibration/accuracy
record, and a versioned sensor/channel/firmware mapping. Establish an uncertainty
region and validate the parser on T1 before declaring the complete experimental
protocol. Then preserve T2--T4 for one frozen comparison, with dependence across
trials from the same apparatus explicitly retained. Environmental authorization
accuracy would still be distinct from observed pH/EC dosing or crop benefit.
The latter claims need independent chemical references and observed execution.

No author was contacted, equipment purchased, or experiment submitted. The
metadata gap could potentially be resolved without a new hardware purchase;
it should not be described as proof that all independent hydroponic data are
unavailable.
