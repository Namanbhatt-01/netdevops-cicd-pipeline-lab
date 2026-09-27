#!/usr/bin/env python3
"""
NetDevOps Automated Configuration & Operational State Drift Remediation Bot
Compares operational state snapshots (Pre vs Post vs Baseline):
  - BGP neighbor state assertions
  - Prefix count delta verification
  - Missing route detection
  - Automated remediation of drifted configurations via vtysh
"""

import argparse
import json
import os
import subprocess
import sys

def load_snapshot(phase):
    path = os.path.join(os.path.dirname(__file__), f"../artifacts/snapshots/snapshot_{phase}.json")
    if not os.path.exists(path):
        print(f"[!] Snapshot file not found: {path}")
        return None
    with open(path) as f:
        return json.load(f)

def run_vtysh_remediation(container_name, config_commands):
    print(f"[*] Applying automated remediation to {container_name}...")
    cmd_str = "\n".join(["conf t"] + config_commands + ["end", "write memory"])
    try:
        res = subprocess.run(
            ["docker", "exec", "-i", container_name, "vtysh"],
            input=cmd_str,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[+] Remediation successful on {container_name}")
        return True
    except Exception as e:
        print(f"[-] Remediation failed on {container_name}: {e}")
        return False

def check_and_remediate(check_only=True):
    pre = load_snapshot("pre")
    post = load_snapshot("post")

    if not pre or not post:
        print("[!] Cannot perform diff: pre or post snapshot missing.")
        return False

    drift_found = False
    print("======================================================================")
    print(" NetDevOps CI/CD Gatekeeper: Operational State Drift Analysis")
    print("======================================================================")

    for node, pre_info in pre["nodes"].items():
        post_info = post["nodes"].get(node, {})
        pre_peers = pre_info.get("bgp_summary", {}).get("ipv4Unicast", {}).get("peers", {})
        post_peers = post_info.get("bgp_summary", {}).get("ipv4Unicast", {}).get("peers", {})

        print(f"\n--- Node: {node} ---")
        # Check BGP Peers
        for peer_ip, pre_peer_data in pre_peers.items():
            pre_state = pre_peer_data.get("state")
            post_peer_data = post_peers.get(peer_ip, {})
            post_state = post_peer_data.get("state", "Down")

            if pre_state == "Established" and post_state != "Established":
                print(f"[-] DRIFT ALERT: BGP Peer {peer_ip} degraded from {pre_state} to {post_state}!")
                drift_found = True
                if not check_only:
                    print(f"[*] Triggering automated BGP peer reset / session restore...")
                    run_vtysh_remediation(node, [f"router bgp", f"neighbor {peer_ip} shutdown", f"no neighbor {peer_ip} shutdown"])
            else:
                print(f"[+] BGP Peer {peer_ip}: Stable ({post_state})")

        # Check Route Counts
        pre_routes = len(pre_info.get("routes", {}))
        post_routes = len(post_info.get("routes", {}))
        if post_routes < pre_routes:
            print(f"[-] DRIFT ALERT: Routing table shrunk from {pre_routes} to {post_routes} prefixes!")
            drift_found = True
        else:
            print(f"[+] Route Table: Healthy ({post_routes} installed prefixes)")

    print("\n======================================================================")
    if drift_found:
        print("[-] RESULT: State Drift Detected! PR gatekeeper failed assertions.")
        return False
    else:
        print("[+] RESULT: Zero State Drift Detected. Pipeline assertions PASSED.")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetDevOps Drift Remediator")
    parser.add_argument("--check-only", action="store_true", help="Perform drift check without modifying network")
    parser.add_argument("--remediate", action="store_true", help="Auto-remediate detected configuration drift")
    args = parser.parse_args()

    success = check_and_remediate(check_only=not args.remediate)
    sys.exit(0 if success else 1)
