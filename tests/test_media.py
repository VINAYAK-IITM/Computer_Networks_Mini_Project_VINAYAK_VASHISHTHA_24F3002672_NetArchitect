import unittest

from netarchitect.errors import PhysicalDistanceViolationError
from netarchitect.media import recommend_media
from netarchitect.models import LinkSpec


class MediaTests(unittest.TestCase):
    def test_100m_selects_copper(self):
        self.assertIn("Cat6", recommend_media(LinkSpec("access", 100)).medium)

    def test_101m_selects_om4(self):
        self.assertIn("OM4", recommend_media(LinkSpec("backbone", 101)).medium)

    def test_400m_is_om4_boundary(self):
        self.assertIn("OM4", recommend_media(LinkSpec("backbone", 400)).medium)

    def test_401m_selects_os2(self):
        self.assertIn("OS2", recommend_media(LinkSpec("metro", 401)).medium)

    def test_explicit_copper_above_100m_fails(self):
        with self.assertRaises(PhysicalDistanceViolationError):
            recommend_media(LinkSpec("bad-run", 100.1, requested_medium="copper"))

    def test_carrier_service_reports_sla_checks(self):
        result = recommend_media(LinkSpec("evpl", 15000, requested_medium="carrier"))
        self.assertIn("EVPL", result.medium)
        self.assertIn("SLA", result.justification)


if __name__ == "__main__":
    unittest.main()

