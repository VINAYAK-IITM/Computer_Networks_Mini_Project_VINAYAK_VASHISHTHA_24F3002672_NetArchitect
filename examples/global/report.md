# Network Design Report: Profile 3: Global WAN

Four-city and cloud design for 2,000 IoT/scanner endpoints using site segmentation, IPsec, multi-area OSPF, eBGP, and a reserved route aggregate.

## Design summary

- Planned endpoints: **2,000**
- Access switch density target: **48 endpoints per switch** (about 42 switches for the stated endpoint count)
- Address pool: **10.30.0.0/16**
- Sites: **5**
- Resiliency target: **redundant**
- Cloud boundary: **Yes**
- Latency target: **Not specified**
- Routing: **Multi-Area OSPF** + **eBGP at the cloud/provider boundary**

## Physical media decisions

| Link | Distance | Recommendation | Standard / service |
|---|---:|---|---|
| City 1 to City 2 carrier WAN | 2,200.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |
| City 2 to City 3 carrier WAN | 3,100.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |
| City 3 to City 4 carrier WAN | 1,800.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |
| Cloud IPsec underlay | 25.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |
| City data-center fiber handoff | 8.0 km | OS2 single-mode fiber | 10GBASE-LR, 1310 nm, nominal reach up to 10 km |

### Why these choices

- **City 1 to City 2 carrier WAN:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.
- **City 2 to City 3 carrier WAN:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.
- **City 3 to City 4 carrier WAN:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.
- **Cloud IPsec underlay:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.
- **City data-center fiber handoff:** OS2 with LR optics is appropriate for this long-reach single-mode link. Estimated loss is 7.30 dB using 0.35 dB/km, 2 connectors at 0.75 dB each, 0 splices at 0.10 dB each, and a 3 dB engineering margin; assumed budget is 23.00 dB (within the stated generic budget estimate). This estimate is not a substitute for the selected optic's datasheet and an end-to-end power/dispersion check.

## Routing decision

The design spans 5 sites and crosses a cloud/provider autonomous-system boundary. Use OSPF internally for site reachability and eBGP at the external boundary for policy-controlled route exchange. Summarize only the reserved enterprise aggregate 10.30.0.0/16 after installing an appropriate discard route and proving the aggregate does not hide gaps.

## VLSM address plan

Requested endpoint counts exclude the gateway. The allocator adds one gateway address, then reserves the IPv4 network and broadcast addresses.

| Segment | VLAN | Endpoints | CIDR | Gateway | Usable range | Broadcast | Wildcard | Utilization |
|---|---:|---:|---|---|---|---|---|---:|
| city1_iot | 110 | 600 | 10.30.0.0/22 | 10.30.0.1 | 10.30.0.1 - 10.30.3.254 | 10.30.3.255 | 0.0.3.255 | 58.81% |
| city2_iot | 120 | 500 | 10.30.4.0/23 | 10.30.4.1 | 10.30.4.1 - 10.30.5.254 | 10.30.5.255 | 0.0.1.255 | 98.24% |
| city3_scanners | 130 | 400 | 10.30.6.0/23 | 10.30.6.1 | 10.30.6.1 - 10.30.7.254 | 10.30.7.255 | 0.0.1.255 | 78.63% |
| city4_scanners | 140 | 500 | 10.30.8.0/23 | 10.30.8.1 | 10.30.8.1 - 10.30.9.254 | 10.30.9.255 | 0.0.1.255 | 98.24% |
| city1_users | 111 | 180 | 10.30.10.0/24 | 10.30.10.1 | 10.30.10.1 - 10.30.10.254 | 10.30.10.255 | 0.0.0.255 | 71.26% |
| city2_users | 121 | 140 | 10.30.11.0/24 | 10.30.11.1 | 10.30.11.1 - 10.30.11.254 | 10.30.11.255 | 0.0.0.255 | 55.51% |
| city4_users | 141 | 160 | 10.30.12.0/24 | 10.30.12.1 | 10.30.12.1 - 10.30.12.254 | 10.30.12.255 | 0.0.0.255 | 63.39% |
| cloud_apps | 250 | 250 | 10.30.13.0/24 | 10.30.13.1 | 10.30.13.1 - 10.30.13.254 | 10.30.13.255 | 0.0.0.255 | 98.82% |
| city3_users | 131 | 120 | 10.30.14.0/25 | 10.30.14.1 | 10.30.14.1 - 10.30.14.126 | 10.30.14.127 | 0.0.0.127 | 96.03% |
| management | 299 | 100 | 10.30.14.128/25 | 10.30.14.129 | 10.30.14.129 - 10.30.14.254 | 10.30.14.255 | 0.0.0.127 | 80.16% |
| guest | 290 | 120 | 10.30.15.0/25 | 10.30.15.1 | 10.30.15.1 - 10.30.15.126 | 10.30.15.127 | 0.0.0.127 | 96.03% |
| core_edge | - | 1 | 10.30.15.128/30 | 10.30.15.129 | 10.30.15.129 - 10.30.15.130 | 10.30.15.131 | 0.0.0.3 | 100.00% |
| city2_transit | - | 1 | 10.30.15.132/30 | 10.30.15.133 | 10.30.15.133 - 10.30.15.134 | 10.30.15.135 | 0.0.0.3 | 100.00% |
| city3_transit | - | 1 | 10.30.15.136/30 | 10.30.15.137 | 10.30.15.137 - 10.30.15.138 | 10.30.15.139 | 0.0.0.3 | 100.00% |
| city4_transit | - | 1 | 10.30.15.140/30 | 10.30.15.141 | 10.30.15.141 - 10.30.15.142 | 10.30.15.143 | 0.0.0.3 | 100.00% |
| cloud_transit | - | 1 | 10.30.15.144/30 | 10.30.15.145 | 10.30.15.145 - 10.30.15.146 | 10.30.15.147 | 0.0.0.3 | 100.00% |

## Generated device drafts

- `core_switch.cfg`: VLANs, first-usable SVI gateways, rapid-PVST, sample 802.1Q trunk, routed transit, OSPF, and the declared source-isolation ACLs.
- `edge_router.cfg`: routed handoffs, OSPF, and, where applicable, BGP and an IPsec template.

## Deployment review points

- Match interface names, VLAN IDs, OSPF areas, MTU, speed/duplex, and transceiver type to the actual device inventory.
- Verify the selected fiber path using optic datasheets, patch-panel/splice counts, polarity, receive power, and dispersion limits.
- A target below 5 ms is a design objective, not a carrier guarantee. Obtain and measure the end-to-end SLA, jitter, and failover behavior.
- Replace all VPN peer and key placeholders. Review the ACL and BGP policy before applying the draft.
- For BGP aggregation, reserve the aggregate and ensure more-specific routes and a deliberate discard route prevent traffic black holes.
