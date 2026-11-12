"""EC dose-response identification check (frozen: docs/multisite/IDENTIFICATION_PROTOCOL.md).

Fits EC[k+1] = EC[k] + a*N[k-d] + b*W[k-d] + c on 1-min clean bins of S1
trials T1-T2 per line, then validates open-loop simulation on T3 and T4
against Hold and drift-only. pH is secondary and exploratory. Run in Docker
with PYTHONPATH=/workspace:/workspace/src.
"""
from __future__ import annotations

import importlib
import json

import numpy as np
import pandas as pd

ms = importlib.import_module("scripts.74_multisite_audit")

TRAIN, TEST = ("T1", "T2"), ("T3", "T4")
DELAYS = (0, 1, 2, 5, 10)
HORIZONS = (10, 30, 60)
PRIMARY_H = 30
CHANNELS = {"EC": dict(dose="EC_Dose_{k}", range=(0.0, 200000.0)),
            "pH": dict(dose="pH_Dose_{k}", range=(0.0, 14.0))}


def bins(frame, channel, line):
    """1-min bins: median reading, request counts, clean flag; gaps reindexed as unclean."""
    spec = CHANNELS[channel]
    x = frame[f"{channel}_LNS_{line}"].to_numpy(dtype=float)
    f = ms.flags(x, *spec["range"])
    df = pd.DataFrame({"minute": frame.timestamp.dt.floor("min"), "x": np.where(f["missing"], np.nan, x),
                       "flag": f["flagged"], "N": frame[spec["dose"].format(k=line)].fillna(0) > 0,
                       "W": frame[f"Water_Dose_{line}"].fillna(0) > 0})
    g = df.groupby("minute").agg(x=("x", "median"), n=("x", "count"), flag=("flag", "any"),
                                 N=("N", "sum"), W=("W", "sum"))
    g = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="min"))
    clean = (g.n.fillna(0) > 0) & ~g.flag.fillna(True).astype(bool)
    return {"x": g.x.to_numpy(float), "N": g.N.fillna(0).to_numpy(float),
            "W": g.W.fillna(0).to_numpy(float), "clean": clean.to_numpy(bool)}


def pairs(b, d):
    k = np.arange(max(d, 0), len(b["x"]) - 1)
    ok = b["clean"][k] & b["clean"][k + 1] & b["clean"][k - d]
    k = k[ok]
    X = np.column_stack([b["N"][k - d], b["W"][k - d], np.ones(len(k))])
    return X, b["x"][k + 1] - b["x"][k]


def ols_hc1(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    n, p = X.shape
    inv = np.linalg.pinv(X.T @ X)
    cov = inv @ (X.T * e**2) @ X @ inv * n / max(n - p, 1)
    return beta, np.sqrt(np.diag(cov)), n


def starts(b, d, H):
    """Every 30 min where bins k-d .. k+H are all clean."""
    c = b["clean"]
    out = [k for k in range(d, len(c) - H, 30) if c[k - d:k + H + 1].all()]
    return np.asarray(out, dtype=int)


def simulate_errors(b, d, H, a, bw, c, ks):
    err = []
    for k in ks:
        j = np.arange(k, k + H) - d
        err.append(b["x"][k] + a * b["N"][j].sum() + bw * b["W"][j].sum() + c * H - b["x"][k + H])
    return np.asarray(err)


def rmse(e):
    return float(np.sqrt(np.mean(np.square(e)))) if len(e) else np.nan


def fit_line(train_bins, d):
    X, y = map(np.concatenate, zip(*(pairs(b, d) for b in train_bins)))
    return ols_hc1(X, y), float(np.mean(y)) if len(y) else 0.0


def run(channel, data):
    params, valid = [], []
    for line in range(1, 5):
        train = [data[t][line] for t in TRAIN]
        best = None
        for d in DELAYS:
            (beta, _, _), _ = fit_line(train, d)
            ks = [starts(b, d, PRIMARY_H) for b in train]
            e = np.concatenate([simulate_errors(b, d, PRIMARY_H, *beta, k) for b, k in zip(train, ks)])
            score = rmse(e)
            if best is None or (np.isfinite(score) and score < best[1]):
                best = (d, score)
        d = best[0]
        (beta, se, n), drift = fit_line(train, d)
        params.append({"channel": channel, "line": line, "delay_min": d, "train_pairs": n,
                       "a_gain_per_request": beta[0], "a_ci_low": beta[0] - 1.96 * se[0],
                       "a_ci_high": beta[0] + 1.96 * se[0], "b_per_topup": beta[1],
                       "b_ci_low": beta[1] - 1.96 * se[1], "b_ci_high": beta[1] + 1.96 * se[1],
                       "c_drift_per_min": beta[2], "train_sim_rmse_h30": best[1]})
        for trial in TEST:
            b = data[trial][line]
            for H in HORIZONS:
                ks = starts(b, d, H)
                sim = simulate_errors(b, d, H, *beta, ks)
                hold = np.array([b["x"][k] - b["x"][k + H] for k in ks])
                dr = hold + drift * H
                valid.append({"channel": channel, "line": line, "trial": trial, "horizon_min": H,
                              "starts": len(ks), "rmse_sim": rmse(sim), "rmse_hold": rmse(hold),
                              "rmse_drift": rmse(dr)})
    return params, valid


def decide(params, valid):
    v = [r for r in valid if r["horizon_min"] == PRIMARY_H]
    passing = [r for r in v if r["starts"] >= 20 and r["rmse_sim"] <= 0.8 * r["rmse_hold"]
               and r["rmse_sim"] < r["rmse_drift"]]
    gain = [p for p in params if p["a_ci_low"] > 0]
    go = len(passing) >= 6 and len(gain) >= 3
    return {"cells_passing": len(passing), "cells_total": len(v),
            "cells_not_testable": sum(r["starts"] < 20 for r in v),
            "lines_positive_gain": len(gain), "decision": "GO" if go else "NO-GO"}


def main():
    raw = {t: ms.read_s1_trial(f)[0] for t, f in
           ((f.name.split()[0], f) for f in sorted((ms.RAW / "pompeo/repo/Low-Cost Sensor Data").iterdir()))}
    summary = {}
    for channel in CHANNELS:
        data = {t: {line: bins(raw[t], channel, line) for line in range(1, 5)} for t in raw}
        params, valid = run(channel, data)
        pd.DataFrame(params).to_csv(ms.OUT / f"identification_params_{channel}.csv", index=False, float_format="%.5g")
        pd.DataFrame(valid).to_csv(ms.OUT / f"identification_validation_{channel}.csv", index=False,
                                   float_format="%.5g")
        summary[channel] = decide(params, valid) | ({"role": "primary"} if channel == "EC" else
                                                    {"role": "exploratory, no gate"})
        pd.set_option("display.width", 220)
        print(f"\n== {channel} params\n{pd.DataFrame(params).to_string(index=False)}")
        print(f"\n== {channel} validation\n{pd.DataFrame(valid).to_string(index=False)}")
    (ms.OUT / "identification_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
