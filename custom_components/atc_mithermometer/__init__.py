"""ATC MiThermometer custom component."""

from __future__ import annotations

import logging

from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import AtcBluetoothDeviceData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ATC MiThermometer from a config entry."""

    address = entry.unique_id or entry.data.get("address")
    if address is None:
        raise ValueError("Config entry missing Bluetooth address")

    helper = AtcBluetoothDeviceData()
    coordinator = hass.data.setdefault(DOMAIN, {})[entry.entry_id] = (
        PassiveBluetoothProcessorCoordinator(
            hass,
            _LOGGER,
            address=address,
            mode=BluetoothScanningMode.PASSIVE,
            update_method=helper.update,
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
