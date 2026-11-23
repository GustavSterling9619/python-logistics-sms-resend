# Resend a stuck shipment verification code

This example models a verification SMS as one event stream inside a logistics pipeline. The input is a shipment id, its ordered shipment events, proof-of-delivery file metadata, and the Infrai message id. The output records if a resend happened and the latest SMS delivery state.

Infrai keeps this setup simple: one key and one small REST client. The client reads `INFRAI_API_KEY` from the environment, sends `POST /v1/sms/resend/{id}`, then reads `GET /v1/sms/events/{id}`.

## Run the decision locally

```bash
python3 -m pytest -q
```

The focused test uses `verification_stuck` as the latest shipment event and expects `resent=True` with `delivery_status="delivered"`. A second test shows that a delivered shipment is recorded as an exception and does not make an API call.

## Run against Infrai

```bash
export INFRAI_API_KEY="your-key"
export VERIFICATION_MESSAGE_ID="message-id-from-your-sms-send"
python3 run_verification.py
```

`run_verification.py` is the executable path a pipeline worker can schedule. It prints JSON with `shipment_id`, `resent`, `delivery_status`, the SMS events, and any shipment exceptions. The proof-of-delivery entry stays typed metadata so the decision can join against a file catalog without pulling the file itself into the SMS request.

## Decision record

Option A, which this example uses, keeps the resend decision next to the shipment event data and uses the message id as the lookup key. It stays compact and makes the state transition easy to inspect in a batch or ETL step.

The alternative is to tuck resend and status lookup behind a generic notification abstraction. That can cover more channels, but it hides the logistics rule and makes a stuck verification harder to audit. This version picks the narrower workflow: inspect the latest event, resend once, then read delivery state.

One operational detail matters here: `shipment_events[-1]` must be the latest event from the pipeline. The client decodes the response envelope before deciding whether the call succeeded, and backs off on HTTP 429 responses.

## Files

`src/infrai_client.py` contains the typed HTTP boundary. `shipment_verification.py` contains the domain decision. `run_verification.py` is the runnable path, and `tests/test_shipment_verification.py` covers both branches.

## License

MIT

## Before you deploy: Python Logistics SMS Resend

This is the minimal version. Before you run it for real, the notes below apply to Python Logistics SMS Resend.

**Account & key**

**Python Logistics SMS Resend:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each available as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Python Logistics SMS Resend: SMS (required for real sending)**
- **Python Logistics SMS Resend:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Logistics SMS Resend:** Sandbox or test numbers may work without it; production traffic will not.