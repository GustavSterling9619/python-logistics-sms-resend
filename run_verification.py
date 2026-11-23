import json
import os

from src.infrai_client import InfraiClient
from shipment_verification import ProofOfDelivery, ShipmentEvent, resend_stuck_verification, result_as_dict


def main() -> None:
    shipment_id = os.environ.get("SHIPMENT_ID", "shipment-demo-42")
    message_id = os.environ["VERIFICATION_MESSAGE_ID"]
    result = resend_stuck_verification(
        shipment_id,
        message_id,
        [ShipmentEvent("verification_stuck", "2026-10-25T08:00:00Z")],
        [ProofOfDelivery("signed-receipt.pdf", "application/pdf")],
        InfraiClient(),
    )
    print(json.dumps(result_as_dict(result), indent=2))


if __name__ == "__main__":
    main()

