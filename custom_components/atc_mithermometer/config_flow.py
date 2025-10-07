"""Config flow for the ATC MiThermometer custom component."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN
from .device import AtcBluetoothDeviceData


class AtcConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for an ATC MiThermometer."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: dict[str, str] = {}
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._device_helper = AtcBluetoothDeviceData()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle flow initiated by Bluetooth discovery."""

        if not self._device_helper.supported(discovery_info):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm adding a discovered device."""

        assert self._discovery_info is not None
        title = self._device_helper.get_title(self._discovery_info)

        if user_input is not None:
            return self.async_create_entry(title=title, data={})

        self._set_confirm_only()
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=placeholders,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let user pick a discovered device or abort if none available."""

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address],
                data={},
            )

        current_ids = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass, connectable=False):
            address = discovery_info.address
            if address in current_ids or address in self._discovered_devices:
                continue
            if not self._device_helper.supported(discovery_info):
                continue
            self._discovered_devices[address] = self._device_helper.get_title(discovery_info)

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(self._discovered_devices)}
            ),
        )
