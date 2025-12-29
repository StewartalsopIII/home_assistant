from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass(frozen=True)
class VapiTransport:
    websocket_call_url: str


class VapiClient:
    def __init__(self, http: aiohttp.ClientSession, api_key: str) -> None:
        self._http = http
        self._api_key = api_key

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"authorization": f"Bearer {self._api_key}"}

    async def create_call(self, assistant_id: str, sample_rate: int = 16000) -> VapiTransport:
        url = "https://api.vapi.ai/call"
        payload: dict[str, Any] = {
            "assistantId": assistant_id,
            "transport": {
                "provider": "vapi.websocket",
                "audioFormat": {
                    "format": "pcm_s16le",
                    "container": "raw",
                    "sampleRate": sample_rate,
                },
            },
        }
        async with self._http.post(
            url,
            headers={**self._auth_headers, "content-type": "application/json"},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as r:
            r.raise_for_status()
            data = await r.json()

        websocket_url = (
            data.get("transport", {}) or {}
        ).get("websocketCallUrl")
        if not websocket_url:
            raise RuntimeError(f"Vapi response missing websocketCallUrl: {json.dumps(data)[:500]}")
        return VapiTransport(websocket_call_url=websocket_url)

    async def connect_transport(self, transport: VapiTransport) -> aiohttp.ClientWebSocketResponse:
        return await self._http.ws_connect(
            transport.websocket_call_url,
            headers=self._auth_headers,
            heartbeat=30,
            autoping=True,
            autoclose=True,
            max_msg_size=0,  # allow large audio frames
        )
