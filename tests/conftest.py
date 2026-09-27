"""
Pytest Configuration & Fixtures for NetDevOps Validation Testbed
Provides live extraction from running containers or cached snapshot data.
"""

import json
import os
import subprocess
import pytest

@pytest.fixture(scope="session")
def live_node_names():
    return ["netdevops_r1", "netdevops_r2", "netdevops_r3"]

@pytest.fixture(scope="session")
def get_node_bgp():
    def _get_bgp(node_name):
        try:
            res = subprocess.run(
                ["docker", "exec", node_name, "vtysh", "-c", "show ip bgp summary json"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(res.stdout)
        except Exception:
            # Fallback to local pre snapshot if docker offline
            snap_path = os.path.join(os.path.dirname(__file__), "../artifacts/snapshots/snapshot_pre.json")
            if os.path.exists(snap_path):
                with open(snap_path) as f:
                    data = json.load(f)
                    return data.get("nodes", {}).get(node_name, {}).get("bgp_summary", {})
            return {}
    return _get_bgp

@pytest.fixture(scope="session")
def get_node_routes():
    def _get_routes(node_name):
        try:
            res = subprocess.run(
                ["docker", "exec", node_name, "vtysh", "-c", "show ip route json"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(res.stdout)
        except Exception:
            snap_path = os.path.join(os.path.dirname(__file__), "../artifacts/snapshots/snapshot_pre.json")
            if os.path.exists(snap_path):
                with open(snap_path) as f:
                    data = json.load(f)
                    return data.get("nodes", {}).get(node_name, {}).get("routes", {})
            return {}
    return _get_routes
