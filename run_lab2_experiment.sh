#!/usr/bin/env bash
# ==============================================================================
# Comprehensive Execution & Verification Script for Lab 2: NetDevOps CI/CD
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="${SCRIPT_DIR}/.venv/bin/python"
VENV_PYTEST="${SCRIPT_DIR}/.venv/bin/pytest"
REPORTS_DIR="${SCRIPT_DIR}/artifacts/reports"
SNAPS_DIR="${SCRIPT_DIR}/artifacts/snapshots"

mkdir -p "${REPORTS_DIR}" "${SNAPS_DIR}"

echo "=============================================================================="
echo " [STEP 1/5] Bootstrapping Virtual Router Testbed (r1, r2, r3) via Docker"
echo "=============================================================================="
docker compose -f "${SCRIPT_DIR}/topology/docker-compose.yml" up -d
echo "[*] Waiting 6 seconds for BGP neighbor adjacencies to converge..."
sleep 6

echo "=============================================================================="
echo " [STEP 2/5] Capturing Baseline Operational State Snapshot (Pre-Change)"
echo "=============================================================================="
"${VENV_PY}" "${SCRIPT_DIR}/automation/snapshot_engine.py" --phase pre

echo "=============================================================================="
echo " [STEP 3/5] Executing Automated Pytest Regression & Convergence Suite"
echo "=============================================================================="
"${VENV_PYTEST}" "${SCRIPT_DIR}/tests/" -v \
    --html="${REPORTS_DIR}/netdevops_validation_report.html" \
    --self-contained-html \
    --junitxml="${REPORTS_DIR}/junit.xml"

echo "=============================================================================="
echo " [STEP 4/5] Injecting Failure / Drift Scenario & Asserting Gatekeeper Response"
echo "=============================================================================="
echo "[*] Simulating unexpected link failure / BGP shutdown on r1..."
"${VENV_PY}" "${SCRIPT_DIR}/automation/inject_change.py" --action bgp-down --node netdevops_r1 --peer 192.168.12.2
sleep 2

echo "[*] Capturing degraded state snapshot (Post-Change)..."
"${VENV_PY}" "${SCRIPT_DIR}/automation/snapshot_engine.py" --phase post

echo "[*] Running Drift Remediator in CHECK-ONLY mode (Expecting drift alert)..."
"${VENV_PY}" "${SCRIPT_DIR}/automation/drift_remediator.py" --check-only || true

echo "[*] Running Drift Remediator in AUTO-REMEDIATE mode (Healing the network)..."
"${VENV_PY}" "${SCRIPT_DIR}/automation/drift_remediator.py" --remediate
sleep 4

echo "=============================================================================="
echo " [STEP 5/5] Re-verifying Post-Remediation Health"
echo "=============================================================================="
"${VENV_PY}" "${SCRIPT_DIR}/automation/snapshot_engine.py" --phase post
"${VENV_PY}" "${SCRIPT_DIR}/automation/drift_remediator.py" --check-only

echo "=============================================================================="
echo " [✓] Lab 2 NetDevOps Validation Pipeline Completed Successfully!"
echo "=============================================================================="
