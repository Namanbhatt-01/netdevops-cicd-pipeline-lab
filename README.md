# LAB 02: NetDevOps Change Validation & Configuration Drift Remediation

[![NetDevOps CI/CD Validation](https://github.com/Namanbhatt-01/netdevops-cicd-pipeline-lab/actions/workflows/netdevops_ci.yml/badge.svg)](https://github.com/Namanbhatt-01/netdevops-cicd-pipeline-lab/actions/workflows/netdevops_ci.yml)
[![Pytest Assertions](https://img.shields.io/badge/Pytest-Automated_Gatekeeper-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![FRRouting](https://img.shields.io/badge/Control_Plane-FRRouting_v9.1-orange)](https://frrouting.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reproducible NetDevOps CI/CD validation pipeline that evaluates pre/post-change routing states, executes automated Pytest regression assertions, and remediates configuration drift through policy-gated automation. Demonstrated on a containerized multi-node FRRouting reference architecture.

---

## 1. Problem Statement

Manual network changes in data centers frequently cause silent outages due to incomplete configuration audits, missing routes, or unintended BGP neighbor session teardowns. 

This repository establishes a **GitOps & NetDevOps Validation Pipeline**:
1. Normalizes vendor/device operational states into typed **Canonical Domain Models** (`BgpPeer`, `Route`, `InterfaceState`).
2. Replaces arbitrary sleep timers with deterministic **BGP convergence readiness polling**.
3. Enforces pre- and post-deployment state assertions via Pytest.
4. Detects operational drift and applies policy-gated remediation (`RemediationPlanner` $\to$ `PolicyGate` $\to$ `RemediationExecutor`).
5. Emits machine-readable evidence envelopes for control plane ingestion.

---

## 2. Canonical Domain Architecture

```
┌─────────────────────────────────────────────────────────┐
│               RAW DEVICE OUTPUTS (FRR / vtysh)          │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│          CANONICAL DOMAIN ADAPTER (Pydantic)            │
│  - BgpPeer (peer_ip, remote_as, state, prefixes)        │
│  - Route (prefix, protocol, next_hops, metric)          │
│  - InterfaceState (name, oper_up, rx/tx stats, drops)   │
└────────────────────────────┬────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
┌────────────────────────┐              ┌────────────────────────┐
│  Pytest State Engine   │              │ Policy-Gated Remediator│
│  - Adjacency checks    │              │  - Detect Drift        │
│  - Route installations │              │  - Build Plan          │
│  - Drop thresholds     │              │  - Policy Approval     │
└────────────────────────┘              └────────────────────────┘
```

---

## 3. Policy-Gated Remediation Lifecycle

```
[ Drift Detected ] ──> [ RemediationPlanner ] ──> [ PolicyGate ]
                                                        │
                                    ┌───────────────────┴───────────────────┐
                                    ▼ (Approved)                            ▼ (High Risk / Rejected)
                           [ RemediationExecutor ]                  [ Operator Alert ]
                                    │
                                    ▼
                         [ Re-verify Convergence ]
                                    │
                         [ Emit Signed Evidence ]
```

---

## 4. Evidence Envelope Output

The pipeline outputs an execution record to `poc/evidence.json`:

```json
{
  "schema_version": "1.0",
  "experiment": {
    "id": "netdevops-drift-001",
    "name": "Automated State Validation and Policy-Gated Drift Remediation"
  },
  "execution": {
    "run_id": "netdevops-20260929-144500",
    "timestamp": "2026-09-29T14:45:00Z",
    "environment": "docker-compose",
    "platform": "darwin-arm64"
  },
  "measurements": [
    { "metric": "pre_change_bgp_peers_established", "value": 6, "mode": "measured" },
    { "metric": "drift_remediation_recovery_seconds", "value": 3.2, "mode": "measured" },
    { "metric": "post_remediation_drift_count", "value": 0, "mode": "measured" }
  ],
  "assertions": [
    { "id": "NET-ASSERT-001", "name": "BGP Adjacency Established Across Topology", "passed": true },
    { "id": "NET-ASSERT-002", "name": "Zero Configuration Drift Post-Remediation", "passed": true }
  ],
  "result": "passed"
}
```

---

## 5. Quickstart & Local Execution

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Execute the Full Automated Pipeline
```bash
# 1. Start Topology & Run Verification Pipeline
./run_lab2_experiment.sh

# 2. Teardown
make clean
```

---

## 6. Known Limitations

1. **Reference Implementation Scope**: Device driver parsing and command execution currently target FRRouting (`vtysh`) and Linux `iproute2`; production multi-vendor environments would integrate Scrapli/NAPALM/Netmiko adapters for Cisco IOS-XE/NX-OS, Arista EOS, or Juniper JunOS.
2. **Remediation Risk Gate**: Remediation policies currently operate on a static risk taxonomy (`LOW`, `MEDIUM`, `HIGH`); dynamic blast radius calculation across multi-tenant VRFs is not implemented.
3. **Execution Environment**: Routing nodes run in Linux network namespaces within Docker containers rather than bare-metal hardware switches.

---

## 7. License

MIT License. See [LICENSE](LICENSE) for details.
