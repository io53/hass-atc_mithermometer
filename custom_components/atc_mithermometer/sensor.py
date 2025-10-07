"""Sensor platform for the ATC MiThermometer."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN, MANUFACTURER, MODEL
from .device import AtcBluetoothUpdate


SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "temperature": SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "humidity": SensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "battery": SensorEntityDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "voltage": SensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


def _build_device_info(update: AtcBluetoothUpdate) -> DeviceInfo:
    return DeviceInfo(
        connections={(CONNECTION_BLUETOOTH, update.address)},
        identifiers={(DOMAIN, update.address)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=update.name or DEFAULT_NAME,
    )


def atc_update_to_bluetooth_data_update(
    update: AtcBluetoothUpdate | None,
) -> PassiveBluetoothDataUpdate | None:
    """Convert an ATC update into a PassiveBluetoothDataUpdate."""

    if update is None:
        return None

    device_id = update.address
    device_info = _build_device_info(update)

    entity_descriptions: dict[PassiveBluetoothEntityKey, EntityDescription] = {}
    entity_data: dict[PassiveBluetoothEntityKey, float | int] = {}

    readings = {
        "temperature": update.reading.temperature,
        "humidity": update.reading.humidity,
        "battery": update.reading.battery,
        "voltage": update.reading.voltage,
    }

    for key, value in readings.items():
        if value is None:
            continue
        description = SENSOR_DESCRIPTIONS[key]
        entity_key = PassiveBluetoothEntityKey(description.key, device_id)
        entity_descriptions[entity_key] = description
        entity_data[entity_key] = value

    return PassiveBluetoothDataUpdate(
        devices={device_id: device_info},
        entity_descriptions=entity_descriptions,
        entity_data=entity_data,
        entity_names={},
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the ATC MiThermometer sensors."""

    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    processor = PassiveBluetoothDataProcessor(atc_update_to_bluetooth_data_update)
    entry.async_on_unload(
        processor.async_add_entities_listener(
            AtcBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(coordinator.async_register_processor(processor))


class AtcBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[float | int | None, AtcBluetoothUpdate | None]
    ],
    SensorEntity,
):
    """Representation of an ATC MiThermometer sensor."""

    @property
    def native_value(self) -> float | int | None:
        return self.processor.entity_data.get(self.entity_key)
