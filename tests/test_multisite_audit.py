import importlib

import numpy as np
import pandas as pd

ms = importlib.import_module("scripts.74_multisite_audit")

HEADER = "Datetime, pH_LNS_1, EC_LNS_1, pH_Dose_1, EC_Dose_1\n"


def test_s1_parser_excludes_misaligned_rows_and_logs_empty_files(tmp_path):
    (tmp_path / "a.txt").write_text(HEADER + "2022-03-05 00:00:00 , 6.0,1200,0.5,0\n"
                                    "2022-03-05 00:00:10 , 6.0,0.5,0\n")  # NaN reading dropped a field
    (tmp_path / "b.txt").write_text(HEADER)
    frame, log = ms.read_s1_trial(tmp_path)
    assert len(frame) == 1 and frame["pH_LNS_1"].iloc[0] == 6.0
    assert {r["file"]: r["excluded_field_count"] for r in log}["a.txt"] == 1
    assert {r["file"]: r["status"] for r in log}["b.txt"] == "no data rows"


def test_s1_replay_matches_firmware_and_persistence_drops_isolated_fault():
    n = 200
    t = pd.date_range("2022-03-05", periods=n, freq="10s")
    ph = np.full(n, 5.8)
    ph[50] = 0.0          # bound reading: firmware does not dose (0 <= 5.85)
    ph[100] = 20.0        # impossible reading: naive firmware doses acid
    ph[150:170] = 6.2     # genuine sustained high pH
    frame = pd.DataFrame({"timestamp": t, "pH_LNS_1": ph, "EC_LNS_1": 1200.0,
                          "pH_Dose_1": np.where(ph > 5.85, 0.5, 0.0), "EC_Dose_1": 0.0})
    out, f, _, _ = ms.s1_cell("T1", 1, "pH", frame)
    assert np.array_equal(out["logged"], out["firmware"])
    assert out["logged_flagged"].sum() == 1                      # the 20.0 reading
    assert out["native|naive|cmd"].sum() == 21 and out["native|naive|flag"].sum() == 1
    assert out["native|range+persistence|flag"].sum() == 0
    assert out["native|range+persistence|cmd"].sum() == 18       # 20 high samples minus 2-sample persistence


def test_flags_are_disjoint_categories():
    x = np.r_[np.full(20, 6.0), 15.0, 14.0, np.nan]
    f = ms.flags(x, 0.0, 14.0)
    assert f["out_of_range"][20] and f["bound"][21] and f["missing"][22]
    assert not (f["spike"] & (f["out_of_range"] | f["bound"])).any()
