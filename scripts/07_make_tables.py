from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create manuscript toy tables.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Create hydroponic Experiment 1 tables.")
    parser.add_argument("--all-available", action="store_true", help="Create tables for all available processed datasets.")
    args = parser.parse_args()
    if args.hydro_exp1 or args.all_available:
        make_hydro_exp1_tables()
        if args.all_available:
            make_all_available_tables()
        if not args.toy:
            return
    if not args.toy:
        print("Real tables require completed benchmark metrics.")
        return
    metrics = ROOT / "results/metrics/toy_summary.csv"
    if not metrics.exists():
        raise SystemExit("Missing toy metrics; run scripts/06_compute_metrics.py --toy first.")
    frame = pd.read_csv(metrics)
    out = ROOT / "results/tables/toy_summary_table.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    print(f"Wrote {out}")


def make_hydro_exp1_tables() -> None:
    out_dir = ROOT / "results/tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = ROOT / "results/metrics/hydro_exp1_summary.csv"
    if summary.exists():
        frame = pd.read_csv(summary)
        frame.to_csv(out_dir / "hydro_exp1_method_summary.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_method_summary.csv'}")
    quality = ROOT / "results/run_metadata/hydro_exp1_data_quality.csv"
    if quality.exists():
        frame = pd.read_csv(quality)
        frame.to_csv(out_dir / "hydro_exp1_data_quality.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_data_quality.csv'}")
    synthetic = ROOT / "results/metrics/hydro_exp1_synthetic_summary.csv"
    if synthetic.exists():
        frame = pd.read_csv(synthetic)
        frame.to_csv(out_dir / "hydro_exp1_synthetic_summary.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_synthetic_summary.csv'}")
    by_fault = ROOT / "results/metrics/hydro_exp1_synthetic_by_fault_type.csv"
    if by_fault.exists():
        frame = pd.read_csv(by_fault)
        frame.to_csv(out_dir / "hydro_exp1_synthetic_by_fault_type.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_fault_type.csv'}")
    by_sensor = ROOT / "results/metrics/hydro_exp1_synthetic_by_sensor.csv"
    if by_sensor.exists():
        frame = pd.read_csv(by_sensor)
        frame.to_csv(out_dir / "hydro_exp1_synthetic_by_sensor.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_sensor.csv'}")
    by_sensor_fault = ROOT / "results/metrics/hydro_exp1_synthetic_by_sensor_fault_type.csv"
    if by_sensor_fault.exists():
        frame = pd.read_csv(by_sensor_fault)
        frame.to_csv(out_dir / "hydro_exp1_synthetic_by_sensor_fault_type.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_sensor_fault_type.csv'}")
    bootstrap = ROOT / "results/metrics/hydro_exp1_bootstrap_ci.csv"
    if bootstrap.exists():
        frame = pd.read_csv(bootstrap)
        frame.to_csv(out_dir / "hydro_exp1_bootstrap_ci.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_bootstrap_ci.csv'}")
    ranks = ROOT / "results/metrics/hydro_exp1_method_ranks.csv"
    if ranks.exists():
        frame = pd.read_csv(ranks)
        frame.to_csv(out_dir / "hydro_exp1_method_ranks.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_method_ranks.csv'}")
    ablation = ROOT / "results/metrics/hydro_exp1_ablation_summary.csv"
    if ablation.exists():
        frame = pd.read_csv(ablation)
        frame.to_csv(out_dir / "hydro_exp1_ablation_summary.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_ablation_summary.csv'}")
    tuning = ROOT / "results/metrics/hydro_exp1_aasvr_tuning.csv"
    if tuning.exists():
        frame = pd.read_csv(tuning).head(10)
        frame.to_csv(out_dir / "hydro_exp1_aasvr_tuning_top.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_aasvr_tuning_top.csv'}")


def make_all_available_tables() -> None:
    out_dir = ROOT / "results/tables"
    metrics_dir = ROOT / "results/metrics"
    processed_dir = ROOT / "data/processed"
    frames = []
    hydro_synthetic = metrics_dir / "hydro_exp1_synthetic_summary.csv"
    if hydro_synthetic.exists():
        frame = pd.read_csv(hydro_synthetic).copy()
        frame.insert(0, "dataset", "hydro_exp1_synthetic")
        frame["evaluation_unit"] = "sensor_sample"
        frames.append(frame)
    native_event_datasets = set()
    for path in sorted(metrics_dir.glob("*_native_event_summary.csv")):
        dataset = path.name.removesuffix("_native_event_summary.csv")
        if not _dataset_available_for_tables(dataset):
            continue
        frame = pd.read_csv(path)
        if {"dataset", "method"}.issubset(frame.columns):
            native_event_datasets.add(dataset)
            frames.append(frame)
    for path in sorted(metrics_dir.glob("*_summary.csv")):
        if path.name in {"toy_summary.csv", "hydro_exp1_summary.csv", "hydro_exp1_synthetic_summary.csv"}:
            continue
        dataset = path.name.removesuffix("_summary.csv")
        if dataset in native_event_datasets:
            continue
        if not _dataset_available_for_tables(dataset):
            continue
        frame = pd.read_csv(path)
        if {"dataset", "method"}.issubset(frame.columns):
            frames.append(frame)
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_csv(out_dir / "all_available_summary.csv", index=False)
        combined.sort_values(["dataset", "balanced_accuracy"], ascending=[True, False]).to_csv(
            out_dir / "main_benchmark_table.csv", index=False
        )
        print(f"Wrote {out_dir / 'all_available_summary.csv'}")
        print(f"Wrote {out_dir / 'main_benchmark_table.csv'}")
    dataset_rows = []
    for metadata_path in sorted(processed_dir.glob("*_metadata.csv")):
        dataset = metadata_path.name.removesuffix("_metadata.csv")
        if not _dataset_available_for_tables(dataset):
            continue
        metadata = pd.read_csv(metadata_path)
        dataset_rows.append(
            {
                "dataset": dataset,
                "variables": len(metadata),
                "sensors": int(metadata.get("role", pd.Series(dtype=str)).eq("sensor").sum()),
                "actuators": int(metadata.get("role", pd.Series(dtype=str)).eq("actuator").sum()),
                "metadata_path": str(metadata_path),
            }
        )
    if dataset_rows:
        pd.DataFrame(dataset_rows).to_csv(out_dir / "dataset_summary.csv", index=False)
        print(f"Wrote {out_dir / 'dataset_summary.csv'}")


def _dataset_available_for_tables(dataset: str) -> bool:
    if dataset in {"hydro_exp1", "hydro_exp1_synthetic"}:
        return True
    raw_dir = ROOT / "data/raw" / dataset
    return raw_dir.exists() and any(
        path.is_file() and (path.name.endswith(".csv") or path.name.endswith(".csv.gz"))
        for path in raw_dir.rglob("*")
    )


if __name__ == "__main__":
    main()
