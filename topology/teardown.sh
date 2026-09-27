#!/usr/bin/env bash
# ==============================================================================
# Lab 2: Containerized Router Topology Teardown Script
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[-] Tearing down Lab 2 Virtual Network Testbed..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" down -v

echo "[+] Lab 2 teardown complete."
