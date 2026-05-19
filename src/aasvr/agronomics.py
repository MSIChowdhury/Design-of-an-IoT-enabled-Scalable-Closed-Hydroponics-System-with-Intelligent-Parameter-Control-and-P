from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


AGRONOMIC_RAW = Path("data/raw/hydroponic/agronomic_harvest.csv")
AGRONOMIC_TEMPLATE = Path("data/raw/hydroponic/agronomic_harvest_template.csv")
AGRONOMIC_PROCESSED = Path("data/processed/hydro_agronomic_harvest.parquet")
AGRONOMIC_QUALITY = Path("results/run_metadata/hydro_agronomic_data_quality.csv")

REQUIRED_COLUMNS = (
    "experiment",
    "treatment",
    "plant_id",
    "FMAP_g",
    "DMAP_g",
    "TPL_cm",
    "RL_cm",
    "SL_cm",
    "TNL_count",
    "NL10_count",
)

OPTIONAL_COLUMNS = (
    "protein_g_100g",
    "fat_g_100g",
    "tdf_g_100g",
    "carb_g_100g",
)

OUTCOME_COLUMNS = REQUIRED_COLUMNS[3:] + OPTIONAL_COLUMNS


@dataclass(frozen=True)
class AgronomicOutputs:
    processed_path: Path
    quality_path: Path


