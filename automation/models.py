from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class BgpPeer(BaseModel):
    peer_ip: str
    remote_as: int
    state: Literal["Established", "Idle", "Active", "Connect", "OpenSent", "OpenConfirm", "Down"]
    prefixes_received: int = 0
    uptime_seconds: int = 0

class Route(BaseModel):
    prefix: str
    protocol: str
    next_hops: List[str] = Field(default_factory=list)
    metric: Optional[int] = None

class InterfaceState(BaseModel):
    name: str
    admin_up: bool
    oper_up: bool
    mtu: int = 1500
    rx_packets: int = 0
    tx_packets: int = 0
    rx_drops: int = 0
    tx_drops: int = 0

class CanonicalNetworkState(BaseModel):
    node: str
    collected_at: datetime
    peers: List[BgpPeer] = Field(default_factory=list)
    routes: List[Route] = Field(default_factory=list)
    interfaces: List[InterfaceState] = Field(default_factory=list)

class RemediationPlan(BaseModel):
    plan_id: str
    target_node: str
    reason: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    commands: List[str]
    rollback_commands: List[str]
    verification_assertions: List[str]
    status: Literal["PLANNED", "DRY_RUN", "APPLIED", "ROLLED_BACK", "VERIFIED"] = "PLANNED"
