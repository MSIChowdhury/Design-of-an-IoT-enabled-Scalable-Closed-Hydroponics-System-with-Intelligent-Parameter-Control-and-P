.PHONY: test smoke prepare evaluate figures manuscript-check real all

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

manuscript-check:
	$(PYTHON) scripts/check_manuscript.py

real:
	$(PYTHON) scripts/run_all.py --available-real

all: test smoke manuscript-check
