#!/usr/bin/env python3
"""
NetDevOps Automated Canonical Network State Snapshot Engine
Transforms raw FRR/Linux command outputs into typed canonical domain models (BgpPeer, Route, InterfaceState).
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from models import BgpPeer, Route, InterfaceState, CanonicalNetworkState

def run_vtysh(container_name: str, command: str) -> str:
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
        return "{}"
    except Exception as e:
        return "{}"

def run_ip_cmd(container_name: str, command: str) -> str:
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

def parse_canonical_state(node_name: str) -> CanonicalNetworkState:
    # 1. Parse BGP
    peers = []
    bgp_raw = run_vtysh(node_name, "show ip bgp summary json")
    try:
        bgp_json = json.loads(bgp_raw)
        ipv4_peers = bgp_json.get("ipv4Unicast", {}).get("peers", {})
        for peer_ip, pdata in ipv4_peers.items():
            state_str = pdata.get("state", "Down")
            # Map FRR numeric pfxRcvd into state Established
            if isinstance(pdata.get("pfxRcvd"), int) or state_str == "Established":
                norm_state = "Established"
                pfx = pdata.get("pfxRcvd", 0) if isinstance(pdata.get("pfxRcvd"), int) else 0
            else:
                norm_state = state_str if state_str in ["Idle", "Active", "Connect", "OpenSent", "OpenConfirm"] else "Down"
                pfx = 0

            peers.append(BgpPeer(
                peer_ip=peer_ip,
                remote_as=pdata.get("remoteAs", 65000),
                state=norm_state,
                prefixes_received=pfx,
                uptime_seconds=pdata.get("peerUptimeMsec", 0) // 1000
            ))
    except Exception:
        pass

    # 2. Parse Routes
    routes = []
    route_raw = run_vtysh(node_name, "show ip route json")
    try:
        route_json = json.loads(route_raw)
        for prefix, entries in route_json.items():
            if isinstance(entries, list):
                for entry in entries:
                    nhops = [nh.get("ip") for nh in entry.get("nexthops", []) if nh.get("ip")]
                    routes.append(Route(
                        prefix=prefix,
                        protocol=entry.get("protocol", "unknown"),
                        next_hops=nhops,
                        metric=entry.get("metric")
                    ))
    except Exception:
        pass

    # 3. Parse Interfaces
    interfaces = []
    links_raw = run_ip_cmd(node_name, "-d link show")
    try:
        links_json = json.loads(links_raw)
        for link in links_json:
            flags = link.get("flags", [])
            interfaces.append(InterfaceState(
                name=link.get("ifname", "unknown"),
                admin_up="UP" in flags,
                oper_up=link.get("operstate") == "UP",
                mtu=link.get("mtu", 1500),
                rx_packets=link.get("stats64", {}).get("rx", {}).get("packets", 0),
                tx_packets=link.get("stats64", {}).get("tx", {}).get("packets", 0),
                rx_drops=link.get("stats64", {}).get("rx", {}).get("dropped", 0),
                tx_drops=link.get("stats64", {}).get("tx", {}).get("dropped", 0)
            ))
    except Exception:
        pass

    return CanonicalNetworkState(
        node=node_name,
        collected_at=datetime.utcnow(),
        peers=peers,
        routes=routes,
        interfaces=interfaces
    )

def main():
    parser = argparse.ArgumentParser(description="NetDevOps Canonical State Snapshot Engine")
    parser.add_argument("--phase", choices=["pre", "post", "baseline"], default="pre", help="Snapshot lifecycle phase")
    args = parser.parse_args()

    nodes = ["netdevops_r1", "netdevops_r2", "netdevops_r3"]
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": args.phase,
        "nodes": {}
    }

    print(f"[*] Extracting NetDevOps canonical state snapshot (Phase: {args.phase})...")
    for node in nodes:
        print(f" -> Normalizing domain state from {node}...")
        canonical = parse_canonical_state(node)
        snapshot["nodes"][node] = canonical.dict()

    out_dir = os.path.join(os.path.dirname(__file__), "../artifacts/snapshots")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"snapshot_{args.phase}.json")

    with open(out_file, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print(f"[+] Canonical snapshot successfully written to {out_file}")

if __name__ == "__main__":
    main()
