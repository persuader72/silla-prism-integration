"""Contains sensors exposed by the Prism wallbox integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .domain_data import DomainData
from .entity import PrismEntity
from .entry_data import RuntimeEntryData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up all sensors for this entry."""
    entry_data: RuntimeEntryData = DomainData.get(hass).get_entry_data(entry)
    _LOGGER.debug("async_setup_entry for sensors: %s", entry_data)
    sensors = [
        PrismSensor(hass, entry_data.topic, description) for description in SENSORS
    ]
    async_add_entities(sensors)


class PrismSensor(PrismEntity, SensorEntity):
    """A Sensor for Prism wallbox devices."""

    entity_description: SensorEntityDescription
    _attr_should_poll = False

    def __init__(
        self, hass: HomeAssistant, base_topic: str, description: EntityDescription
    ) -> None:
        """Init Prism sensor."""
        super().__init__(base_topic, description)
        self._hass: HomeAssistant = hass
        self._unsubscribe = None

    async def _subscribe_topic(self):
        """Subscribe to mqtt topic."""
        _LOGGER.debug("_subscribe_topic: %s", self._topic)
        self._unsubscribe = await self._hass.components.mqtt.async_subscribe(
            self._topic, self.message_received
        )

    async def _unsubscribe_topic(self):
        """Unsubscribe to mqtt topic."""
        _LOGGER.debug("_unsubscribe_topic: %s", self._topic)
        if self._unsubscribe is not None:
            await self._unsubscribe()

    def message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        if self.options is not None:
            try:
                self._attr_native_value = self.options[int(msg.payload) - 1]
            except IndexError:
                self._attr_native_value = None
        else:
            self._attr_native_value = msg.payload
        self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to mqtt."""
        _LOGGER.debug("async_added_to_hass")
        await self._subscribe_topic()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from mqtt."""
        _LOGGER.debug("async_will_remove_from_hass")
        await super().async_will_remove_from_hass()
        if self._unsubscribe is not None:
            await self._unsubscribe_topic()


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="state",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "waiting", "charging", "pause"],
        has_entity_name=True,
        translation_key="state",
    ),
    SensorEntityDescription(
        key="volt",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="volt",
    ),
    SensorEntityDescription(
        key="w",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="w",
    ),
    SensorEntityDescription(
        key="amp",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="amp",
    ),
    SensorEntityDescription(
        key="pilot",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="pilot",
    ),
    SensorEntityDescription(
        key="user_amp",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="user_amp",
    ),
    SensorEntityDescription(
        key="session_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="session_time",
    ),
    SensorEntityDescription(
        key="wh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="wh",
    ),
    SensorEntityDescription(
        key="wh_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="wh_total",
    ),
    SensorEntityDescription(
        key="mode",
        device_class=SensorDeviceClass.ENUM,
        options=["solar", "normal", "paused", "suspended"],
        has_entity_name=True,
        translation_key="mode",
    ),
    SensorEntityDescription(
        key="energy_data/power_grid",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="power_grid",
    ),
)
