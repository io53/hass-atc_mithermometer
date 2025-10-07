"""Helpers for decoding ATC MiThermometer Bluetooth payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

EXPECTED_PAYLOAD_LENGTH = 12


class AtcParseError(ValueError):
    """Raised when an ATC payload cannot be decoded."""


@dataclass(frozen=True)
class AtcReading:
    """Container for a single advertisement reading."""

    temperature: float
    humidity: int
    battery: int
    voltage: float


def _ensure_bytes(data: Iterable[int] | bytes | bytearray) -> bytes:
    """Coerce iterable payloads into a bytes object."""

    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return bytes(int(value) & 0xFF for value in data)


def parse_atc_payload(payload: Iterable[int] | bytes | bytearray) -> AtcReading:
    """Decode an ATC MiThermometer service data payload.

    The payload usually appears inside Bluetooth LE service data for UUID 0x181A
    (Environmental Sensing). The value format matches the ATC custom firmware:

    * Bytes 0-5: reversed MAC address (ignored here)
    * Bytes 6-7: temperature in tenths of °C, big-endian, signed
    * Byte 8: humidity as percentage
    * Byte 9: battery level in percent
    * Bytes 10-11: battery voltage in millivolts, big-endian
    """

    payload_bytes = _ensure_bytes(payload)

    if len(payload_bytes) < EXPECTED_PAYLOAD_LENGTH:
        raise AtcParseError(
            f"ATC payload must be at least {EXPECTED_PAYLOAD_LENGTH} bytes, got {len(payload_bytes)}"
        )

    trimmed = payload_bytes[:EXPECTED_PAYLOAD_LENGTH]

    temperature_raw = int.from_bytes(trimmed[6:8], "big", signed=True)
    humidity = trimmed[8]
    battery = trimmed[9]
    voltage_raw = int.from_bytes(trimmed[10:12], "big", signed=False)

    temperature_c = round(temperature_raw / 10.0, 1)
    voltage_v = round(voltage_raw / 1000.0, 3)

    return AtcReading(
        temperature=temperature_c,
        humidity=humidity,
        battery=battery,
        voltage=voltage_v,
    )
