"""POST-HOC diagnostics for the multi-site run (not part of the frozen protocol).

Explains the S1 pH firmware-rule mismatch and the S3 timestamp resolution.
Changes no frozen output. Run in Docker with PYTHONPATH=/workspace:/workspace/src.
"""
from __future__ import annotations

import importlib

import numpy as np
import pandas as pd

ms = importlib.import_module("scripts.74_multisite_audit")


def main():
    s3 = pd.read_csv(ms.RAW / "aquaponic/pond_iot_2023_raw.csv", encoding="utf-8-sig", usecols=["created_date"])
    t = pd.to_datetime(s3.created_date, errors="coerce")
    d = t.sort_values().diff().dt.total_seconds().dropna()
    print("S3 timestamp examples:", s3.created_date.iloc[[0, 1, 2]].tolist())
    print("S3 unique timestamps", t.nunique(), "of", len(t), "| median positive step (s)", d[d > 0].median())
    for folder in sorted((ms.RAW / "pompeo/repo/Low-Cost Sensor Data").iterdir()):
        frame, _ = ms.read_s1_trial(folder)
        day = frame.timestamp.dt.date
        per_line = []
        for k in range(1, 5):
            g = pd.DataFrame({"day": day, "rule": frame[f"pH_LNS_{k}"] > 5.85,
                              "logged": frame[f"pH_Dose_{k}"].fillna(0) > 0})
            per_line.append(g.groupby("day").sum())
        a = pd.concat(per_line).groupby(level=0).sum()
        paused = (a.logged == 0) & (a.rule > 0)
        dosed = np.concatenate([frame[f"pH_LNS_{k}"][frame[f"pH_Dose_{k}"].fillna(0) > 0].to_numpy()
                                for k in range(1, 5)])
        print(folder.name.split()[0], "days", len(a), "| days with rule>0 but no acid dose:", int(paused.sum()),
              "| share of logged doses at pH <= 5.85:", round(float(np.mean(dosed <= 5.85)), 3))


if __name__ == "__main__":
    main()
