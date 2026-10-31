# Network Design Report: Custom Lab Network

Small example profile to edit for a classroom lab.

## Design summary

- Planned endpoints: **40**
- Access switch density target: **24 endpoints per switch** (about 2 switches for the stated endpoint count)
- Address pool: **10.42.0.0/24**
- Sites: **1**
- Resiliency target: **standard**
- Cloud boundary: **No**
- Latency target: **Not specified**
- Routing: **Single-Area OSPF, Area 0**

## Physical media decisions

| Link | Distance | Recommendation | Standard / service |
|---|---:|---|---|
| Access layer uplink | 65 m | Cat6a balanced copper | 10GBASE-T (IEEE 802.3an), channel up to 100 m |

### Why these choices

- **Access layer uplink:** The run is within the 100 m Ethernet channel limit. Cat6a supports 10GBASE-T over a compliant channel; verify alien crosstalk, cable bundle temperature, and the switch's PoE power budget for attached devices.

## Routing decision

The profile has 3 routed subnet requests in one autonomous system, below the 50-subnet design threshold. A single OSPF Area 0 keeps the link-state topology simple and provides dynamic route recalculation after a topology change.

## VLSM address plan

Requested endpoint counts exclude the gateway. The allocator adds one gateway address, then reserves the IPv4 network and broadcast addresses.

| Segment | VLAN | Endpoints | CIDR | Gateway | Usable range | Broadcast | Wildcard | Utilization |
|---|---:|---:|---|---|---|---|---|---:|
| users | 10 | 35 | 10.42.0.0/26 | 10.42.0.1 | 10.42.0.1 - 10.42.0.62 | 10.42.0.63 | 0.0.0.63 | 58.06% |
| management | 99 | 5 | 10.42.0.64/29 | 10.42.0.65 | 10.42.0.65 - 10.42.0.70 | 10.42.0.71 | 0.0.0.7 | 100.00% |
| core_edge | - | 1 | 10.42.0.72/30 | 10.42.0.73 | 10.42.0.73 - 10.42.0.74 | 10.42.0.75 | 0.0.0.3 | 100.00% |

## Generated device drafts

- `core_switch.cfg`: VLANs, first-usable SVI gateways, rapid-PVST, sample 802.1Q trunk, routed transit, OSPF, and the declared source-isolation ACLs.
- `edge_router.cfg`: routed handoffs, OSPF, and, where applicable, BGP and an IPsec template.

## Deployment review points

- Match interface names, VLAN IDs, OSPF areas, MTU, speed/duplex, and transceiver type to the actual device inventory.
- Verify the selected fiber path using optic datasheets, patch-panel/splice counts, polarity, receive power, and dispersion limits.
- A target below 5 ms is a design objective, not a carrier guarantee. Obtain and measure the end-to-end SLA, jitter, and failover behavior.
- Replace all VPN peer and key placeholders. Review the ACL and BGP policy before applying the draft.
- For BGP aggregation, reserve the aggregate and ensure more-specific routes and a deliberate discard route prevent traffic black holes.
