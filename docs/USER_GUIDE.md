# User Guide

## Commands

Run commands from the repository root with Python 3.10+.

| Command | Purpose |
|---|---|
| `python -m netarchitect list-profiles` | List all built-in scenarios |
| `python -m netarchitect show-profile campus` | Show a preset summary |
| `python -m netarchitect generate campus --out output/campus` | Generate all preset artifacts |
| `python -m netarchitect generate-custom path\to\profile.json --out output\custom` | Generate from custom JSON |
| `python -m netarchitect flow campus --acl GUEST-TO-MANAGEMENT --source 10.10.6.10 --destination 10.10.7.65` | Walk one ACL decision |

Available preset IDs are `campus`, `metro`, and `global`.

## Generated files

- `report.md`: decision summary, explanations, media table, VLSM table, and deployment review points
- `address_plan.csv`: spreadsheet-friendly allocation table
- `network_plan.json`: complete input/result record for automation or review
- `core_switch.cfg`: Layer 3 switch draft with VLANs, SVIs, sample trunk, OSPF, and ACLs
- `edge_router.cfg`: routed handoffs, OSPF, and optional BGP/IPsec templates

## Custom profile fields

Begin with [custom-profile.json](../examples/custom-profile.json). Required fields are `profile_id`, `name`, `description`, `root_cidr`, `endpoint_count`, and `subnets`.

`switch_port_density` sets the assumed endpoint count per access switch (default 48) and produces a rough switch-count estimate. `resiliency` accepts `standard`, `redundant`, or `dual_homed`; the latter two require at least two routed handoffs.

Each subnet requires `name` and `hosts`. `hosts` counts endpoint addresses and the allocator separately reserves one gateway. Add `vlan_id` for a LAN segment. Omit it for a routed handoff; set `interface` to the intended router interface. `area_id` defaults to 0.

Each link requires `name` and `distance_m`. `requested_medium` may be `auto`, `copper`, `fiber`, or `carrier`; it defaults to `auto`. Fiber-specific inputs can override the connector count, splice count, and assumed transceiver budget.

An ACL item names an existing source and destination subnet. The current version generates a deny for the destination followed by a permit for other destinations from that source. Input actions other than `deny` are rejected so a profile cannot silently imply unsupported policy.

Cloud profiles set `cloud_boundary`, `bgp_asn`, `bgp_peer_asn`, and `bgp_peer_link`. VPN templates require `vpn_peer_ip` and `vpn_remote_cidr`. Example peer values are documentation placeholders and must be replaced.

## Reading a VLSM plan

`requested_endpoints` excludes the gateway. `allocated_usable` includes the requested endpoints and the gateway. `utilization_percent` is the fraction of usable addresses assigned to endpoints plus gateway. Network and broadcast addresses are never counted as usable.

## Errors

Fix the input identified in the error and rerun generation. A copper-distance exception should be resolved by changing to fiber/carrier or correcting the physical distance. Address-space exhaustion needs a larger root prefix or smaller host counts. Use strict, aligned IPv4 CIDRs such as `10.42.0.0/20`.

## Verification

Run the included unit suite with `python -m unittest discover -s tests -v`. The examples are generated artifacts, not a substitute for reviewing each device's supported syntax and intended topology.

