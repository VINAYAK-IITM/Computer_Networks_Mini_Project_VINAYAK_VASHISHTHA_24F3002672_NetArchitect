"""Topology-aware routing selection with human-readable reasoning."""


def select_routing(profile, subnet_count: int) -> dict:
    if profile.cloud_boundary:
        internal = "Multi-Area OSPF"
        external = "eBGP at the cloud/provider boundary"
        reason = (
            f"The design spans {profile.site_count} sites and crosses a cloud/provider "
            "autonomous-system boundary. Use OSPF internally for site reachability and "
            "eBGP at the external boundary for policy-controlled route exchange. "
            f"Summarize only the reserved enterprise aggregate {profile.route_summary or profile.root_cidr} "
            "after installing an appropriate discard route and proving the aggregate does not hide gaps."
        )
    elif profile.site_count > 1:
        internal = "Multi-Area OSPF"
        external = None
        reason = (
            f"The design joins {profile.site_count} sites with redundant paths. Use Area 0 "
            "as the backbone and place site links in planned non-backbone areas; summarize "
            "at ABRs only after contiguous site prefixes are reserved. OSPF cost and carrier "
            "SLA design must be checked against the failover and latency targets."
        )
    elif subnet_count < 50:
        internal = "Single-Area OSPF, Area 0"
        external = None
        reason = (
            f"The profile has {subnet_count} routed subnet requests in one autonomous system, "
            "below the 50-subnet design threshold. A single OSPF Area 0 keeps the link-state "
            "topology simple and provides dynamic route recalculation after a topology change."
        )
    else:
        internal = "Multi-Area OSPF"
        external = None
        reason = (
            f"The profile has {subnet_count} subnet requests, at or above the 50-subnet "
            "threshold. Keep Area 0 as the backbone and introduce areas at deliberate "
            "boundaries to contain link-state scope and support summarization."
        )
    return {
        "internal_protocol": internal,
        "external_protocol": external,
        "subnet_count": subnet_count,
        "route_summary": profile.route_summary or profile.root_cidr,
        "justification": reason,
    }

