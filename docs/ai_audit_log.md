# AI Code Audit Log

This audit records two flawed recommendations that arose as AI-generated draft candidates while constructing this project. They were rejected before release. The examples are reproducible reasoning cases for this repository; they are not presented as a vendor-lab capture, production incident, or Packet Tracer result.

## Case 1: VLSM sizing omitted gateway and reserved addresses

**Initial AI-generated draft idea:**

```python
prefix = 32 - ceil(log2(requested_hosts))
```

**Why it is wrong:** `requested_hosts` counts endpoints. The equation above omits the default gateway and IPv4 network/broadcast reservations. For 63 endpoints it chooses `/26` (64 total, 62 usable), but the design needs 64 usable addresses: 63 endpoints plus one gateway. The block must be `/25` (128 total, 126 usable).

**Packet-flow walkthrough:** With `192.0.2.0/26`, addresses `.1` through `.62` are the only usable addresses. `.63` is broadcast and `.64` belongs to the next block. After reserving `.1` as the gateway, only 61 endpoint addresses remain. The 62nd endpoint cannot use `.63`; the 63rd cannot use `.64` while remaining in the `/26`. A host using `.64` would be outside the planned subnet and would not ARP for the `.1` gateway as an on-link neighbor, so the 63-host segment cannot be provisioned as designed.

**Correction:** `vlsm.py` sizes for `endpoint_count + gateway + network + broadcast`, rounds up to a power of two, and selects `/25` for this request. The unit suite includes this exact boundary and root-pool exhaustion.

## Case 2: Subnet mask used as an IOS wildcard mask

**Initial AI-generated draft idea:**

```text
permit ip 10.10.6.0 255.255.255.0 any
```

**Why it is wrong:** Cisco ACL wildcards use zero bits for positions that must match and one bits for positions to ignore. For the checked-in guest segment `10.10.6.0/24`, the correct wildcard is `0.0.0.255`, not the subnet mask `255.255.255.0`. The flawed line fixes the wrong bits and does not match the intended guest source range.

**Packet-flow walkthrough:** On the checked-in campus plan, `10.10.6.10 -> 10.10.7.65` matches the corrected guest source wildcard and the management destination wildcard, so the inbound guest SVI ACL denies it. `10.10.6.10 -> 8.8.8.8` matches the corrected source rule but not the management destination; the following source-specific permit accepts it at this ACL. With the flawed wildcard, the guest source packet fails to match the intended permit and reaches the ACL's implicit terminal deny. These decisions are reproducible with:

```powershell
python -m netarchitect flow campus --acl GUEST-TO-MANAGEMENT --source 10.10.6.10 --destination 10.10.7.65
python -m netarchitect flow campus --acl GUEST-TO-MANAGEMENT --source 10.10.6.10 --destination 8.8.8.8
```

**Correction:** `vlsm.py` derives the wildcard from `IPv4Network.hostmask`; the configuration renderer consumes that same field. `packetflow.py` evaluates wildcard matching bitwise so the examples and tests can check the rule semantics.

## Review and validation boundary

The flow walkthrough validates only the shown subnet and one ACL decision. It does not validate a full route lookup, NAT, firewall state, tunnel negotiation, actual device parser, or end-to-end packet capture. The AI draft is a starting point for student defense; inspect the code, repeat the arithmetic, and adapt the review to the actual topology.

