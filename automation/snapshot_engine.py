#!/usr/bin/env python3
"""
NetDevOps Automated Network State Snapshot Engine
Connects to live containerized network nodes (FRR / Linux) via Scrapli/vtysh:
  - Extracts BGP neighbor summary JSON (state, uptime, pfxRcvd)
  - Extracts IPv4 routing table JSON (installed prefixes, protocols, next-hops)
  - Extracts interface statistics (RX/TX counters, drops, MTU)
Saves structured snapshots into artifacts/snapshots/snapshot_<phase>.json
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

def run_vtysh(container_name, command):
    """Executes a command inside the container via vtysh."""
    try:
        res = subprocess.run(
            ["docker", "exec", container_name, "vtysh", "-c", command],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[!] Error executing vtysh on {container_name}: {e.stderr}")
        return "{}"
    except Exception as e:
        print(f"[!] Exception calling docker exec: {e}")
        return "{}"

def run_ip_cmd(container_name, command):
    """Executes an iproute2 command inside the container."""
    try:
        res = subprocess.run(
            ["docker", "exec", container_name, "ip", "-j"] + command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "[]"

def collect_node_state(node_name):
    # 1. BGP Summary JSON
    bgp_raw = run_vtysh(node_name, "show ip bgp summary json")
    try:
        bgp_json = json.loads(bgp_raw)
    except Exception:
        bgp_json = {}

    # 2. Routing Table JSON
    route_raw = run_vtysh(node_name, "show ip route json")
    try:
        route_json = json.loads(route_raw)
    except Exception:
        route_json = {}

    # 3. Interface Details JSON
    links_raw = run_ip_cmd(node_name, "-d link show")
    try:
        links_json = json.loads(links_raw)
    except Exception:
        links_json = []

    return {
        "node": node_name,
        "collected_at": datetime.utcnow().isoformat(),
        "bgp_summary": bgp_json,
        "routes": route_json,
        "interfaces": links_json
    }

def main():
    parser = argparse.ArgumentParser(description="NetDevOps State Snapshot Engine")
    parser.add_argument("--phase", choices=["pre", "post", "baseline"], default="pre", help="Snapshot lifecycle phase")
    args = parser.parse_args()

    nodes = ["netdevops_r1", "netdevops_r2", "netdevops_r3"]
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": args.phase,
        "nodes": {}
    }

    print(f"[*] Extracting NetDevOps state snapshot (Phase: {args.phase})...")
    for node in nodes:
        print(f" -> Sampling operational state from {node}...")
        snapshot["nodes"][node] = collect_node_state(node)

    out_dir = os.path.join(os.path.dirname(__file__), "../artifacts/snapshots")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"snapshot_{args.phase}.json")

    with open(out_file, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"[+] State snapshot successfully saved: {out_file}")

if __name__ == "__main__":
    main()
