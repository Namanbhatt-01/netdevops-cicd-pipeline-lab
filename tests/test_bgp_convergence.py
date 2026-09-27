import pytest

def test_bgp_sessions_established(live_node_names, get_node_bgp):
    """
    Asserts that all BGP neighbors on r1, r2, and r3 are in 'Established' state.
    """
    for node in live_node_names:
        bgp_data = get_node_bgp(node)
        peers = bgp_data.get("ipv4Unicast", {}).get("peers", {})
        assert len(peers) >= 2, f"Node {node} has fewer than 2 BGP peers configured (found {len(peers)})"

        for peer_ip, peer_info in peers.items():
            state = peer_info.get("state")
            assert state == "Established", f"BGP peer {peer_ip} on {node} is NOT Established! (Current state: {state})"

def test_bgp_prefix_exchange(live_node_names, get_node_bgp):
    """
    Asserts that each router has received expected route prefixes from peers.
    """
    for node in live_node_names:
        bgp_data = get_node_bgp(node)
        peers = bgp_data.get("ipv4Unicast", {}).get("peers", {})

        for peer_ip, peer_info in peers.items():
            pfx_rcvd = peer_info.get("pfxRcd", peer_info.get("pfxRcvd", 0))
            assert pfx_rcvd > 0, f"Node {node} received 0 prefixes from BGP peer {peer_ip}"

def test_full_mesh_route_table_convergence(live_node_names, get_node_routes):
    """
    Asserts all loopbacks (10.0.0.1, 10.0.0.2, 10.0.0.3) and subnets are present in routing tables.
    """
    expected_prefixes = ["10.0.0.1/32", "10.0.0.2/32", "10.0.0.3/32"]
    for node in live_node_names:
        routes = get_node_routes(node)
        for pfx in expected_prefixes:
            assert pfx in routes, f"Prefix {pfx} missing from routing table on {node}"
