import json
import os
import pytest

def test_zero_bgp_peer_drift():
    """
    Asserts that baseline pre-change snapshot has consistent BGP peering across all nodes.
    """
    snap_dir = os.path.join(os.path.dirname(__file__), "../artifacts/snapshots")
    pre_file = os.path.join(snap_dir, "snapshot_pre.json")

    if not os.path.exists(pre_file):
        pytest.skip("Pre snapshot not present for drift assertion")

    with open(pre_file) as f1:
        pre = json.load(f1)

    for node, pre_node_data in pre["nodes"].items():
        pre_peers = pre_node_data.get("bgp_summary", {}).get("ipv4Unicast", {}).get("peers", {})
        assert len(pre_peers) >= 2, f"Baseline peer count on {node} is incomplete ({len(pre_peers)} peers)"

        for peer_ip, pre_peer in pre_peers.items():
            assert pre_peer.get("state") == "Established", f"Peer {peer_ip} on {node} not Established in baseline"
