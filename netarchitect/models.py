"""Typed inputs shared by validation, algorithms, reports, and config output."""

from dataclasses import dataclass
from typing import Any


def _text(value: Any, label: str, default: str | None = None) -> str:
    if value is None and default is not None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _integer(value: Any, label: str, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _number(value: Any, label: str, default: float | None = None) -> float:
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{label} must be a number")
    return float(value)


@dataclass(frozen=True)
class LinkSpec:
    name: str
    distance_m: float
    role: str = "backbone"
    requested_medium: str = "auto"
    connectors: int = 2
    splices: int = 0
    transceiver_budget_db: float = 23.0


@dataclass(frozen=True)
class SubnetSpec:
    name: str
    hosts: int
    purpose: str
    vlan_id: int | None = None
    area_id: int = 0
    interface: str | None = None
    ospf_cost: int | None = None


@dataclass(frozen=True)
class AccessRule:
    name: str
    source: str
    destination: str
    action: str = "deny"


@dataclass(frozen=True)
class Profile:
    profile_id: str
    name: str
    description: str
    root_cidr: str
    endpoint_count: int
    site_count: int
    cloud_boundary: bool
    target_latency_ms: float | None
    links: tuple[LinkSpec, ...]
    subnets: tuple[SubnetSpec, ...]
    acls: tuple[AccessRule, ...]
    switch_port_density: int = 48
    resiliency: str = "standard"
    route_summary: str | None = None
    router_id: str = "10.255.255.1"
    bgp_asn: int | None = None
    bgp_peer_asn: int | None = None
    bgp_peer_link: str | None = None
    vpn_peer_ip: str | None = None
    vpn_remote_cidr: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Profile":
        try:
            if not isinstance(data, dict):
                raise ValueError("profile root must be a JSON object")
            cloud_boundary = data.get("cloud_boundary", False)
            if not isinstance(cloud_boundary, bool):
                raise ValueError("cloud_boundary must be true or false")
            link_data = data.get("links", [])
            subnet_data = data.get("subnets")
            acl_data = data.get("acls", [])
            if not isinstance(link_data, list) or not isinstance(subnet_data, list) or not isinstance(acl_data, list):
                raise ValueError("links, subnets, and acls must be JSON arrays")
            links = tuple(
                LinkSpec(
                    name=_text(item.get("name"), "link name"),
                    distance_m=_number(item.get("distance_m"), "link distance_m"),
                    role=_text(item.get("role", "backbone"), "link role"),
                    requested_medium=_text(item.get("requested_medium", "auto"), "requested_medium"),
                    connectors=_integer(item.get("connectors", 2), "link connectors"),
                    splices=_integer(item.get("splices", 0), "link splices"),
                    transceiver_budget_db=_number(item.get("transceiver_budget_db", 23), "transceiver_budget_db"),
                )
                for item in data.get("links", [])
                if isinstance(item, dict)
            )
            if len(links) != len(link_data):
                raise ValueError("each links entry must be a JSON object")
            subnets = tuple(
                SubnetSpec(
                    name=_text(item.get("name"), "subnet name"),
                    hosts=_integer(item.get("hosts"), "subnet hosts"),
                    purpose=_text(item.get("purpose", "User segment"), "subnet purpose"),
                    vlan_id=_integer(item.get("vlan_id"), "vlan_id") if item.get("vlan_id") is not None else None,
                    area_id=_integer(item.get("area_id", 0), "area_id"),
                    interface=_text(item.get("interface"), "subnet interface") if item.get("interface") else None,
                    ospf_cost=_integer(item.get("ospf_cost"), "ospf_cost") if item.get("ospf_cost") is not None else None,
                )
                for item in subnet_data
                if isinstance(item, dict)
            )
            if len(subnets) != len(subnet_data):
                raise ValueError("each subnets entry must be a JSON object")
            acls = tuple(
                AccessRule(
                    name=_text(item.get("name"), "ACL name"),
                    source=_text(item.get("source"), "ACL source"),
                    destination=_text(item.get("destination"), "ACL destination"),
                    action=_text(item.get("action", "deny"), "ACL action").lower(),
                )
                for item in acl_data
                if isinstance(item, dict)
            )
            if len(acls) != len(acl_data):
                raise ValueError("each acls entry must be a JSON object")
            target_latency = data.get("target_latency_ms")
            cloud_text = data.get("cloud_boundary", False)
            return cls(
                profile_id=_text(data.get("profile_id"), "profile_id"),
                name=_text(data.get("name"), "name"),
                description=_text(data.get("description"), "description"),
                root_cidr=_text(data.get("root_cidr"), "root_cidr"),
                endpoint_count=_integer(data.get("endpoint_count"), "endpoint_count"),
                switch_port_density=_integer(data.get("switch_port_density", 48), "switch_port_density"),
                site_count=_integer(data.get("site_count", 1), "site_count"),
                cloud_boundary=cloud_text,
                resiliency=_text(data.get("resiliency", "standard"), "resiliency"),
                target_latency_ms=_number(target_latency, "target_latency_ms") if target_latency is not None else None,
                links=links,
                subnets=subnets,
                acls=acls,
                route_summary=(
                    _text(data.get("route_summary"), "route_summary")
                    if data.get("route_summary") is not None
                    else None
                ),
                router_id=_text(data.get("router_id", "10.255.255.1"), "router_id"),
                bgp_asn=_integer(data.get("bgp_asn"), "bgp_asn") if data.get("bgp_asn") is not None else None,
                bgp_peer_asn=_integer(data.get("bgp_peer_asn"), "bgp_peer_asn") if data.get("bgp_peer_asn") is not None else None,
                bgp_peer_link=_text(data.get("bgp_peer_link"), "bgp_peer_link") if data.get("bgp_peer_link") is not None else None,
                vpn_peer_ip=_text(data.get("vpn_peer_ip"), "vpn_peer_ip") if data.get("vpn_peer_ip") is not None else None,
                vpn_remote_cidr=_text(data.get("vpn_remote_cidr"), "vpn_remote_cidr") if data.get("vpn_remote_cidr") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid profile structure: {exc}") from exc

