import unittest

from netarchitect.models import Profile
from netarchitect.routing import select_routing


def profile(site_count=1, cloud=False):
    return Profile(
        profile_id="test", name="Test", description="test", root_cidr="10.0.0.0/16",
        endpoint_count=1, site_count=site_count, cloud_boundary=cloud,
        target_latency_ms=None, links=(), subnets=(), acls=(), bgp_asn=65010,
        bgp_peer_asn=65020, bgp_peer_link="cloud",
    )


class RoutingTests(unittest.TestCase):
    def test_single_site_below_threshold_uses_area_zero(self):
        self.assertEqual(select_routing(profile(), 49)["internal_protocol"], "Single-Area OSPF, Area 0")

    def test_single_site_at_threshold_uses_multi_area(self):
        self.assertEqual(select_routing(profile(), 50)["internal_protocol"], "Multi-Area OSPF")

    def test_multiple_sites_use_multi_area(self):
        self.assertEqual(select_routing(profile(site_count=3), 8)["internal_protocol"], "Multi-Area OSPF")

    def test_cloud_boundary_adds_ebgp(self):
        result = select_routing(profile(site_count=5, cloud=True), 20)
        self.assertEqual(result["external_protocol"], "eBGP at the cloud/provider boundary")
        self.assertIn("discard route", result["justification"])


if __name__ == "__main__":
    unittest.main()

