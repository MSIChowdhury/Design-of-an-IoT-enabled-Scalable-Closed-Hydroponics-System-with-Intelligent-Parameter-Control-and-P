.PHONY: test smoke prepare evaluate figures manuscript-check paper real all stats subset-protocol agronomic optional-evidence water-calibration exhaustive-mini exhaustive-grid exhaustive-test exhaustive-aggregate exhaustive-sweep-mini

PYTHON ?= python

test:
	$(PYTHON) -m pytest -q

smoke:
	$(PYTHON) scripts/run_all.py --toy

prepare:
	$(PYTHON) scripts/01_validate_data_layout.py
	$(PYTHON) scripts/02_prepare_datasets.py --toy

evaluate:
	$(PYTHON) scripts/04_run_methods.py --toy
	$(PYTHON) scripts/05_inject_faults.py --toy
	$(PYTHON) scripts/06_compute_metrics.py --toy

figures:
	$(PYTHON) scripts/07_make_tables.py --toy
	$(PYTHON) scripts/08_make_figures.py --toy

stats:
	$(PYTHON) scripts/10_run_ablation.py --hydro-exp1
	$(PYTHON) scripts/11_statistical_analysis.py --hydro-exp1

subset-protocol:
	$(PYTHON) scripts/download_datasets.py --all --profile paper
	$(PYTHON) scripts/12_make_subset_protocol.py --profile paper

agronomic:
	$(PYTHON) scripts/22_prepare_agronomic.py
	$(PYTHON) scripts/23_agronomic_linkage.py
	$(PYTHON) scripts/07_make_tables.py --hydro-exp1
	$(PYTHON) scripts/08_make_figures.py --hydro-exp1

optional-evidence:
	$(PYTHON) scripts/24_prepare_optional_evidence.py --write-templates --hydro-exp1

water-calibration:
	$(PYTHON) scripts/25_calibrate_water_level.py

exhaustive-mini:
	$(PYTHON) scripts/26_build_exhaustive_fault_grid.py --profile mini
	$(PYTHON) scripts/27_run_exhaustive_benchmark.py --profile mini --split test --methods aasvr_r,aasvr_no_response,no_cusum,lockout_only,cusum_only
	$(PYTHON) scripts/29_aggregate_exhaustive_results.py --profile mini --split test --bootstrap 100

exhaustive-grid:
	$(PYTHON) scripts/26_build_exhaustive_fault_grid.py --profile exhaustive

exhaustive-test:
	$(PYTHON) scripts/27_run_exhaustive_benchmark.py --profile exhaustive --split test

exhaustive-aggregate:
	$(PYTHON) scripts/29_aggregate_exhaustive_results.py --profile exhaustive --split test

exhaustive-sweep-mini:
	$(PYTHON) scripts/28_sweep_aasvr_exhaustive.py --profile mini --split validation --max-settings 16

manuscript-check:
	$(PYTHON) scripts/check_manuscript.py

paper:
	cd "Paper Files" && latexmk -pdf -interaction=nonstopmode -halt-on-error main_aasvr.tex
	cd "Paper Files" && latexmk -pdf -interaction=nonstopmode -halt-on-error main_aasvr_blinded.tex

real:
	$(PYTHON) scripts/run_all.py --available-real

all: test smoke manuscript-check
