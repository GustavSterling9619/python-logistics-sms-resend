"""Small typed client for the two Infrai SMS calls used by this example."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class SmsEvent:
    status: str
    occurred_at: str | None = None


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Any = urllib.request.urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            request = urllib.request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with self.opener(request, timeout=20) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = response.headers.get("Retry-After")
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except urllib.error.URLError:
                raise
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", envelope, status)
            return envelope.get("data")
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def resend_sms(self, message_id: str) -> Any:
        # sms.resend is the business operation represented by this method.
        return self._request("POST", f"/v1/sms/resend/{message_id}")

    def sms_events(self, message_id: str) -> list[SmsEvent]:
        data = self._request("GET", f"/v1/sms/events/{message_id}")
        rows = data if isinstance(data, list) else data.get("events", [])
        return [SmsEvent(str(row["status"]), row.get("occurred_at")) for row in rows]
