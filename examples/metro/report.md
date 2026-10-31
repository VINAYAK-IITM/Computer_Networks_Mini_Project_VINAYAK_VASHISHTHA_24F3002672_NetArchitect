# Network Design Report: Profile 2: Metro MAN

Headquarters, two remote offices, and a FinTech colocation presence with 450 users, OS2/EVPL transport, QoS targets, and dual-homed failover.

## Design summary

- Planned endpoints: **450**
- Access switch density target: **48 endpoints per switch** (about 10 switches for the stated endpoint count)
- Address pool: **10.20.0.0/20**
- Sites: **4**
- Resiliency target: **dual homed**
- Cloud boundary: **No**
- Latency target: **5.0 ms**
- Routing: **Multi-Area OSPF**

## Physical media decisions

| Link | Distance | Recommendation | Standard / service |
|---|---:|---|---|
| HQ to FinTech colo optical path | 35.0 km | OS2 single-mode fiber | 10GBASE-ER, 1550 nm, nominal reach up to 40 km |
| East office EVPL | 15.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |
| West office primary EVPL | 28.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |
| West office diverse backup EVPL | 32.0 km | Carrier Ethernet / EVPL | Provider-defined UNI and SLA |

### Why these choices

- **HQ to FinTech colo optical path:** OS2 with ER optics covers this metropolitan distance within the nominal reach; verify attenuation, dispersion, and receive power. Estimated loss is 19.05 dB using 0.35 dB/km, 4 connectors at 0.75 dB each, 8 splices at 0.10 dB each, and a 3 dB engineering margin; assumed budget is 23.00 dB (within the stated generic budget estimate). This estimate is not a substitute for the selected optic's datasheet and an end-to-end power/dispersion check.
- **East office EVPL:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.
- **West office primary EVPL:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.
- **West office diverse backup EVPL:** A managed Layer 2 service keeps the physical path and protection inside the carrier domain. Confirm the committed latency, CIR, MTU, QoS marking, and diverse-path SLA with the provider.

## Routing decision

The design joins 4 sites with redundant paths. Use Area 0 as the backbone and place site links in planned non-backbone areas; summarize at ABRs only after contiguous site prefixes are reserved. OSPF cost and carrier SLA design must be checked against the failover and latency targets.

## VLSM address plan

Requested endpoint counts exclude the gateway. The allocator adds one gateway address, then reserves the IPv4 network and broadcast addresses.

| Segment | VLAN | Endpoints | CIDR | Gateway | Usable range | Broadcast | Wildcard | Utilization |
|---|---:|---:|---|---|---|---|---|---:|
| hq_users | 10 | 250 | 10.20.0.0/24 | 10.20.0.1 | 10.20.0.1 - 10.20.0.254 | 10.20.0.255 | 0.0.0.255 | 98.82% |
| east_users | 110 | 100 | 10.20.1.0/25 | 10.20.1.1 | 10.20.1.1 - 10.20.1.126 | 10.20.1.127 | 0.0.0.127 | 80.16% |
| west_users | 210 | 100 | 10.20.1.128/25 | 10.20.1.129 | 10.20.1.129 - 10.20.1.254 | 10.20.1.255 | 0.0.0.127 | 80.16% |
| hq_voice | 30 | 40 | 10.20.2.0/26 | 10.20.2.1 | 10.20.2.1 - 10.20.2.62 | 10.20.2.63 | 0.0.0.63 | 66.13% |
| hq_management | 99 | 32 | 10.20.2.64/26 | 10.20.2.65 | 10.20.2.65 - 10.20.2.126 | 10.20.2.127 | 0.0.0.63 | 53.23% |
| colo_services | 310 | 50 | 10.20.2.128/26 | 10.20.2.129 | 10.20.2.129 - 10.20.2.190 | 10.20.2.191 | 0.0.0.63 | 82.26% |
| east_voice | 130 | 24 | 10.20.2.192/27 | 10.20.2.193 | 10.20.2.193 - 10.20.2.222 | 10.20.2.223 | 0.0.0.31 | 83.33% |
| east_management | 199 | 16 | 10.20.2.224/27 | 10.20.2.225 | 10.20.2.225 - 10.20.2.254 | 10.20.2.255 | 0.0.0.31 | 56.67% |
| west_voice | 230 | 24 | 10.20.3.0/27 | 10.20.3.1 | 10.20.3.1 - 10.20.3.30 | 10.20.3.31 | 0.0.0.31 | 83.33% |
| west_management | 299 | 16 | 10.20.3.32/27 | 10.20.3.33 | 10.20.3.33 - 10.20.3.62 | 10.20.3.63 | 0.0.0.31 | 56.67% |
| core_edge | - | 1 | 10.20.3.64/30 | 10.20.3.65 | 10.20.3.65 - 10.20.3.66 | 10.20.3.67 | 0.0.0.3 | 100.00% |
| east_transit | - | 1 | 10.20.3.68/30 | 10.20.3.69 | 10.20.3.69 - 10.20.3.70 | 10.20.3.71 | 0.0.0.3 | 100.00% |
| west_primary | - | 1 | 10.20.3.72/30 | 10.20.3.73 | 10.20.3.73 - 10.20.3.74 | 10.20.3.75 | 0.0.0.3 | 100.00% |
| west_backup | - | 1 | 10.20.3.76/30 | 10.20.3.77 | 10.20.3.77 - 10.20.3.78 | 10.20.3.79 | 0.0.0.3 | 100.00% |
| colo_transit | - | 1 | 10.20.3.80/30 | 10.20.3.81 | 10.20.3.81 - 10.20.3.82 | 10.20.3.83 | 0.0.0.3 | 100.00% |

## Generated device drafts

- `core_switch.cfg`: VLANs, first-usable SVI gateways, rapid-PVST, sample 802.1Q trunk, routed transit, OSPF, and the declared source-isolation ACLs.
- `edge_router.cfg`: routed handoffs, OSPF, and, where applicable, BGP and an IPsec template.

## Deployment review points

- Match interface names, VLAN IDs, OSPF areas, MTU, speed/duplex, and transceiver type to the actual device inventory.
- Verify the selected fiber path using optic datasheets, patch-panel/splice counts, polarity, receive power, and dispersion limits.
- A target below 5 ms is a design objective, not a carrier guarantee. Obtain and measure the end-to-end SLA, jitter, and failover behavior.
- Replace all VPN peer and key placeholders. Review the ACL and BGP policy before applying the draft.
- For BGP aggregation, reserve the aggregate and ensure more-specific routes and a deliberate discard route prevent traffic black holes.
