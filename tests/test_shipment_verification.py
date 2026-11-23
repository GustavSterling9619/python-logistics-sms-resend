from src.infrai_client import SmsEvent
from shipment_verification import ShipmentEvent, resend_stuck_verification


class FakeClient:
    def __init__(self):
        self.calls = []

    def resend_sms(self, message_id):
        self.calls.append(("resend", message_id))

    def sms_events(self, message_id):
        self.calls.append(("events", message_id))
        return [SmsEvent("delivered")]


def test_stuck_verification_is_resent_and_delivery_state_is_returned():
    client = FakeClient()
    result = resend_stuck_verification(
        "S-7", "M-9", [ShipmentEvent("verification_stuck", "now")], [], client
    )
    assert result.resent is True
    assert result.delivery_status == "delivered"
    assert client.calls == [("resend", "M-9"), ("events", "M-9")]


def test_non_stuck_shipment_is_recorded_as_an_exception():
    client = FakeClient()
    result = resend_stuck_verification(
        "S-7", "M-9", [ShipmentEvent("delivered", "now")], [], client
    )
    assert result.resent is False
    assert result.exceptions[0].code == "verification_not_stuck"
    assert client.calls == []
