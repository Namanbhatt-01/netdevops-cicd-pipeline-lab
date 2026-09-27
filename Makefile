# Makefile: Lab 2 NetDevOps CI/CD Pipeline
SHELL := /bin/bash

.PHONY: help setup test snapshot drift-test remediate clean

help:
	@echo "=========================================================================="
	@echo "  🚀 NetDevOps CI/CD Pipeline & Containerized Network Testing Lab"
	@echo "=========================================================================="
	@echo "Usage:"
	@echo "  make setup        - Deploy containerized router testbed (r1, r2, r3)"
	@echo "  make test         - Execute automated Pytest assertion suite"
	@echo "  make snapshot     - Extract operational state snapshots (pre/post)"
	@echo "  make drift-test   - Inject synthetic failure and assert gatekeeper block"
	@echo "  make remediate    - Run automated drift remediation and self-healing"
	@echo "  make run-all      - Execute complete end-to-end automated experiment"
	@echo "  make clean        - Teardown virtual network containers"
	@echo "=========================================================================="

setup:
	@bash topology/setup_topology.sh

test:
	@pytest tests/ -v --html=artifacts/reports/netdevops_validation_report.html --self-contained-html

snapshot:
	@python3 automation/snapshot_engine.py --phase pre

drift-test:
	@python3 automation/inject_change.py --action bgp-down --node netdevops_r1 --peer 192.168.12.2
	@python3 automation/snapshot_engine.py --phase post
	@python3 automation/drift_remediator.py --check-only || true

remediate:
	@python3 automation/drift_remediator.py --remediate
	@python3 automation/snapshot_engine.py --phase post
	@python3 automation/drift_remediator.py --check-only

run-all:
	@bash run_lab2_experiment.sh

clean:
	@bash topology/teardown.sh
