"""Bluetooth helper logic for ATC MiThermometer sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
else:  # pragma: no cover - fallback when Home Assistant isn't installed
    @dataclass(slots=True)
    class BluetoothServiceInfoBleak:  # type: ignore[override]
        """Fallback stub used for local testing without Home Assistant."""

        address: str
        name: str
        rssi: int | None
        service_data: dict[str, bytes]

from .const import DEFAULT_NAME, ENVIRONMENTAL_SENSING_UUID
from .parser import AtcParseError, AtcReading, parse_atc_payload


@dataclass(slots=True)
class AtcBluetoothUpdate:
    """Parsed data from a Bluetooth advertisement."""

    address: str
    name: str
    reading: AtcReading
    rssi: int | None
    payload: bytes


class AtcBluetoothDeviceData:
    """Helper to check support and decode ATC advertisements."""

    def supported(self, service_info: BluetoothServiceInfoBleak) -> bool:
        payload = service_info.service_data.get(ENVIRONMENTAL_SENSING_UUID)
        if not payload:
            return False
        try:
            parse_atc_payload(payload)
        except AtcParseError:
            return False
        return True

    def get_title(self, service_info: BluetoothServiceInfoBleak) -> str:
        return service_info.name or DEFAULT_NAME

    def update(self, service_info: BluetoothServiceInfoBleak) -> AtcBluetoothUpdate | None:
        payload = service_info.service_data.get(ENVIRONMENTAL_SENSING_UUID)
        if not payload:
            return None
        try:
            reading = parse_atc_payload(payload)
        except AtcParseError:
            return None
        return AtcBluetoothUpdate(
            address=service_info.address,
            name=self.get_title(service_info),
            reading=reading,
            rssi=service_info.rssi,
            payload=bytes(payload),
        )
