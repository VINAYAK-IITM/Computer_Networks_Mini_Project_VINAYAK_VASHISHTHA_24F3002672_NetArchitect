import unittest

from netarchitect.errors import AddressSpaceExhaustedError
from netarchitect.models import Profile, SubnetSpec
from netarchitect.vlsm import allocate_vlsm


def profile(root, subnets):
    return Profile(
        profile_id="test", name="Test", description="test", root_cidr=root,
        endpoint_count=sum(item.hosts for item in subnets), site_count=1,
        cloud_boundary=False, target_latency_ms=None, links=(), subnets=tuple(subnets), acls=(),
    )


class VlsmTests(unittest.TestCase):
    def test_63_endpoints_include_gateway_and_need_at_least_65_total_addresses(self):
        result = allocate_vlsm(profile("192.0.2.0/24", [SubnetSpec("plant", 63, "Hosts")]))[0]
        self.assertEqual(result["cidr"], "192.0.2.0/25")
        self.assertEqual(result["usable_capacity"], 126)
        self.assertEqual(result["allocated_usable"], 64)

    def test_largest_subnet_allocated_first_without_overlap(self):
        result = allocate_vlsm(profile("10.0.0.0/24", [
            SubnetSpec("small", 10, "Small"), SubnetSpec("large", 100, "Large")
        ]))
        by_name = {item["name"]: item for item in result}
        self.assertEqual(by_name["large"]["network"], "10.0.0.0")
        self.assertNotEqual(by_name["small"]["network"], by_name["large"]["network"])

    def test_wildcard_is_inverse_of_subnet_mask(self):
        result = allocate_vlsm(profile("10.0.0.0/24", [SubnetSpec("users", 50, "Users")]))[0]
        self.assertEqual(result["subnet_mask"], "255.255.255.192")
        self.assertEqual(result["wildcard_mask"], "0.0.0.63")

    def test_address_space_exhaustion_is_reported(self):
        with self.assertRaises(AddressSpaceExhaustedError):
            allocate_vlsm(profile("192.0.2.0/29", [SubnetSpec("too_big", 20, "Too big")]))

    def test_generated_subnets_stay_inside_root(self):
        result = allocate_vlsm(profile("10.1.0.0/24", [
            SubnetSpec("a", 40, "A"), SubnetSpec("b", 30, "B")
        ]))
        self.assertTrue(all(item["cidr"].startswith("10.1.0.") for item in result))


if __name__ == "__main__":
    unittest.main()

