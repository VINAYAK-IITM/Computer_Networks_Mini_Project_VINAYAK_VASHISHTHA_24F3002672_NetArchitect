"""Run the validated recommendation pipeline and write synchronized exports."""

import csv
import json
import math
from dataclasses import asdict
from pathlib import Path

from .configgen import render_configs
from .media import recommend_media
from .models import Profile
from .routing import select_routing
from .validation import validate_profile
from .vlsm import allocate_vlsm


def build_plan(profile: Profile) -> dict:
    validate_profile(profile)
    media = [recommend_media(link).to_dict() for link in profile.links]
    address_plan = allocate_vlsm(profile)
    routing = select_routing(profile, len(address_plan))
    return {
        "schema_version": 1,
        "profile": asdict(profile),
        "media_recommendations": media,
        "address_plan": address_plan,
        "routing": routing,
        "assumptions": [
            "Each subnet host request counts endpoints; one additional usable IPv4 address is reserved for its default gateway.",
            "IPv4 network and broadcast addresses are not assignable to endpoints.",
            "The first usable address in each subnet is the gateway.",
            "Fiber loss is a planning estimate with generic attenuation and connector assumptions, not an optic datasheet calculation.",
            "Generated device configuration is an educational draft that requires platform and topology review.",
        ],
    }


def render_report(plan: dict) -> str:
    profile = plan["profile"]
    lines = [
        f"# Network Design Report: {profile['name']}",
        "",
        profile["description"],
        "",
        "## Design summary",
        "",
        f"- Planned endpoints: **{profile['endpoint_count']:,}**",
        f"- Access switch density target: **{profile['switch_port_density']} endpoints per switch** "
        f"(about {math.ceil(profile['endpoint_count'] / profile['switch_port_density'])} switches for the stated endpoint count)",
        f"- Address pool: **{profile['root_cidr']}**",
        f"- Sites: **{profile['site_count']}**",
        f"- Resiliency target: **{profile['resiliency'].replace('_', ' ')}**",
        f"- Cloud boundary: **{'Yes' if profile['cloud_boundary'] else 'No'}**",
        f"- Latency target: **{str(profile['target_latency_ms']) + ' ms' if profile['target_latency_ms'] else 'Not specified'}**",
        f"- Routing: **{plan['routing']['internal_protocol']}**"
        + (f" + **{plan['routing']['external_protocol']}**" if plan["routing"]["external_protocol"] else ""),
        "",
        "## Physical media decisions",
        "",
        "| Link | Distance | Recommendation | Standard / service |",
        "|---|---:|---|---|",
    ]
    for item in plan["media_recommendations"]:
        distance = (
            f"{item['distance_m'] / 1000:,.1f} km"
            if item["distance_m"] >= 1000
            else f"{item['distance_m']:g} m"
        )
        lines.append(
            f"| {item['link']} | {distance} | {item['medium']} | {item['standard']} |"
        )
    lines.extend(["", "### Why these choices", ""])
    for item in plan["media_recommendations"]:
        lines.extend([f"- **{item['link']}:** {item['justification']}"])
    lines.extend(
        [
            "",
            "## Routing decision",
            "",
            plan["routing"]["justification"],
            "",
            "## VLSM address plan",
            "",
            "Requested endpoint counts exclude the gateway. The allocator adds one gateway address, then reserves the IPv4 network and broadcast addresses.",
            "",
            "| Segment | VLAN | Endpoints | CIDR | Gateway | Usable range | Broadcast | Wildcard | Utilization |",
            "|---|---:|---:|---|---|---|---|---|---:|",
        ]
    )
    for item in plan["address_plan"]:
        vlan = str(item["vlan_id"]) if item["vlan_id"] is not None else "-"
        lines.append(
            f"| {item['name']} | {vlan} | {item['requested_endpoints']} | {item['cidr']} | "
            f"{item['gateway']} | {item['first_usable']} - {item['last_usable']} | "
            f"{item['broadcast']} | {item['wildcard_mask']} | {item['utilization_percent']:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## Generated device drafts",
            "",
            "- `core_switch.cfg`: VLANs, first-usable SVI gateways, rapid-PVST, sample 802.1Q trunk, routed transit, OSPF, and the declared source-isolation ACLs.",
            "- `edge_router.cfg`: routed handoffs, OSPF, and, where applicable, BGP and an IPsec template.",
            "",
            "## Deployment review points",
            "",
            "- Match interface names, VLAN IDs, OSPF areas, MTU, speed/duplex, and transceiver type to the actual device inventory.",
            "- Verify the selected fiber path using optic datasheets, patch-panel/splice counts, polarity, receive power, and dispersion limits.",
            "- A target below 5 ms is a design objective, not a carrier guarantee. Obtain and measure the end-to-end SLA, jitter, and failover behavior.",
            "- Replace all VPN peer and key placeholders. Review the ACL and BGP policy before applying the draft.",
            "- For BGP aggregation, reserve the aggregate and ensure more-specific routes and a deliberate discard route prevent traffic black holes.",
            "",
        ]
    )
    return "\n".join(lines)


def write_exports(plan: dict, destination: str | Path) -> Path:
    out_dir = Path(destination)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(render_report(plan), encoding="utf-8")
    (out_dir / "network_plan.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8"
    )
    fields = [
        "name", "purpose", "vlan_id", "area_id", "requested_endpoints", "cidr",
        "subnet_mask", "wildcard_mask", "gateway", "first_usable", "last_usable",
        "broadcast", "usable_capacity", "allocated_usable", "utilization_percent",
    ]
    with (out_dir / "address_plan.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in plan["address_plan"])
    for filename, contents in render_configs(plan).items():
        (out_dir / filename).write_text(contents, encoding="utf-8")
    return out_dir

