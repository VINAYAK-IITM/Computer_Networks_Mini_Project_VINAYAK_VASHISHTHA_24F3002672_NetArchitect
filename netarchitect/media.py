"""Distance-aware media selection and explicit optical-budget estimates."""

from dataclasses import asdict, dataclass

from .errors import PhysicalDistanceViolationError
from .models import LinkSpec


@dataclass(frozen=True)
class MediaRecommendation:
    link: str
    distance_m: float
    medium: str
    standard: str
    justification: str
    estimated_loss_db: float | None = None
    assumed_budget_db: float | None = None
    budget_status: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def recommend_media(link: LinkSpec) -> MediaRecommendation:
    distance = link.distance_m
    if link.requested_medium == "copper" and distance > 100:
        raise PhysicalDistanceViolationError(link.name, distance)

    if link.requested_medium == "carrier":
        return MediaRecommendation(
            link=link.name,
            distance_m=distance,
            medium="Carrier Ethernet / EVPL",
            standard="Provider-defined UNI and SLA",
            justification=(
                "A managed Layer 2 service keeps the physical path and protection "
                "inside the carrier domain. Confirm the committed latency, CIR, "
                "MTU, QoS marking, and diverse-path SLA with the provider."
            ),
        )

    wants_fiber = link.requested_medium == "fiber"
    if not wants_fiber and distance <= 100:
        return MediaRecommendation(
            link=link.name,
            distance_m=distance,
            medium="Cat6a balanced copper",
            standard="10GBASE-T (IEEE 802.3an), channel up to 100 m",
            justification=(
                "The run is within the 100 m Ethernet channel limit. Cat6a supports "
                "10GBASE-T over a compliant channel; verify alien crosstalk, cable "
                "bundle temperature, and the switch's PoE power budget for attached devices."
            ),
        )

    if distance <= 400:
        attenuation_db_per_km = 3.0
        medium = "OM4 multimode fiber"
        standard = "10GBASE-SR, 850 nm, up to 400 m on OM4"
        reason = (
            "OM4 provides the modal bandwidth and reach for 10GBASE-SR at 850 nm "
            "over this campus backbone distance. Keep the optical channel within "
            "the transceiver's published reach and dispersion specification."
        )
    else:
        attenuation_db_per_km = 0.35
        medium = "OS2 single-mode fiber"
        if distance <= 10_000:
            standard = "10GBASE-LR, 1310 nm, nominal reach up to 10 km"
            reason = "OS2 with LR optics is appropriate for this long-reach single-mode link."
        elif distance <= 40_000:
            standard = "10GBASE-ER, 1550 nm, nominal reach up to 40 km"
            reason = (
                "OS2 with ER optics covers this metropolitan distance within the "
                "nominal reach; verify attenuation, dispersion, and receive power."
            )
        else:
            standard = "Carrier-engineered coherent optics or a managed wavelength service"
            reason = (
                "The distance exceeds the nominal reach of common LR/ER 10 GbE optics. "
                "Use an engineered optical system or carrier service."
            )

    estimated_loss = (
        (distance / 1000) * attenuation_db_per_km
        + link.connectors * 0.75
        + link.splices * 0.10
        + 3.0
    )
    status = (
        "within the stated generic budget estimate"
        if estimated_loss <= link.transceiver_budget_db
        else "exceeds the stated generic budget estimate; redesign or select optics"
    )
    reason += (
        f" Estimated loss is {estimated_loss:.2f} dB using {attenuation_db_per_km:g} dB/km, "
        f"{link.connectors} connectors at 0.75 dB each, {link.splices} splices at 0.10 dB "
        f"each, and a 3 dB engineering margin; assumed budget is "
        f"{link.transceiver_budget_db:.2f} dB ({status}). This estimate is not a "
        "substitute for the selected optic's datasheet and an end-to-end power/dispersion check."
    )
    return MediaRecommendation(
        link=link.name,
        distance_m=distance,
        medium=medium,
        standard=standard,
        justification=reason,
        estimated_loss_db=round(estimated_loss, 2),
        assumed_budget_db=link.transceiver_budget_db,
        budget_status=status,
    )

