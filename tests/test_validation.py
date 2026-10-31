import unittest

from netarchitect.errors import ProfileValidationError
from netarchitect.models import Profile, SubnetSpec
from netarchitect.validation import validate_profile


def base_profile(**overrides):
    fields = dict(
        profile_id="custom", name="Custom", description="Validation fixture",
        root_cidr="10.0.0.0/24", endpoint_count=40, site_count=1,
        cloud_boundary=False, target_latency_ms=None, links=(),
        subnets=(SubnetSpec("users", 30, "Users"),), acls=(),
    )
    fields.update(overrides)
    return Profile(**fields)


class ValidationTests(unittest.TestCase):
    def test_valid_custom_inputs_are_accepted(self):
        validate_profile(base_profile())

    def test_density_range_is_validated(self):
        with self.assertRaises(ProfileValidationError):
            validate_profile(base_profile(switch_port_density=0))

    def test_resiliency_requires_multiple_routed_handoffs(self):
        with self.assertRaises(ProfileValidationError):
            validate_profile(base_profile(resiliency="dual_homed"))

    def test_dual_homed_profile_accepts_two_handoffs(self):
        profile = base_profile(
            resiliency="dual_homed",
            subnets=(
                SubnetSpec("users", 30, "Users"),
                SubnetSpec("wan_primary", 1, "Primary", interface="GigabitEthernet0/0"),
                SubnetSpec("wan_backup", 1, "Backup", interface="GigabitEthernet0/1"),
            ),
        )
        validate_profile(profile)

    def test_route_summary_must_contain_the_root(self):
        with self.assertRaises(ProfileValidationError):
            validate_profile(base_profile(route_summary="10.0.0.0/25"))


if __name__ == "__main__":
    unittest.main()

