"""Input validation performed before any recommendations are generated."""

import ipaddress
import math
import re

from .errors import ProfileValidationError
from .models import Profile

_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,31}$")


def validate_profile(profile: Profile) -> None:
    if not _NAME_RE.fullmatch(profile.profile_id):
        raise ProfileValidationError("profile_id must be 1-32 letters, digits, '_' or '-'.")
    try:
        root = ipaddress.ip_network(profile.root_cidr, strict=True)
    except ValueError as exc:
        raise ProfileValidationError(f"root_cidr is not a valid IPv4 network: {exc}") from exc
    if not isinstance(root, ipaddress.IPv4Network):
        raise ProfileValidationError("Only IPv4 CIDRs are supported by this release.")
    if profile.endpoint_count < 1:
        raise ProfileValidationError("endpoint_count must be at least 1.")
    if not profile.subnets:
        raise ProfileValidationError("At least one subnet request is required.")
    if not 1 <= profile.switch_port_density <= 512:
        raise ProfileValidationError("switch_port_density must be between 1 and 512 endpoints per access switch.")
    if profile.site_count < 1:
        raise ProfileValidationError("site_count must be at least 1.")
    if profile.resiliency not in {"standard", "redundant", "dual_homed"}:
        raise ProfileValidationError("resiliency must be 'standard', 'redundant', or 'dual_homed'.")
    if profile.target_latency_ms is not None and profile.target_latency_ms <= 0:
        raise ProfileValidationError("target_latency_ms must be positive when supplied.")
    if profile.target_latency_ms is not None and not math.isfinite(profile.target_latency_ms):
        raise ProfileValidationError("target_latency_ms must be a finite number.")
    try:
        ipaddress.IPv4Address(profile.router_id)
    except ValueError as exc:
        raise ProfileValidationError(f"router_id must be an IPv4 address: {exc}") from exc

    names: set[str] = set()
    vlans: set[int] = set()
    for subnet in profile.subnets:
        if not _NAME_RE.fullmatch(subnet.name):
            raise ProfileValidationError(f"Invalid subnet name '{subnet.name}'.")
        if subnet.name in names:
            raise ProfileValidationError(f"Duplicate subnet name '{subnet.name}'.")
        names.add(subnet.name)
        if subnet.hosts < 1:
            raise ProfileValidationError(f"Subnet '{subnet.name}' needs at least one endpoint host.")
        if subnet.vlan_id is not None:
            if not 1 <= subnet.vlan_id <= 4094:
                raise ProfileValidationError(f"VLAN ID for '{subnet.name}' must be 1-4094.")
            if subnet.vlan_id in vlans:
                raise ProfileValidationError(f"Duplicate VLAN ID {subnet.vlan_id}.")
            vlans.add(subnet.vlan_id)
        if not 0 <= subnet.area_id <= 4294967295:
            raise ProfileValidationError(f"OSPF area ID for '{subnet.name}' is out of range.")
        if subnet.ospf_cost is not None and not 1 <= subnet.ospf_cost <= 65535:
            raise ProfileValidationError(f"OSPF cost for '{subnet.name}' must be 1-65535.")

    link_names: set[str] = set()
    for link in profile.links:
        if not link.name or link.name in link_names:
            raise ProfileValidationError(f"Link names must be unique and non-empty ('{link.name}').")
        link_names.add(link.name)
        if link.distance_m < 0:
            raise ProfileValidationError(f"Distance for '{link.name}' cannot be negative.")
        if not math.isfinite(link.distance_m):
            raise ProfileValidationError(f"Distance for '{link.name}' must be finite.")
        if link.requested_medium not in {"auto", "copper", "fiber", "carrier"}:
            raise ProfileValidationError(
                f"Unsupported medium '{link.requested_medium}' on '{link.name}'."
            )
        if (
            link.connectors < 0
            or link.splices < 0
            or link.transceiver_budget_db <= 0
            or not math.isfinite(link.transceiver_budget_db)
        ):
            raise ProfileValidationError(f"Invalid optical assumptions on '{link.name}'.")

    acl_names: set[str] = set()
    for rule in profile.acls:
        if not _NAME_RE.fullmatch(rule.name) or rule.name in acl_names:
            raise ProfileValidationError(f"ACL names must be unique identifiers ('{rule.name}').")
        acl_names.add(rule.name)
        if rule.source not in names or rule.destination not in names:
            raise ProfileValidationError(
                f"ACL '{rule.name}' references an unknown source or destination subnet."
            )
        if rule.action != "deny":
            raise ProfileValidationError("Only explicit deny rules are currently supported; permit is implicit.")
    if profile.cloud_boundary:
        if profile.bgp_asn is None or profile.bgp_peer_asn is None or not profile.bgp_peer_link:
            raise ProfileValidationError(
                "Cloud-boundary profiles need bgp_asn, bgp_peer_asn, and bgp_peer_link."
            )
        if not 1 <= profile.bgp_asn <= 4294967295 or not 1 <= profile.bgp_peer_asn <= 4294967295:
            raise ProfileValidationError("BGP ASNs must be in the range 1-4294967295.")
        if profile.bgp_peer_link not in names:
            raise ProfileValidationError("bgp_peer_link must name one requested transit subnet.")
        if not next(item for item in profile.subnets if item.name == profile.bgp_peer_link).interface:
            raise ProfileValidationError("bgp_peer_link must refer to a subnet with a routed interface.")
    if profile.resiliency in {"redundant", "dual_homed"}:
        routed_handoffs = sum(1 for subnet in profile.subnets if subnet.interface)
        if routed_handoffs < 2:
            raise ProfileValidationError(
                f"{profile.resiliency} resiliency needs at least two routed handoff subnets."
            )
    if profile.vpn_remote_cidr:
        try:
            remote = ipaddress.ip_network(profile.vpn_remote_cidr, strict=True)
        except ValueError as exc:
            raise ProfileValidationError(f"vpn_remote_cidr is invalid: {exc}") from exc
        if not isinstance(remote, ipaddress.IPv4Network):
            raise ProfileValidationError("vpn_remote_cidr must be an IPv4 network.")
        if remote.overlaps(root):
            raise ProfileValidationError("vpn_remote_cidr must not overlap the local root_cidr.")
        if not profile.vpn_peer_ip:
            raise ProfileValidationError("vpn_peer_ip is required when vpn_remote_cidr is set.")
        try:
            peer = ipaddress.IPv4Address(profile.vpn_peer_ip)
        except ValueError as exc:
            raise ProfileValidationError(f"vpn_peer_ip is invalid: {exc}") from exc
        if peer.is_multicast or peer.is_unspecified:
            raise ProfileValidationError("vpn_peer_ip must be a unicast IPv4 address.")
    if profile.route_summary is not None:
        try:
            summary = ipaddress.ip_network(profile.route_summary, strict=True)
        except ValueError as exc:
            raise ProfileValidationError(f"route_summary is invalid: {exc}") from exc
        if not isinstance(summary, ipaddress.IPv4Network) or not root.subnet_of(summary):
            raise ProfileValidationError("route_summary must be an IPv4 aggregate containing root_cidr.")

