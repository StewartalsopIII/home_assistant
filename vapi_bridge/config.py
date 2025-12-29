from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _load_env_file(path: str) -> None:
    try:
        p = Path(path)
        if not p.is_file():
            return
        for raw_line in p.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key or key in os.environ:
                continue
            if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
                value = value[1:-1]
            os.environ[key] = value
    except Exception:
        # Best-effort only; config validation will fail later if required vars are missing.
        return


@dataclass(frozen=True)
class Config:
    vapi_private_api_key: str
    vapi_assistant_id: str

    udp_bind_host: str
    udp_port: int

    # Vapi transport format (fixed for now)
    vapi_sample_rate: int = 16000

    # Device speaker format (what we send over UDP to ESPHome)
    device_speaker_sample_rate: int = 16000
    device_speaker_bits_per_sample: int = 16
    device_speaker_channels: int = 2

    # Session lifecycle
    idle_timeout_s: float = 20.0
    voice_rms_threshold: int = 500

    @staticmethod
    def from_env() -> "Config":
        _load_env_file(os.getenv("VAPI_BRIDGE_ENV_FILE", ".env"))

        vapi_private_api_key = os.getenv("VAPI_PRIVATE_API_KEY", "").strip()
        vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID", "").strip()
        if not vapi_private_api_key:
            raise RuntimeError("Missing env var: VAPI_PRIVATE_API_KEY")
        if not vapi_assistant_id:
            raise RuntimeError("Missing env var: VAPI_ASSISTANT_ID")

        return Config(
            vapi_private_api_key=vapi_private_api_key,
            vapi_assistant_id=vapi_assistant_id,
            udp_bind_host=os.getenv("VAPI_BRIDGE_UDP_BIND_HOST", "0.0.0.0"),
            udp_port=_getenv_int("VAPI_BRIDGE_UDP_PORT", 9123),
            idle_timeout_s=float(os.getenv("VAPI_BRIDGE_IDLE_TIMEOUT_S", "20.0")),
            voice_rms_threshold=_getenv_int("VAPI_BRIDGE_VOICE_RMS_THRESHOLD", 500),
        )
