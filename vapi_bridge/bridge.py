from __future__ import annotations

import asyncio
import audioop
import contextlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

from .audio import MicFormat, MicToVapiConverter, VapiToDeviceConverter
from .config import Config
from .protocol import (
    PacketType,
    build_control,
    build_packet,
    parse_control,
    parse_packet,
)
from .vapi import VapiClient

_LOG = logging.getLogger("vapi_bridge")

MAX_UDP_PACKET_SIZE = 508  # must match ESPHome UDPComponent::MAX_PACKET_SIZE
MAX_UDP_PAYLOAD_SIZE = 480  # leave space for header + future growth


@dataclass
class Session:
    session_id: int
    device_addr: tuple[str, int]
    mic_format: MicFormat

    mic_queue: asyncio.Queue[bytes]
    stop_event: asyncio.Event

    seq_out: int = 0
    last_activity: float = 0.0

    def touch(self) -> None:
        self.last_activity = time.monotonic()


class Bridge(asyncio.DatagramProtocol):
    def __init__(self, config: Config) -> None:
        self._config = config
        self._transport: asyncio.DatagramTransport | None = None
        self._http: aiohttp.ClientSession | None = None
        self._vapi: VapiClient | None = None

        self._session: Session | None = None
        self._session_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        # Long-lived WebSocket; don't use a global total timeout.
        self._http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None))
        self._vapi = VapiClient(self._http, self._config.vapi_private_api_key)

        loop = asyncio.get_running_loop()
        transport, _protocol = await loop.create_datagram_endpoint(
            lambda: self, local_addr=(self._config.udp_bind_host, self._config.udp_port)
        )
        self._transport = transport  # type: ignore[assignment]
        _LOG.info("UDP listening on %s:%d", self._config.udp_bind_host, self._config.udp_port)

    async def close(self) -> None:
        await self._end_session(reason="shutdown")
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        if self._http is not None:
            await self._http.close()
            self._http = None

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            header, payload = parse_packet(data)
        except Exception as e:
            _LOG.debug("Dropping UDP from %s:%d: %s", addr[0], addr[1], e)
            return

        if header.packet_type == PacketType.CONTROL:
            try:
                msg = parse_control(payload)
            except Exception:
                _LOG.warning("Bad CONTROL JSON from %s:%d", addr[0], addr[1])
                return
            asyncio.create_task(self._handle_control(msg, header.session_id, addr))
            return

        if header.packet_type == PacketType.MIC_AUDIO:
            session = self._session
            if session is None or header.session_id != session.session_id:
                return
            if session.stop_event.is_set():
                return
            try:
                session.mic_queue.put_nowait(payload)
            except asyncio.QueueFull:
                # Drop oldest audio to keep latency bounded
                with contextlib.suppress(asyncio.QueueEmpty):
                    _ = session.mic_queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    session.mic_queue.put_nowait(payload)
            return

    async def _handle_control(self, msg: dict[str, Any], session_id: int, addr: tuple[str, int]) -> None:
        msg_type = msg.get("type")
        if msg_type == "start":
            mic = msg.get("mic", {}) or {}
            mic_format = MicFormat(
                sample_rate=int(mic.get("sample_rate", 48000)),
                bits_per_sample=int(mic.get("bits_per_sample", 32)),
                channels=int(mic.get("channels", 2)),
            )
            await self._start_session(session_id=session_id, device_addr=addr, mic_format=mic_format)
            return

        if msg_type == "stop":
            if self._session is not None and self._session.session_id == session_id:
                await self._end_session(reason="device_stop")
            return

        _LOG.info("CONTROL from %s:%d: %s", addr[0], addr[1], json.dumps(msg)[:500])

    async def _start_session(self, session_id: int, device_addr: tuple[str, int], mic_format: MicFormat) -> None:
        await self._end_session(reason="restart")
        if self._transport is None or self._vapi is None:
            raise RuntimeError("bridge not started")

        _LOG.info("Starting session %d from %s:%d (mic=%s)", session_id, device_addr[0], device_addr[1], mic_format)
        session = Session(
            session_id=session_id,
            device_addr=device_addr,
            mic_format=mic_format,
            mic_queue=asyncio.Queue(maxsize=200),
            stop_event=asyncio.Event(),
            last_activity=time.monotonic(),
        )
        self._session = session
        task = asyncio.create_task(self._run_session(session), name=f"session-{session_id}")
        task.add_done_callback(lambda t: self._on_session_done(session_id, t))
        self._session_task = task

    def _on_session_done(self, session_id: int, task: asyncio.Task[None]) -> None:
        # If the session task ends on its own (idle timeout, remote close, etc), clear state.
        if self._session is not None and self._session.session_id == session_id and self._session_task is task:
            self._session = None
            self._session_task = None

        with contextlib.suppress(asyncio.CancelledError):
            exc = task.exception()
            if exc is not None:
                _LOG.exception("Session %d crashed", session_id, exc_info=exc)

    async def _end_session(self, reason: str) -> None:
        session = self._session
        task = self._session_task
        self._session = None
        self._session_task = None

        if session is not None:
            _LOG.info("Ending session %d (%s)", session.session_id, reason)
            session.stop_event.set()

        if task is not None:
            try:
                await asyncio.wait_for(task, timeout=5)
            except asyncio.TimeoutError:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    def _udp_send(self, packet: bytes, addr: tuple[str, int]) -> None:
        if self._transport is None:
            return
        self._transport.sendto(packet, addr)

    async def _run_session(self, session: Session) -> None:
        assert self._vapi is not None
        assert self._transport is not None

        mic_to_vapi = MicToVapiConverter(session.mic_format, vapi_sample_rate=self._config.vapi_sample_rate)
        vapi_to_device = VapiToDeviceConverter(
            device_sample_rate=self._config.device_speaker_sample_rate,
            device_channels=self._config.device_speaker_channels,
        )

        transport = await self._vapi.create_call(self._config.vapi_assistant_id, sample_rate=self._config.vapi_sample_rate)
        ws = await self._vapi.connect_transport(transport)

        async def send_mic() -> None:
            while not session.stop_event.is_set():
                try:
                    data = await asyncio.wait_for(session.mic_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                out = mic_to_vapi.convert(data)
                if out:
                    if audioop.rms(out, 2) >= self._config.voice_rms_threshold:
                        session.touch()
                    await ws.send_bytes(out)

        async def recv_vapi() -> None:
            while not session.stop_event.is_set():
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.BINARY:
                    session.touch()
                    pcm = vapi_to_device.convert(msg.data)
                    # chunk to fit ESPHome UDP receiver buffer
                    for i in range(0, len(pcm), MAX_UDP_PAYLOAD_SIZE):
                        chunk = pcm[i : i + MAX_UDP_PAYLOAD_SIZE]
                        packet = build_packet(PacketType.SPK_AUDIO, session.session_id, session.seq_out, chunk)
                        session.seq_out += 1
                        if len(packet) > MAX_UDP_PACKET_SIZE:
                            _LOG.warning("Downlink packet too large (%d bytes); truncating", len(packet))
                            packet = packet[:MAX_UDP_PACKET_SIZE]
                        self._udp_send(packet, session.device_addr)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    # Control messages from Vapi
                    _LOG.info("Vapi: %s", msg.data[:500])
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                    break

        async def idle_watchdog() -> None:
            while not session.stop_event.is_set():
                await asyncio.sleep(1.0)
                if (time.monotonic() - session.last_activity) > self._config.idle_timeout_s:
                    _LOG.info("Session %d idle timeout", session.session_id)
                    session.stop_event.set()

        tasks = [
            asyncio.create_task(send_mic(), name=f"mic-send-{session.session_id}"),
            asyncio.create_task(recv_vapi(), name=f"vapi-recv-{session.session_id}"),
            asyncio.create_task(idle_watchdog(), name=f"idle-{session.session_id}"),
        ]

        try:
            await session.stop_event.wait()
        finally:
            with contextlib.suppress(Exception):
                await ws.send_str(json.dumps({"type": "end-call"}))
            with contextlib.suppress(Exception):
                await ws.close()

            for t in tasks:
                t.cancel()
            for t in tasks:
                with contextlib.suppress(asyncio.CancelledError):
                    await t

            # Tell device to stop capture / return to idle
            self._udp_send(build_control({"type": "end"}, session_id=session.session_id), session.device_addr)
