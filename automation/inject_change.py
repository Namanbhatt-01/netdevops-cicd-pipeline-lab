#!/usr/bin/env python3
"""
NetDevOps Synthetic Failure & Drift Injection Tool
Used in CI/CD test automation to inject:
  - BGP neighbor shutdown (link failure / peering degradation)
  - Unauthorized prefix injection / route flapping
  - Interface MTU misconfiguration
"""

import argparse
import subprocess
import sys

def run_vtysh(container_name, commands):
    cmd_str = "\n".join(["conf t"] + commands + ["end"])
    res = subprocess.run(
        ["docker", "exec", "-i", container_name, "vtysh"],
        input=cmd_str,
        capture_output=True,
        text=True
    )
    return res.returncode == 0

def inject_bgp_failure(node="netdevops_r1", peer_ip="192.168.12.20"):
    print(f"[*] Injecting BGP failure: Shutting down peer {peer_ip} on {node}...")
    success = run_vtysh(node, ["router bgp", f"neighbor {peer_ip} shutdown"])
    if success:
        print(f"[+] BGP peer {peer_ip} administratively shut down.")
    else:
        print(f"[-] Failed to shut down BGP peer {peer_ip}.")

def restore_bgp(node="netdevops_r1", peer_ip="192.168.12.20"):
    print(f"[*] Restoring BGP session: Enabling peer {peer_ip} on {node}...")
    success = run_vtysh(node, ["router bgp", f"no neighbor {peer_ip} shutdown"])
    if success:
        print(f"[+] BGP peer {peer_ip} enabled.")

def inject_unauthorized_route(node="netdevops_r1", prefix="10.99.99.0/24"):
    print(f"[*] Injecting unauthorized route drift ({prefix}) on {node}...")
    run_vtysh(node, ["router bgp", f"address-family ipv4 unicast", f"network {prefix}"])

def main():
    parser = argparse.ArgumentParser(description="NetDevOps Failure Injection")
    parser.add_argument("--action", choices=["bgp-down", "bgp-restore", "inject-route"], required=True)
    parser.add_argument("--node", default="netdevops_r1")
    parser.add_argument("--peer", default="192.168.12.20")
    args = parser.parse_args()

    if args.action == "bgp-down":
        inject_bgp_failure(args.node, args.peer)
    elif args.action == "bgp-restore":
        restore_bgp(args.node, args.peer)
    elif args.action == "inject-route":
        inject_unauthorized_route(args.node)

if __name__ == "__main__":
    main()
