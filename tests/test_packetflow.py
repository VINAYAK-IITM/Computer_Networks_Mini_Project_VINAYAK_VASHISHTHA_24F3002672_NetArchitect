import unittest

from netarchitect.cli import load_profile
from netarchitect.engine import build_plan
from netarchitect.packetflow import simulate_deny_rule, wildcard_match


class PacketFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = build_plan(load_profile("campus"))
        cls.rule = cls.plan["profile"]["acls"][0]

    def test_cisco_wildcard_matches_guest_subnet(self):
        self.assertTrue(wildcard_match("10.10.6.10", "10.10.6.0", "0.0.0.255"))
        self.assertFalse(wildcard_match("10.10.6.10", "10.10.6.0", "255.255.255.0"))

    def test_guest_to_management_is_denied(self):
        result = simulate_deny_rule(self.plan, self.rule, "10.10.6.10", "10.10.7.65")
        self.assertEqual(result["decision"], "deny")

    def test_guest_to_other_destination_is_permitted_by_this_acl(self):
        result = simulate_deny_rule(self.plan, self.rule, "10.10.6.10", "8.8.8.8")
        self.assertEqual(result["decision"], "permit")

    def test_non_guest_source_hits_implicit_deny(self):
        result = simulate_deny_rule(self.plan, self.rule, "10.10.0.10", "8.8.8.8")
        self.assertTrue(result["decision"].startswith("implicit deny"))


if __name__ == "__main__":
    unittest.main()

