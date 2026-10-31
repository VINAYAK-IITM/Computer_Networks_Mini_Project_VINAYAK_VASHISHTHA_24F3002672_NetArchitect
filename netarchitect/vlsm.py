"""IPv4 VLSM allocation with gateway reservation and Cisco wildcard math."""

import ipaddress

from .errors import AddressSpaceExhaustedError
from .models import Profile, SubnetSpec


def _prefix_for_endpoint_count(endpoint_count: int) -> int:
    # Reserve one usable address for the default gateway, in addition to the
    # requested endpoints and IPv4 network/broadcast addresses.
    total_addresses = endpoint_count + 1 + 2
    exponent = max(2, (total_addresses - 1).bit_length())
    return 32 - exponent


def _mask_text(network: ipaddress.IPv4Network) -> str:
    return str(network.netmask)


def _record(spec: SubnetSpec, network: ipaddress.IPv4Network) -> dict:
    first = network.network_address + 1
    last = network.broadcast_address - 1
    capacity = network.num_addresses - 2
    return {
        "name": spec.name,
        "purpose": spec.purpose,
        "vlan_id": spec.vlan_id,
        "area_id": spec.area_id,
        "interface": spec.interface,
        "ospf_cost": spec.ospf_cost,
        "requested_endpoints": spec.hosts,
        "gateway": str(first),
        "network": str(network.network_address),
        "cidr": str(network),
        "subnet_mask": _mask_text(network),
        "wildcard_mask": str(network.hostmask),
        "first_usable": str(first),
        "last_usable": str(last),
        "broadcast": str(network.broadcast_address),
        "usable_capacity": capacity,
        "allocated_usable": spec.hosts + 1,
        "utilization_percent": round((spec.hosts + 1) / capacity * 100, 2),
    }


def allocate_vlsm(profile: Profile) -> list[dict]:
    root = ipaddress.ip_network(profile.root_cidr, strict=True)
    cursor = int(root.network_address)
    end = int(root.broadcast_address) + 1
    ranked = sorted(
        enumerate(profile.subnets),
        key=lambda pair: (-(1 << (32 - _prefix_for_endpoint_count(pair[1].hosts))), pair[0]),
    )
    networks: dict[str, ipaddress.IPv4Network] = {}
    for _, spec in ranked:
        prefix = _prefix_for_endpoint_count(spec.hosts)
        block_size = 1 << (32 - prefix)
        aligned_cursor = ((cursor + block_size - 1) // block_size) * block_size
        next_cursor = aligned_cursor + block_size
        if prefix < root.prefixlen or next_cursor > end:
            raise AddressSpaceExhaustedError(
                f"Subnet '{spec.name}' needs a /{prefix} block, but the requested "
                f"subnets do not fit in {root}. Choose a larger root_cidr or reduce host counts."
            )
        network = ipaddress.ip_network((aligned_cursor, prefix), strict=True)
        networks[spec.name] = network
        cursor = next_cursor

    records = [_record(spec, networks[spec.name]) for spec in profile.subnets]
    records.sort(key=lambda item: int(ipaddress.IPv4Address(item["network"])))
    for index, item in enumerate(records):
        current = ipaddress.ip_network(item["cidr"])
        if not current.subnet_of(root):
            raise AddressSpaceExhaustedError(f"Allocated subnet {current} escaped root {root}.")
        for other_item in records[index + 1 :]:
            if current.overlaps(ipaddress.ip_network(other_item["cidr"])):
                raise AddressSpaceExhaustedError(
                    f"Internal allocation error: {current} overlaps {other_item['cidr']}."
                )
    return records

