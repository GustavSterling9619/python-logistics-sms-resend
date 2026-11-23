from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.infrai_client import InfraiClient, SmsEvent


@dataclass(frozen=True)
class ShipmentEvent:
    kind: str
    occurred_at: str


@dataclass(frozen=True)
class ProofOfDelivery:
    name: str
    content_type: str


@dataclass(frozen=True)
class ShipmentException:
    code: str
    note: str


@dataclass
class VerificationResult:
    shipment_id: str
    resent: bool
    delivery_status: str
    events: list[SmsEvent] = field(default_factory=list)
    exceptions: list[ShipmentException] = field(default_factory=list)


def resend_stuck_verification(
    shipment_id: str,
    verification_message_id: str,
    shipment_events: list[ShipmentEvent],
    proof_files: list[ProofOfDelivery],
    client: InfraiClient,
) -> VerificationResult:
    """Resend only when the latest recorded shipment state is verification-stuck."""
    del proof_files
    latest = shipment_events[-1].kind if shipment_events else "unknown"
    if latest != "verification_stuck":
        return VerificationResult(
            shipment_id=shipment_id,
            resent=False,
            delivery_status="not_sent",
            exceptions=[ShipmentException("verification_not_stuck", latest)],
        )
    client.resend_sms(verification_message_id)
    events = client.sms_events(verification_message_id)
    status = events[-1].status if events else "pending"
    return VerificationResult(shipment_id, True, status, events)


def result_as_dict(result: VerificationResult) -> dict[str, Any]:
    return {
        "shipment_id": result.shipment_id,
        "resent": result.resent,
        "delivery_status": result.delivery_status,
        "sms_events": [event.__dict__ for event in result.events],
        "exceptions": [item.__dict__ for item in result.exceptions],
    }

