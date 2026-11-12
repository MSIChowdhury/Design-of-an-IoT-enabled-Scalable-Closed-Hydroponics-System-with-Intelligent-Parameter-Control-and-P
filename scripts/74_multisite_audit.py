"""Multi-site fault-to-actuation replication (frozen protocol docs/multisite/PROTOCOL.md).

S1 Pompeo chamber: low-cost Atlas pH/EC with logged firmware dose requests.
S2 Autonomous Greenhouse Challenge 2: commercial CO2 dosing (contrast).
S3 aquaponic IoT logger: fault prevalence only.
Flag, spike, flat-line, hold and authorize logic is reused unchanged from the
index audit (scripts/68, scripts/64). Raw third-party rows are read from
data/raw/multisite/ (gitignored) and never written out. Run in Docker.
"""
from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.reanalysis import Timing, authorize, hold_estimate
from aasvr.standin import _spikes

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/multisite"
OUT = ROOT / "results/multisite"
SEED, RESAMPLES = 20261112, 2000
# Firmware rule from Hydroponic_Control.ino: acid when pH > 5.85, nutrient when EC < 1100.
S1_RULE = {"pH": dict(low=-np.inf, high=5.85, direction=(-1,), range=(0.0, 14.0)),
           "EC": dict(low=1100.0, high=np.inf, direction=(1,), range=(0.0, 200000.0))}
S1_DOSE = {"pH": "pH_Dose_{k}", "EC": "EC_Dose_{k}"}
S2_RANGE = (0.0, 10000.0)
S3_RANGES = {"water_pH": (0.0, 14.0), "TDS": (0.0, 1000.0), "water_temp": (-55.0, 125.0)}
FLATLINE_SECONDS = 3600


# ---------- shared frozen definitions ----------

def flags(x, low, high):
    """Out-of-range, bound and spike flags exactly as in scripts/68."""
    finite = np.isfinite(x)
    in_range = finite & (x >= low) & (x <= high)
    out = finite & ~in_range
    bound = finite & ((x == low) | (x == high))
    spike, _, _ = _spikes(np.where(in_range, x, np.nan))
    spike = spike & ~out & ~bound
    return {"missing": ~finite, "out_of_range": out, "bound": bound, "spike": spike,
            "flagged": out | bound | spike, "in_range": in_range}


def flatline_mask(x, times, max_gap):
    """scripts/64 flat-line runs (>= 3600 s identical in-range values), gap scaled to site."""
    mask = np.zeros(len(x), dtype=bool)
    start = 0
    for i in range(1, len(x) + 1):
        if i == len(x) or x[i] != x[start] or times[i] - times[i - 1] > max_gap:
            if np.isfinite(x[start]) and times[i - 1] - times[start] >= FLATLINE_SECONDS:
                mask[start:i] = True
            start = i
    return mask


def site_timing(times):
    step = float(np.median(np.diff(times)))
    return step, Timing(persistence=2 * step, cooldown=0.0, max_gap=10 * step, max_age=4 * step)


def prevalence(unit, sensor, x, times, low, high):
    step, timing = site_timing(times)
    f = flags(x, low, high)
    dt = np.diff(times)
    span = times[-1] - times[0]
    row = {"unit": unit, "sensor": sensor, "samples": len(x), "median_interval_s": step,
           "gap_time_fraction": float(dt[dt > timing.max_gap].sum() / span) if span > 0 else np.nan,
           "flatline": float(flatline_mask(np.where(f["in_range"], x, np.nan), times, timing.max_gap).mean())}
    row.update({k: float(f[k].mean()) for k in ("missing", "out_of_range", "bound", "spike", "flagged")})
    return row


def day_bootstrap(per_day, ratio):
    """Percentile CI of ratio(sum of resampled day rows); days are the cluster."""
    rng = np.random.default_rng(SEED)
    values = per_day.to_numpy(dtype=float)
    if len(values) < 2:
        return np.nan, np.nan
    draws = []
    for _ in range(RESAMPLES):
        total = values[rng.integers(0, len(values), len(values))].sum(axis=0)
        draws.append(ratio(dict(zip(per_day.columns, total))))
    draws = np.asarray(draws, dtype=float)
    draws = draws[np.isfinite(draws)]
    return (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))) if len(draws) else (np.nan, np.nan)


def safe(a, b):
    return a / b if b else np.nan


# ---------- S1 parsing ----------

