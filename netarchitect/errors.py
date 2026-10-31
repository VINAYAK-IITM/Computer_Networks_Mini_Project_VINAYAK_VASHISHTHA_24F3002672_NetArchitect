"""Domain-specific errors surfaced by the CLI with actionable context."""


class NetArchitectError(Exception):
    """Base class for expected input and planning failures."""


class ProfileValidationError(NetArchitectError):
    """Raised when a profile is incomplete or internally inconsistent."""


class PhysicalDistanceViolationError(NetArchitectError):
    """Raised when copper is requested beyond its 100 m channel limit."""

    def __init__(self, link_name: str, distance_m: float):
        self.link_name = link_name
        self.distance_m = distance_m
        super().__init__(
            f"Copper request for '{link_name}' is {distance_m:g} m; "
            "the Ethernet copper channel limit is 100 m, beyond which insertion "
            "loss and signal attenuation make the run unreliable. Use fiber or a "
            "carrier service and validate the complete path."
        )


class AddressSpaceExhaustedError(NetArchitectError):
    """Raised when all requested VLSM networks do not fit in the root CIDR."""

