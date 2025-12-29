from __future__ import annotations

import audioop
from dataclasses import dataclass


@dataclass
class MicFormat:
    sample_rate: int
    bits_per_sample: int
    channels: int

    @property
    def sample_width_bytes(self) -> int:
        if self.bits_per_sample % 8 != 0:
            raise ValueError("bits_per_sample must be byte-aligned")
        return self.bits_per_sample // 8


class MicToVapiConverter:
    def __init__(self, mic_format: MicFormat, vapi_sample_rate: int = 16000) -> None:
        self.mic_format = mic_format
        self.vapi_sample_rate = vapi_sample_rate
        self._rate_state: tuple[object, object] | None = None

    def convert(self, data: bytes) -> bytes:
        width = self.mic_format.sample_width_bytes
        channels = self.mic_format.channels

        if channels == 2:
            data = audioop.tomono(data, width, 0.5, 0.5)
            channels = 1

        if width != 2:
            data = audioop.lin2lin(data, width, 2)
            width = 2

        if self.mic_format.sample_rate != self.vapi_sample_rate:
            data, self._rate_state = audioop.ratecv(
                data, width, channels, self.mic_format.sample_rate, self.vapi_sample_rate, self._rate_state
            )

        return data


class VapiToDeviceConverter:
    def __init__(self, device_sample_rate: int = 16000, device_channels: int = 2) -> None:
        self.device_sample_rate = device_sample_rate
        self.device_channels = device_channels
        self._rate_state: tuple[object, object] | None = None

    def convert(self, vapi_pcm_s16le_mono_16k: bytes) -> bytes:
        data = vapi_pcm_s16le_mono_16k

        if self.device_sample_rate != 16000:
            data, self._rate_state = audioop.ratecv(
                data, 2, 1, 16000, self.device_sample_rate, self._rate_state
            )

        if self.device_channels == 2:
            data = audioop.tostereo(data, 2, 1.0, 1.0)

        return data

