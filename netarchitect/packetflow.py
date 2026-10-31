"""Small deterministic ACL packet-flow evaluator used for audit walkthroughs."""

import ipaddress


def wildcard_match(address: str, network_address: str, wildcard: str) -> bool:
    """Evaluate a Cisco IPv4 wildcard match (zero bits must match)."""
    ip_value = int(ipaddress.IPv4Address(address))
    base_value = int(ipaddress.IPv4Address(network_address))
    wildcard_value = int(ipaddress.IPv4Address(wildcard))
    mask_value = (~wildcard_value) & 0xFFFFFFFF
    return (ip_value & mask_value) == (base_value & mask_value)


def simulate_deny_rule(plan: dict, rule: dict, source_ip: str, destination_ip: str) -> dict:
    """Walk an inbound source-SVI ACL with one deny and a following permit."""
    source = next(item for item in plan["address_plan"] if item["name"] == rule["source"])
    destination = next(
        item for item in plan["address_plan"] if item["name"] == rule["destination"]
    )
    source_match = wildcard_match(
        source_ip, source["network"], source["wildcard_mask"]
    )
    if not source_match:
        decision = "implicit deny (packet does not match this source-specific ACL)"
        matched_line = "implicit terminal deny"
    elif wildcard_match(
        destination_ip, destination["network"], destination["wildcard_mask"]
    ):
        decision = "deny"
        matched_line = (
            f"deny ip {source['network']} {source['wildcard_mask']} "
            f"{destination['network']} {destination['wildcard_mask']}"
        )
    else:
        decision = "permit"
        matched_line = f"permit ip {source['network']} {source['wildcard_mask']} any"
    return {
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "acl": rule["name"],
        "source_match": source_match,
        "decision": decision,
        "matched_line": matched_line,
        "note": "ACL is evaluated inbound on the source SVI; routing and the destination policy are separate checks.",
    }

