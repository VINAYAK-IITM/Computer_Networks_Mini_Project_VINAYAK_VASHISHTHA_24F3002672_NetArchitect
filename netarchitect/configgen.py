"""Render reviewable Cisco IOS configuration drafts from one computed plan."""

import ipaddress
import re


def _slug(value: str, max_length: int = 24) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", value).strip("_")
    return cleaned[:max_length].upper() or "NETARCHITECT"


def _by_name(plan: dict) -> dict[str, dict]:
    return {item["name"]: item for item in plan["address_plan"]}


def _network_statement(item: dict) -> str:
    return (
        f" network {item['network']} {item['wildcard_mask']} "
        f"area {item['area_id']}"
    )


def render_core_switch(plan: dict) -> str:
    profile = plan["profile"]
    records = _by_name(plan)
    vlans = [item for item in plan["address_plan"] if item["vlan_id"] is not None]
    lines = [
        "! NetArchitect educational draft. Review platform syntax and topology before deployment.",
        f"! Profile: {profile['name']}",
        "! Assumption: this is a Layer 3 campus/distribution switch with SVI routing enabled.",
        f"hostname {_slug(profile['profile_id'] + '_CORE')}",
        "no ip domain-lookup",
        "vtp mode transparent",
        "spanning-tree mode rapid-pvst",
        "ip routing",
        "! VLAN definitions and gateway SVIs",
    ]
    for item in vlans:
        vlan_id = item["vlan_id"]
        label = _slug(item["name"])
        lines.extend(
            [
                f"vlan {vlan_id}",
                f" name {label}",
                "!",
                f"interface Vlan{vlan_id}",
                f" description {item['purpose']}",
                f" ip address {item['gateway']} {item['subnet_mask']}",
                " no shutdown",
                "!",
            ]
        )

    for rule in plan["profile"].get("acls", []):
        source = records[rule["source"]]
        destination = records[rule["destination"]]
        acl_name = _slug(rule["name"])
        lines.extend(
            [
                f"ip access-list extended {acl_name}",
                f" remark Isolate {source['name']} from {destination['name']}",
                f" deny ip {source['network']} {source['wildcard_mask']} {destination['network']} {destination['wildcard_mask']}",
                f" permit ip {source['network']} {source['wildcard_mask']} any",
                "!",
                f"interface Vlan{source['vlan_id']}",
                f" ip access-group {acl_name} in",
                "!",
            ]
        )

    core_transit = records.get("core_edge")
    if core_transit:
        core_ip = str(ipaddress.IPv4Address(core_transit["last_usable"]))
        lines.extend(
            [
                "! Routed connection to the edge router; peer is the allocated gateway address.",
                "interface GigabitEthernet1/0/47",
                " description Routed transit to edge router - adapt physical port",
                " no switchport",
                f" ip address {core_ip} {core_transit['subnet_mask']}",
                " no shutdown",
                "!",
                "! Example 802.1Q uplink to the access layer; adjust port and allowed VLANs.",
                "interface GigabitEthernet1/0/48",
                " description 802.1Q trunk to access layer - adapt physical port",
                " switchport mode trunk",
                " switchport trunk allowed vlan " + ",".join(str(item["vlan_id"]) for item in vlans),
                " no shutdown",
                "!",
            ]
        )

    router_id = profile.get("router_id", "10.255.255.1")
    router_octets = router_id.split(".")
    router_octets[-1] = str(2 if router_octets[-1] == "1" else 1)
    switch_router_id = ".".join(router_octets)
    lines.extend(
        [
            "! OSPF control plane for directly attached SVIs and routed transit.",
            "router ospf 10",
            f" router-id {switch_router_id}",
            " passive-interface default",
        ]
    )
    if core_transit:
        lines.append(" no passive-interface GigabitEthernet1/0/47")
    for item in plan["address_plan"]:
        if item["vlan_id"] is not None or item["name"] == "core_edge":
            lines.append(_network_statement(item))
    lines.extend(["!", "end", ""])
    return "\n".join(lines)


