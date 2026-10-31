# Assumptions, Safety, and Limits

## Addressing and topology assumptions

- IPv4 only. The first usable address in each subnet is the gateway.
- A subnet's requested host count describes endpoints and excludes the gateway.
- Routed handoff requests use one endpoint address plus the reserved gateway address; the resulting minimum IPv4 point-to-point block is a `/30`.
- All requested subnets are allocated within one profile root prefix. Profiles that need site-specific pools should reserve aligned per-site aggregates before deployment.
- `switch_port_density` estimates a rough access-switch count from the stated endpoint total. It is not a floorplan, PoE budget, AP capacity, or port-reservation calculation.
- The generated core switch and edge router are logical examples, not a full device inventory. Physical ports, transit peers, per-site router ownership, and switch model must be confirmed.

## Media assumptions

- The 100 m Cat6a copper threshold is a channel limit; confirm patch cords, horizontal cable, PoE loading, bundle temperature, and category rating.
- OM4 10GBASE-SR is modeled to 400 m. OS2 LR and ER nominal reach labels are not a guarantee that a specific installed optical channel passes.
- Fiber-loss estimates use generic attenuation, connector, splice, and margin assumptions. They do not replace the module transmit/receive budget, dispersion limits, optical power measurements, or an engineered link budget.
- Carrier EVPL output is a service recommendation. The carrier must confirm committed information rate, QoS mapping, MTU, latency, jitter, protection, and diverse physical paths.

## Routing and security assumptions

- OSPF thresholds and areas are educational planning rules. Production area assignment requires contiguous prefixes and deliberate ABR placement.
- BGP ASNs in the sample are private documentation values. Validate ASN ownership, filters, maximum-prefix policy, authentication, and accepted/advertised routes.
- A route summary can attract traffic for unused addresses. Use it only when the aggregate is reserved, more-specific routes are present, and a deliberate discard route is installed.
- ACL examples demonstrate one-way source isolation only. They do not constitute a complete security policy or firewall configuration.
- VPN peer and key values are placeholders. Use organization-approved algorithms, key management, identity matching, NAT traversal, and vendor-supported syntax.

## Performance and vendor limitations

- A sub-5 ms target cannot be promised from distance alone. Processing, queueing, provider path, congestion, and failover influence latency. Obtain an SLA and measure the complete path under load.
- Cisco IOS and IOS XE syntax varies by release and hardware. Validate every command in the appropriate configuration guide or a supported lab before use.
- NetArchitect does not connect to live devices, emulate packet forwarding, capture packets, guarantee availability, or deploy configuration.

