#!/usr/bin/env bash
# ==============================================================================
# Lab 2: Containerized Router Topology Startup Script
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Deploying Lab 2 Containerized Virtual Network (r1, r2, r3)..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d

echo "[*] Waiting 6 seconds for BGP neighbor convergence..."
sleep 6

echo "[+] Virtual network testbed online."
