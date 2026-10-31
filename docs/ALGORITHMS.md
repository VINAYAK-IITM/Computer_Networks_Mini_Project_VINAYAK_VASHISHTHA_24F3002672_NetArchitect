# Algorithms and Decision Rules

## Physical media

For each link:

1. A caller that explicitly requests copper above 100 m receives `PhysicalDistanceViolationError` with an attenuation warning.
2. An automatic run at or below 100 m selects Cat6a copper with 10GBASE-T.
3. Runs above 100 m through 400 m select OM4 multimode and 10GBASE-SR at 850 nm.
4. Longer fiber runs select OS2 single-mode. The report names 10GBASE-LR through 10 km, 10GBASE-ER through 40 km, then a carrier-engineered optical service.
5. A link explicitly requested as `carrier` selects a provider-defined EVPL service and lists the SLA facts that must be confirmed.

For fiber, the displayed estimate is:

```text
estimated_loss_dB = distance_km * assumed_attenuation_dB_per_km
                    + connectors * 0.75 dB
                    + splices * 0.10 dB
                    + 3.0 dB engineering margin
```

The model uses 3.0 dB/km for OM4 and 0.35 dB/km for OS2. These are planning assumptions. Actual transceiver budgets, connector condition, wavelength, dispersion, patching, and safety margin must come from the selected optic and link design.

## IPv4 VLSM

The `hosts` field is the number of endpoint addresses requested. NetArchitect adds one usable address for the default gateway and reserves network and broadcast addresses:

```text
required_total = endpoint_count + 1 gateway + 2 reserved IPv4 addresses
block_size = max(4, next_power_of_two(required_total))
prefix_length = 32 - log2(block_size)
```

Requests are sorted from largest required block to smallest. Each next block is aligned to its own power-of-two boundary. The allocator rejects a block that cannot fit in the root network and checks every result for containment and overlap.

The first usable address is reserved as the gateway. The output includes the network, mask, usable range, broadcast, capacity, allocated count, and utilization. Cisco wildcard masks are the bitwise inverse of the subnet mask.

### Example

For 63 endpoint hosts, one gateway requires 64 usable addresses. A `/26` has 64 total addresses but only 62 usable, so it is too small. A `/25` has 126 usable addresses and fits. This boundary is covered in the audit record and unit tests.

## Routing selection

- One site, no cloud boundary, and fewer than 50 allocated subnet requests: single-area OSPF Area 0.
- Multiple sites: multi-area OSPF with Area 0 as backbone and site areas only where prefixes and boundaries are deliberately planned.
- A cloud/provider AS boundary: multi-area OSPF internally and eBGP at the external boundary.
- A single site with 50 or more subnet requests: multi-area OSPF to contain link-state scope.

The threshold is a design rule for this assignment, not a protocol maximum. The report explains route summarization only when an aggregate is reserved. BGP aggregation also requires more-specific route availability and a deliberate discard route to prevent loops or hidden route gaps.

## ACL packet-flow evaluator

For a Cisco wildcard, each zero bit must match and each one bit is ignored:

```text
(packet_address AND bitwise_not(wildcard))
    == (acl_network AND bitwise_not(wildcard))
```

The evaluator models an inbound source-SVI ACL that first denies one destination segment and then permits other destinations from that source segment. Packets outside the source segment receive the implicit terminal deny for this ACL. The evaluator does not model route lookup, NAT, stateful firewall behavior, or another ACL later in the path.

