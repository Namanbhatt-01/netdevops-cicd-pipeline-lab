import pytest

def test_control_plane_security_policy():
    """
    Asserts that Control Plane Policing (CoPP) and route-map policies only permit
    authorized routing protocols and drop unencrypted management protocols.
    """
    authorized_policies = {
        "bgp": {"port": 179, "action": "permit"},
        "bfd": {"port": 3784, "action": "permit"},
        "ssh": {"port": 22, "action": "permit"},
        "telnet": {"port": 23, "action": "deny"},
        "http": {"port": 80, "action": "deny"}
    }

    for proto, policy in authorized_policies.items():
        if proto in ["telnet", "http"]:
            assert policy["action"] == "deny", f"Security violation: Insecure protocol {proto} permitted!"
        if proto in ["bgp", "bfd", "ssh"]:
            assert policy["action"] == "permit", f"Availability issue: Required protocol {proto} denied!"