def write_agronomic_template(path: str | Path = AGRONOMIC_TEMPLATE) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for experiment in (1, 2):
        for treatment in ("P1", "P2", "P3"):
            rows.append(
                {
                    "experiment": experiment,
                    "treatment": treatment,
                    "plant_id": f"E{experiment}_{treatment}_001",
                    "FMAP_g": "",
                    "DMAP_g": "",
                    "TPL_cm": "",
                    "RL_cm": "",
                    "SL_cm": "",
                    "TNL_count": "",
                    "NL10_count": "",
                    "protein_g_100g": "",
                    "fat_g_100g": "",
                    "tdf_g_100g": "",
                    "carb_g_100g": "",
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def prepare_agronomic_harvest(
    raw_path: str | Path = AGRONOMIC_RAW,
    *,
    processed_path: str | Path = AGRONOMIC_PROCESSED,
    quality_path: str | Path = AGRONOMIC_QUALITY,
) -> AgronomicOutputs:
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Missing agronomic harvest sheet: {raw_path}. "
            f"Run scripts/22_prepare_agronomic.py --write-template and fill the per-plant values."
        )
    frame = pd.read_csv(raw_path)
    harvest = canonicalize_agronomic_frame(frame)
    quality = agronomic_quality_report(harvest, raw_path=raw_path)

    processed_path = Path(processed_path)
    quality_path = Path(quality_path)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    harvest.to_parquet(processed_path, index=False)
    quality.to_csv(quality_path, index=False)
    return AgronomicOutputs(processed_path=processed_path, quality_path=quality_path)


def canonicalize_agronomic_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Agronomic harvest sheet is missing required columns: {missing}")
    frame = frame[[*REQUIRED_COLUMNS, *[col for col in OPTIONAL_COLUMNS if col in frame.columns]]].copy()
    frame["experiment"] = pd.to_numeric(frame["experiment"], errors="raise").astype(int)
    if not frame["experiment"].isin([1, 2]).all():
        bad = sorted(frame.loc[~frame["experiment"].isin([1, 2]), "experiment"].unique())
        raise ValueError(f"Unsupported agronomic experiment values: {bad}")
    frame["treatment"] = frame["treatment"].astype(str).str.strip().str.upper()
    if not frame["treatment"].isin(["P1", "P2", "P3"]).all():
        bad = sorted(frame.loc[~frame["treatment"].isin(["P1", "P2", "P3"]), "treatment"].unique())
        raise ValueError(f"Unsupported agronomic treatment values: {bad}")
    frame["plant_id"] = frame["plant_id"].astype(str).str.strip()
    if frame["plant_id"].eq("").any():
        raise ValueError("Agronomic harvest sheet contains blank plant_id values.")
    duplicates = frame.duplicated(["experiment", "treatment", "plant_id"])
    if duplicates.any():
        dupes = frame.loc[duplicates, ["experiment", "treatment", "plant_id"]].to_dict("records")
        raise ValueError(f"Duplicate agronomic plant records: {dupes[:5]}")
    for col in OUTCOME_COLUMNS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    required_numeric = list(REQUIRED_COLUMNS[3:])
    if frame[required_numeric].isna().any().any():
        bad_cols = sorted(frame[required_numeric].columns[frame[required_numeric].isna().any()])
        raise ValueError(f"Required agronomic numeric columns contain missing/non-numeric values: {bad_cols}")
    if (frame[required_numeric] < 0).any().any():
        bad_cols = sorted(frame[required_numeric].columns[(frame[required_numeric] < 0).any()])
        raise ValueError(f"Agronomic numeric columns cannot be negative: {bad_cols}")
    frame["TNL_count"] = frame["TNL_count"].round().astype(int)
    frame["NL10_count"] = frame["NL10_count"].round().astype(int)
    if (frame["NL10_count"] > frame["TNL_count"]).any():
        raise ValueError("NL10_count cannot exceed TNL_count.")
    return frame.sort_values(["experiment", "treatment", "plant_id"]).reset_index(drop=True)


def agronomic_quality_report(harvest: pd.DataFrame, *, raw_path: str | Path) -> pd.DataFrame:
    rows = [
        {
            "raw_path": str(raw_path),
            "rows": len(harvest),
            "experiments": ",".join(map(str, sorted(harvest["experiment"].unique()))),
            "treatments": ",".join(sorted(harvest["treatment"].unique())),
            "unique_plants": harvest[["experiment", "treatment", "plant_id"]].drop_duplicates().shape[0],
        }
    ]
    for (experiment, treatment), frame in harvest.groupby(["experiment", "treatment"]):
        rows.append(
            {
                "raw_path": str(raw_path),
                "rows": len(frame),
                "experiments": str(experiment),
                "treatments": treatment,
                "unique_plants": frame["plant_id"].nunique(),
            }
        )
    return pd.DataFrame(rows)


def summarize_agronomic_harvest(
    harvest: pd.DataFrame,
    *,
    seed: int = 20260519,
    bootstrap_resamples: int = 1000,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    outcome_cols = [col for col in OUTCOME_COLUMNS if col in harvest.columns and harvest[col].notna().any()]
    for (experiment, treatment), frame in harvest.groupby(["experiment", "treatment"]):
        for outcome in outcome_cols:
            values = frame[outcome].dropna().to_numpy(dtype=float)
            if len(values) == 0:
                continue
            ci_low, ci_high = bootstrap_mean_ci(values, seed=seed, resamples=bootstrap_resamples)
            rows.append(
                {
                    "experiment": experiment,
                    "treatment": treatment,
                    "outcome": outcome,
                    "n": int(len(values)),
                    "mean": float(np.mean(values)),
                    "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                    "median": float(np.median(values)),
                    "iqr": float(np.percentile(values, 75) - np.percentile(values, 25)),
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "unit": _unit_for_outcome(outcome),
                }
            )
    return pd.DataFrame(rows)


def compute_linkage_table(
    harvest: pd.DataFrame,
    method_exposure: pd.DataFrame,
    *,
    experiment: int = 1,
) -> pd.DataFrame:
    p1 = harvest[(harvest["experiment"].eq(experiment)) & harvest["treatment"].eq("P1")].copy()
    if p1.empty:
        raise ValueError(f"No P1 agronomic records found for experiment {experiment}.")
    summary = summarize_agronomic_harvest(p1)
    primary_outcomes = summary[summary["outcome"].isin(["FMAP_g", "DMAP_g", "TPL_cm", "NL10_count"])].copy()
    rows = []
    for exposure in method_exposure.to_dict("records"):
        for outcome in primary_outcomes.to_dict("records"):
            rows.append(
                {
                    "experiment": experiment,
                    "treatment": "P1",
                    "method": exposure["method"],
                    "outcome": outcome["outcome"],
                    "outcome_mean": outcome["mean"],
                    "outcome_ci_low": outcome["ci_low"],
                    "outcome_ci_high": outcome["ci_high"],
                    "unsafe_band_rate": exposure.get("unsafe_band_rate", np.nan),
                    "untrusted_rate": exposure.get("untrusted_rate", np.nan),
                    "alert_rate": exposure.get("alert_rate", np.nan),
                    "authorization_rate": exposure.get("authorization_rate", np.nan),
                    "response_residual_rate": exposure.get("response_residual_rate", np.nan),
                    "instability_index": exposure.get("instability_index", np.nan),
                    "causal_interpretation": "mechanistic_link_only",
                }
            )
    return pd.DataFrame(rows)


def method_exposure_from_decisions(paths: dict[str, str | Path]) -> pd.DataFrame:
    rows = []
    for method, path in paths.items():
        path = Path(path)
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        rows.append(_exposure_row(method, frame))
    return pd.DataFrame(rows)


def _exposure_row(method: str, frame: pd.DataFrame) -> dict[str, float | str | int]:
    n = max(len(frame), 1)
    gate = frame.get("gate_result", pd.Series("", index=frame.index)).astype(str)
    state = frame.get("state", pd.Series("", index=frame.index)).astype(str)
    reason = frame.get("reason_codes", pd.Series("", index=frame.index)).astype(str)
    raw = pd.to_numeric(frame.get("raw_value", pd.Series(np.nan, index=frame.index)), errors="coerce")
    trusted = pd.to_numeric(frame.get("trusted_value", pd.Series(np.nan, index=frame.index)), errors="coerce")
    return {
        "method": method,
        "samples": int(len(frame)),
        "unsafe_band_rate": _mean_bool(frame.get("unsafe_band", False), n),
        "untrusted_rate": float((gate.eq("reject") | state.isin(["suspect", "persistent", "fault"])).mean()),
        "alert_rate": _mean_bool(frame.get("alert", False), n),
        "authorization_rate": _mean_bool(frame.get("actuation_authorized", False), n),
        "response_residual_rate": float(reason.str.contains("actuator_response_residual", regex=False).mean()),
        "instability_index": float((raw - trusted).abs().mean(skipna=True)),
    }


def bootstrap_mean_ci(values: np.ndarray, *, seed: int, resamples: int = 1000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 1:
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(resamples, len(values)), replace=True).mean(axis=1)
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def _mean_bool(values: pd.Series | bool, n: int) -> float:
    if isinstance(values, bool):
        return float(values)
    if values.dtype == object:
        normalized = values.astype(str).str.lower().isin(["true", "1", "yes"])
        return float(normalized.sum() / n)
    return float(values.astype(bool).sum() / n)


def _unit_for_outcome(outcome: str) -> str:
    if outcome.endswith("_g"):
        return "g"
    if outcome.endswith("_cm"):
        return "cm"
    if outcome.endswith("_count"):
        return "count"
    if outcome.endswith("_100g"):
        return "g/100g"
    return ""