def render_edge_router(plan: dict) -> str:
    profile = plan["profile"]
    records = _by_name(plan)
    lines = [
        "! NetArchitect educational draft. Replace placeholders and review platform syntax.",
        f"! Profile: {profile['name']}",
        "! Assumption: one logical edge router terminates the listed routed handoffs.",
        f"hostname {_slug(profile['profile_id'] + '_EDGE')}",
        "no ip domain-lookup",
        "! Routed WAN interfaces; the peer uses the last usable IPv4 address in each /30.",
    ]
    transit_items = [item for item in plan["address_plan"] if item["interface"]]
    for item in transit_items:
        lines.extend(
            [
                f"interface {item['interface']}",
                f" description {item['purpose']} - confirm handoff and peer address",
                f" ip address {item['gateway']} {item['subnet_mask']}",
                *([f" ip ospf cost {item['ospf_cost']}"] if item.get("ospf_cost") else []),
                " no shutdown",
                "!",
            ]
        )
    lines.extend(
        [
            "! OSPF statements below are templates. Keep each network statement only on the router that owns it.",
            "router ospf 10",
            f" router-id {profile.get('router_id', '10.255.255.1')}",
            " passive-interface default",
        ]
    )
    for item in plan["address_plan"]:
        if item["interface"]:
            lines.append(f" no passive-interface {item['interface']}")
    for item in plan["address_plan"]:
        lines.append(_network_statement(item))
    lines.append("!")

    if profile.get("target_latency_ms") is not None:
        lines.extend(
            [
                "! QoS example: trust/remark traffic at the access boundary and align classes with the carrier.",
                "! Priority queuing improves local treatment; it cannot guarantee the end-to-end latency target.",
                "class-map match-any REALTIME-VOICE",
                " match dscp ef",
                "class-map match-any BUSINESS-CRITICAL",
                " match dscp af31",
                "policy-map WAN-QOS",
                " class REALTIME-VOICE",
                "  priority percent 20",
                " class BUSINESS-CRITICAL",
                "  bandwidth percent 30",
                " class class-default",
                "  fair-queue",
            ]
        )
        for item in transit_items:
            if item["name"] != "core_edge":
                lines.extend([f"interface {item['interface']}", " service-policy output WAN-QOS", "!"])

    if profile.get("bgp_asn") and profile.get("bgp_peer_link"):
        peer_link = records[profile["bgp_peer_link"]]
        peer_ip = peer_link["last_usable"]
        aggregate = ipaddress.ip_network(profile.get("route_summary") or profile["root_cidr"])
        remote_prefix = profile.get("vpn_remote_cidr")
        lines.extend(
            [
                "! BGP summary is safe only if the aggregate is reserved and more-specific routes exist.",
                f"ip route {aggregate.network_address} {aggregate.netmask} Null0 250",
            ]
        )
        if remote_prefix:
            remote = ipaddress.ip_network(remote_prefix)
            lines.extend(
                [
                    "! Limit BGP-to-OSPF redistribution to the declared remote VPN prefix.",
                    f"ip prefix-list CLOUD-REMOTE seq 5 permit {remote}",
                    "route-map BGP-TO-OSPF permit 10",
                    " match ip address prefix-list CLOUD-REMOTE",
                    "!",
                    "router ospf 10",
                    f" redistribute bgp {profile['bgp_asn']} subnets route-map BGP-TO-OSPF",
                    "!",
                ]
            )
        lines.extend(
            [
                f"router bgp {profile['bgp_asn']}",
                f" neighbor {peer_ip} remote-as {profile['bgp_peer_asn']}",
                f" neighbor {peer_ip} description Cloud/provider boundary - confirm peer details",
                " address-family ipv4 unicast",
                f"  neighbor {peer_ip} activate",
                f"  network {aggregate.network_address} mask {aggregate.netmask}",
                " exit-address-family",
                "!",
            ]
        )

    if profile.get("vpn_peer_ip") and profile.get("vpn_remote_cidr"):
        local = ipaddress.ip_network(profile["root_cidr"])
        remote = ipaddress.ip_network(profile["vpn_remote_cidr"])
        vpn_interface = profile.get("vpn_interface") or (
            records[profile["bgp_peer_link"]]["interface"]
            if profile.get("bgp_peer_link")
            else None
        )
        lines.extend(
            [
                "! IPsec template: peer uses RFC 5737 documentation address; replace with the real endpoint.",
                "! Confirm NAT traversal, current crypto policy, peer identity, and platform support.",
                "ip access-list extended VPN-INTERESTING-TRAFFIC",
                f" permit ip {local.network_address} {local.hostmask} {remote.network_address} {remote.hostmask}",
                "!",
                "crypto ikev2 proposal NETARCHITECT-IKEV2",
                " encryption aes-cbc-256",
                " integrity sha256",
                " group 14",
                "crypto ikev2 policy 10",
                " proposal NETARCHITECT-IKEV2",
                "crypto ikev2 keyring NETARCHITECT-KEYRING",
                " peer CLOUD-PEER",
                f"  address {profile['vpn_peer_ip']}",
                "  pre-shared-key local <REPLACE_WITH_SECRET>",
                "  pre-shared-key remote <REPLACE_WITH_SECRET>",
                "crypto ikev2 profile NETARCHITECT-IKEV2-PROFILE",
                f" match identity remote address {profile['vpn_peer_ip']} 255.255.255.255",
                " authentication remote pre-share",
                " authentication local pre-share",
                " keyring local NETARCHITECT-KEYRING",
                "crypto ipsec transform-set NETARCHITECT-TS esp-aes 256 esp-sha256-hmac",
                " mode tunnel",
                "crypto map NETARCHITECT-VPN 10 ipsec-isakmp",
                f" set peer {profile['vpn_peer_ip']}",
                " set transform-set NETARCHITECT-TS",
                " set ikev2-profile NETARCHITECT-IKEV2-PROFILE",
                " match address VPN-INTERESTING-TRAFFIC",
            ]
        )
        if vpn_interface:
            lines.extend([f"interface {vpn_interface}", " crypto map NETARCHITECT-VPN", "!"])
    lines.extend(["end", ""])
    return "\n".join(lines)


def render_configs(plan: dict) -> dict[str, str]:
    return {
        "core_switch.cfg": render_core_switch(plan),
        "edge_router.cfg": render_edge_router(plan),
    }

