from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

MAGIC = b"VAPB"
VERSION = 1


class PacketType(IntEnum):
    MIC_AUDIO = 1
    SPK_AUDIO = 2
    CONTROL = 3


HEADER_STRUCT = struct.Struct("!4sBBHII")
HEADER_SIZE = HEADER_STRUCT.size  # 16 bytes


@dataclass(frozen=True)
class Header:
    packet_type: PacketType
    session_id: int
    seq: int


def parse_packet(data: bytes) -> tuple[Header, bytes]:
    if len(data) < HEADER_SIZE:
        raise ValueError("packet too small")
    magic, version, ptype, _reserved, session_id, seq = HEADER_STRUCT.unpack_from(data)
    if magic != MAGIC:
        raise ValueError("bad magic")
    if version != VERSION:
        raise ValueError("unsupported version")
    try:
        packet_type = PacketType(ptype)
    except ValueError as e:
        raise ValueError("unknown packet type") from e
    return Header(packet_type=packet_type, session_id=session_id, seq=seq), data[HEADER_SIZE:]


def build_packet(packet_type: PacketType, session_id: int, seq: int, payload: bytes) -> bytes:
    return HEADER_STRUCT.pack(MAGIC, VERSION, int(packet_type), 0, int(session_id), int(seq)) + payload


def build_control(packet: dict[str, Any], session_id: int, seq: int = 0) -> bytes:
    payload = json.dumps(packet, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return build_packet(PacketType.CONTROL, session_id=session_id, seq=seq, payload=payload)


def parse_control(payload: bytes) -> dict[str, Any]:
    return json.loads(payload.decode("utf-8"))

