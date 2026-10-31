import tempfile
import unittest
from pathlib import Path

from netarchitect.cli import load_profile
from netarchitect.engine import build_plan, write_exports


class ProfileAndExportTests(unittest.TestCase):
    def test_each_assignment_profile_builds_a_non_overlapping_plan(self):
        for profile_id in ("campus", "metro", "global"):
            with self.subTest(profile=profile_id):
                plan = build_plan(load_profile(profile_id))
                self.assertEqual(len(plan["address_plan"]), len(plan["profile"]["subnets"]))

    def test_exports_share_one_address_plan(self):
        plan = build_plan(load_profile("campus"))
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_exports(plan, Path(temp_dir) / "campus")
            self.assertTrue((output / "report.md").exists())
            self.assertTrue((output / "address_plan.csv").exists())
            switch = (output / "core_switch.cfg").read_text(encoding="utf-8")
            self.assertIn("ip address 10.10.6.1 255.255.255.0", switch)
            self.assertIn("ip access-group GUEST-TO-MANAGEMENT in", switch)


if __name__ == "__main__":
    unittest.main()

