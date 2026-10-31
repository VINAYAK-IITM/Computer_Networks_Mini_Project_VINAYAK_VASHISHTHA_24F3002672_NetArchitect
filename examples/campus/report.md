# Network Design Report: Profile 1: Campus LAN

Three-building campus with 1,600 planned endpoints, PoE access, VLAN segmentation, rapid spanning tree, and a single OSPF domain.

## Design summary

- Planned endpoints: **1,600**
- Access switch density target: **48 endpoints per switch** (about 34 switches for the stated endpoint count)
- Address pool: **10.10.0.0/20**
- Sites: **1**
- Resiliency target: **standard**
- Cloud boundary: **No**
- Latency target: **Not specified**
- Routing: **Single-Area OSPF, Area 0**

## Physical media decisions

| Link | Distance | Recommendation | Standard / service |
|---|---:|---|---|
| Building 1 access run | 85 m | Cat6a balanced copper | 10GBASE-T (IEEE 802.3an), channel up to 100 m |
| Building 1 to Building 2 backbone | 260 m | OM4 multimode fiber | 10GBASE-SR, 850 nm, up to 400 m on OM4 |
| Building 2 to Building 3 backbone | 360 m | OM4 multimode fiber | 10GBASE-SR, 850 nm, up to 400 m on OM4 |

### Why these choices

- **Building 1 access run:** The run is within the 100 m Ethernet channel limit. Cat6a supports 10GBASE-T over a compliant channel; verify alien crosstalk, cable bundle temperature, and the switch's PoE power budget for attached devices.
- **Building 1 to Building 2 backbone:** OM4 provides the modal bandwidth and reach for 10GBASE-SR at 850 nm over this campus backbone distance. Keep the optical channel within the transceiver's published reach and dispersion specification. Estimated loss is 5.28 dB using 3 dB/km, 2 connectors at 0.75 dB each, 0 splices at 0.10 dB each, and a 3 dB engineering margin; assumed budget is 23.00 dB (within the stated generic budget estimate). This estimate is not a substitute for the selected optic's datasheet and an end-to-end power/dispersion check.
- **Building 2 to Building 3 backbone:** OM4 provides the modal bandwidth and reach for 10GBASE-SR at 850 nm over this campus backbone distance. Keep the optical channel within the transceiver's published reach and dispersion specification. Estimated loss is 5.58 dB using 3 dB/km, 2 connectors at 0.75 dB each, 0 splices at 0.10 dB each, and a 3 dB engineering margin; assumed budget is 23.00 dB (within the stated generic budget estimate). This estimate is not a substitute for the selected optic's datasheet and an end-to-end power/dispersion check.

## Routing decision

The profile has 8 routed subnet requests in one autonomous system, below the 50-subnet design threshold. A single OSPF Area 0 keeps the link-state topology simple and provides dynamic route recalculation after a topology change.

## VLSM address plan

Requested endpoint counts exclude the gateway. The allocator adds one gateway address, then reserves the IPv4 network and broadcast addresses.

| Segment | VLAN | Endpoints | CIDR | Gateway | Usable range | Broadcast | Wildcard | Utilization |
|---|---:|---:|---|---|---|---|---|---:|
| staff | 10 | 500 | 10.10.0.0/23 | 10.10.0.1 | 10.10.0.1 - 10.10.1.254 | 10.10.1.255 | 0.0.1.255 | 98.24% |
| students | 20 | 400 | 10.10.2.0/23 | 10.10.2.1 | 10.10.2.1 - 10.10.3.254 | 10.10.3.255 | 0.0.1.255 | 78.63% |
| voice | 30 | 200 | 10.10.4.0/24 | 10.10.4.1 | 10.10.4.1 - 10.10.4.254 | 10.10.4.255 | 0.0.0.255 | 79.13% |
| iot | 50 | 150 | 10.10.5.0/24 | 10.10.5.1 | 10.10.5.1 - 10.10.5.254 | 10.10.5.255 | 0.0.0.255 | 59.45% |
| guest | 90 | 250 | 10.10.6.0/24 | 10.10.6.1 | 10.10.6.1 - 10.10.6.254 | 10.10.6.255 | 0.0.0.255 | 98.82% |
| access_points | 40 | 50 | 10.10.7.0/26 | 10.10.7.1 | 10.10.7.1 - 10.10.7.62 | 10.10.7.63 | 0.0.0.63 | 82.26% |
| management | 99 | 50 | 10.10.7.64/26 | 10.10.7.65 | 10.10.7.65 - 10.10.7.126 | 10.10.7.127 | 0.0.0.63 | 82.26% |
| core_edge | - | 1 | 10.10.7.128/30 | 10.10.7.129 | 10.10.7.129 - 10.10.7.130 | 10.10.7.131 | 0.0.0.3 | 100.00% |

## Generated device drafts

- `core_switch.cfg`: VLANs, first-usable SVI gateways, rapid-PVST, sample 802.1Q trunk, routed transit, OSPF, and the declared source-isolation ACLs.
- `edge_router.cfg`: routed handoffs, OSPF, and, where applicable, BGP and an IPsec template.

## Deployment review points

- Match interface names, VLAN IDs, OSPF areas, MTU, speed/duplex, and transceiver type to the actual device inventory.
- Verify the selected fiber path using optic datasheets, patch-panel/splice counts, polarity, receive power, and dispersion limits.
- A target below 5 ms is a design objective, not a carrier guarantee. Obtain and measure the end-to-end SLA, jitter, and failover behavior.
- Replace all VPN peer and key placeholders. Review the ACL and BGP policy before applying the draft.
- For BGP aggregation, reserve the aggregate and ensure more-specific routes and a deliberate discard route prevent traffic black holes.