def read_s1_trial(folder: Path):
    """Return frame plus per-file exclusion log; misaligned rows are excluded, never repaired."""
    rows, log = [], []
    for path in sorted(folder.glob("*.txt")):
        with open(path, newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if header is None:
                log.append({"file": path.name, "rows": 0, "excluded_field_count": 0, "status": "empty"})
                continue
            header = [h.strip() for h in header]
            kept = bad = 0
            for record in reader:
                if not record or all(not c.strip() for c in record):
                    continue
                if len(record) != len(header):
                    bad += 1
                    continue
                rows.append(dict(zip(header, (c.strip() for c in record))))
                kept += 1
            log.append({"file": path.name, "rows": kept, "excluded_field_count": bad,
                        "status": "no data rows" if kept == 0 else "ok"})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame, log
    frame["timestamp"] = pd.to_datetime(frame.pop("Datetime"), errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp", kind="stable").reset_index(drop=True)
    for c in frame.columns.drop("timestamp"):
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    return frame, log


def s1_cell(trial, line, channel, frame):
    """Per-line replay; returns per-row outputs needed for summaries."""
    rule = S1_RULE[channel]
    x = frame[f"{channel}_LNS_{line}"].to_numpy(dtype=float)
    dose = frame[S1_DOSE[channel].format(k=line)].to_numpy(dtype=float)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    low, high = rule["range"]
    f = flags(x, low, high)
    step, timing = site_timing(times)
    logged = np.nan_to_num(dose) > 0
    firmware = (x > 5.85) if channel == "pH" else (x < 1100)
    arms = {"naive": (np.isfinite(x), 0.0), "range": (f["in_range"], 0.0),
            "range+persistence": (f["in_range"], timing.persistence),
            "range+persistence+bound": (f["in_range"] & ~f["bound"], timing.persistence)}
    out = {"day": frame.timestamp.dt.date.astype(str).to_numpy(), "logged": logged,
           "logged_flagged": logged & f["flagged"], "firmware": firmware, "step": step}
    for cooldown_name, cooldown in (("native", 0.0), ("600s", 600.0)):
        for arm, (accepted, persistence) in arms.items():
            estimate, age = hold_estimate(times, x, accepted, max_gap=timing.max_gap)
            actions = authorize(times, estimate, age <= timing.max_age, rule["low"], rule["high"],
                                replace(timing, persistence=persistence, cooldown=cooldown),
                                allowed_directions=rule["direction"])
            acted = actions != 0
            source = np.maximum.accumulate(np.where(accepted, np.arange(len(x)), -1))
            src_flag = np.zeros(len(x), dtype=bool)
            src_flag[acted] = f["flagged"][source[acted]]
            out[f"{cooldown_name}|{arm}|cmd"] = acted
            out[f"{cooldown_name}|{arm}|flag"] = acted & src_flag
    return out, f, x, times


def run_s1():
    base = RAW / "pompeo/repo/Low-Cost Sensor Data"
    prev, e2, e3, e4, parse_log = [], [], [], [], []
    for folder in sorted(base.iterdir()):
        trial = folder.name.split()[0]
        frame, log = read_s1_trial(folder)
        parse_log += [{"trial": trial, **r} for r in log]
        per_day = []
        for channel in S1_RULE:
            for line in range(1, 5):
                col = f"{channel}_LNS_{line}"
                if frame.empty or col not in frame:
                    continue
                out, f, x, times = s1_cell(trial, line, channel, frame)
                low, high = S1_RULE[channel]["range"]
                prev.append(prevalence(f"S1 {trial} line {line}", channel, x, times, low, high))
                logged, fw = out["logged"], out["firmware"]
                e3.append({"trial": trial, "line": line, "channel": channel, "rows": len(x),
                           "agreement": float(np.mean(logged == fw)),
                           "logged_and_rule": int((logged & fw).sum()), "logged_only": int((logged & ~fw).sum()),
                           "rule_only": int((~logged & fw).sum()), "neither": int((~logged & ~fw).sum())})
                cols = {k: v for k, v in out.items() if isinstance(v, np.ndarray) and v.dtype == bool}
                day = pd.DataFrame(cols).assign(day=out["day"]).groupby("day").sum()
                day["channel"], day["line"] = channel, line
                per_day.append(day)
        if not per_day:
            continue
        days = pd.concat(per_day)
        for channel, grp in days.groupby("channel"):
            d = grp.drop(columns=["channel", "line"]).groupby(level=0).sum()
            tot = d.sum()
            lo, hi = day_bootstrap(d[["logged", "logged_flagged"]], lambda s: safe(s["logged_flagged"], s["logged"]))
            e2.append({"site": "S1", "unit": trial, "channel": channel, "requests": int(tot.logged),
                       "flagged_source_requests": int(tot.logged_flagged),
                       "flagged_fraction": safe(tot.logged_flagged, tot.logged), "ci_low": lo, "ci_high": hi})
            for cooldown in ("native", "600s"):
                n_c, n_f = f"{cooldown}|naive|cmd", f"{cooldown}|naive|flag"
                g_c, g_f = f"{cooldown}|range+persistence|cmd", f"{cooldown}|range+persistence|flag"
                naive_flag, gate_flag = tot[n_f], tot[g_f]
                naive_clean, gate_clean = tot[n_c] - tot[n_f], tot[g_c] - tot[g_f]
                reduction = 1 - safe(gate_flag, naive_flag)
                retention = safe(gate_clean, naive_clean)
                sub = d[[n_c, n_f, g_c, g_f]]
                r_lo, r_hi = day_bootstrap(sub, lambda s: 1 - safe(s[g_f], s[n_f]))
                k_lo, k_hi = day_bootstrap(sub, lambda s: safe(s[g_c] - s[g_f], s[n_c] - s[n_f]))
                if naive_flag < 10:
                    verdict = "not testable"
                elif reduction >= 0.90 and retention >= 0.80:
                    verdict = "replicated"
                else:
                    verdict = "failed"
                row = {"trial": trial, "channel": channel, "cooldown": cooldown,
                       "naive_flagged": int(naive_flag), "gate_flagged": int(gate_flag),
                       "flagged_reduction": reduction, "reduction_ci": f"[{r_lo:.3f}, {r_hi:.3f}]",
                       "unflagged_retention": retention, "retention_ci": f"[{k_lo:.3f}, {k_hi:.3f}]",
                       "verdict": verdict if cooldown == "native" else f"secondary: {verdict}"}
                for arm in ("naive", "range", "range+persistence", "range+persistence+bound"):
                    row[f"{arm} commands"] = int(tot[f"{cooldown}|{arm}|cmd"])
                    row[f"{arm} flagged"] = int(tot[f"{cooldown}|{arm}|flag"])
                e4.append(row)
    return prev, e2, e3, e4, parse_log


# ---------- S2 and S3 ----------

def run_s2():
    prev, e2 = [], []
    for path in sorted((RAW / "agc2/x").glob("*/GreenhouseClimate.csv")):
        unit = path.parent.name
        frame = pd.read_csv(path, low_memory=False)
        frame["timestamp"] = pd.to_datetime(pd.to_numeric(frame["%time"], errors="coerce"), unit="D",
                                            origin="1899-12-30")
        frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        x = pd.to_numeric(frame["CO2air"], errors="coerce").to_numpy(dtype=float)
        dos = pd.to_numeric(frame["co2_dos"], errors="coerce").to_numpy(dtype=float)
        times = frame.timestamp.astype("int64").to_numpy() / 1e9
        prev.append(prevalence(f"S2 {unit}", "CO2air", x, times, *S2_RANGE))
        f = flags(x, *S2_RANGE)
        dosing = np.nan_to_num(dos) > 0
        d = pd.DataFrame({"day": frame.timestamp.dt.date, "logged": dosing,
                          "logged_flagged": dosing & f["flagged"]}).groupby("day").sum()
        lo, hi = day_bootstrap(d, lambda s: safe(s["logged_flagged"], s["logged"]))
        e2.append({"site": "S2", "unit": unit, "channel": "CO2", "requests": int(dosing.sum()),
                   "flagged_source_requests": int(d.logged_flagged.sum()),
                   "flagged_fraction": safe(d.logged_flagged.sum(), dosing.sum()), "ci_low": lo, "ci_high": hi})
    return prev, e2


def run_s3():
    frame = pd.read_csv(RAW / "aquaponic/pond_iot_2023_raw.csv", encoding="utf-8-sig")
    frame["timestamp"] = pd.to_datetime(frame["created_date"], errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp", kind="stable").reset_index(drop=True)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    return [prevalence("S3 pond", s, pd.to_numeric(frame[s], errors="coerce").to_numpy(dtype=float), times, *r)
            for s, r in S3_RANGES.items()]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p1, e2_1, e3, e4, parse_log = run_s1()
    p2, e2_2 = run_s2()
    p3 = run_s3()
    tables = {"fault_prevalence": p1 + p2 + p3, "observed_flagged_requests": e2_1 + e2_2,
              "firmware_agreement": e3, "gating_replay": e4, "s1_parse_log": parse_log}
    for name, rows in tables.items():
        pd.DataFrame(rows).to_csv(OUT / f"{name}.csv", index=False, float_format="%.5g")
    native = [r for r in e4 if r["cooldown"] == "native"]
    summary = {"protocol": "docs/multisite/PROTOCOL.md",
               "criterion": {v: sum(r["verdict"] == v for r in native)
                             for v in ("replicated", "failed", "not testable")},
               "e3_trials_passing_95pct": sorted({r["trial"] for r in e3}
                                                 - {r["trial"] for r in e3 if r["agreement"] < 0.95})}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    pd.set_option("display.width", 250)
    for name, rows in tables.items():
        if name != "s1_parse_log":
            print(f"\n== {name}\n{pd.DataFrame(rows).to_string(index=False)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
