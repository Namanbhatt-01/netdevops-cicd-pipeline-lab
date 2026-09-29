#!/usr/bin/env python3
"""
BGP Convergence Readiness Prober
Polls FRR nodes in a loop until all expected BGP sessions reach Established state or timeout expires.
"""

import argparse
import json
import subprocess
import sys
import time

def check_node_established(container_name: str, expected_peers: int) -> bool:
    try:
        res = subprocess.run(
            ["docker", "exec", container_name, "vtysh", "-c", "show ip bgp summary json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        peers = data.get("ipv4Unicast", {}).get("peers", {})
        if len(peers) < expected_peers:
            return False

        for peer_ip, pdata in peers.items():
            state = pdata.get("state")
            pfx = pdata.get("pfxRcvd")
            # In FRR, if established, pfxRcvd is an integer or state == Established
            if state != "Established" and not isinstance(pfx, int):
                return False
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Wait for BGP convergence")
    parser.add_argument("--nodes", default="netdevops_r1,netdevops_r2,netdevops_r3", help="Comma-separated node list")
    parser.add_argument("--timeout", type=int, default=45, help="Maximum seconds to wait")
    parser.add_argument("--interval", type=int, default=2, help="Poll interval in seconds")
    args = parser.parse_args()

    node_list = [n.strip() for n in args.nodes.split(",")]
    start_time = time.time()

    print(f"[*] Awaiting BGP convergence on nodes: {node_list} (timeout={args.timeout}s)...")
    while time.time() - start_time < args.timeout:
        all_ready = True
        for node in node_list:
            if not check_node_established(node, expected_peers=2):
                all_ready = False
                break

        if all_ready:
            elapsed = time.time() - start_time
            print(f"[+] BGP converged across all {len(node_list)} nodes in {elapsed:.1f}s.")
            sys.exit(0)

        time.sleep(args.interval)

    print(f"[-] ERROR: Timeout waiting for BGP convergence after {args.timeout}s!", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
