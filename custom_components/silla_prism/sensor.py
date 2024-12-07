"""Contains sensors exposed by the Prism wallbox integration."""

from contextlib import suppress
from datetime import datetime
from decimal import Decimal
import logging
from typing import List
from .const import SENSOR_DOMAIN

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
    UnitOfTemperature,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.components import mqtt
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

from .domain_data import DomainData
from .entity import PrismBaseEntity, _get_unique_id, _get_entity_id
from .entry_data import RuntimeEntryData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up all sensors for this entry."""
    entry_data: RuntimeEntryData = DomainData.get(hass).get_entry_data(entry)
    _LOGGER.debug("async_setup_entry for sensors: %s", entry_data)
    ports = entry_data.ports

    sensors = []
    for port in range(1, ports+1):
        for description in SENSORS:
            sensors.append(PrismSensor(entry_data, description, port))
    for description in BASE_SENSORS:
        sensors.append(PrismSensor(entry_data, description, 0))
    if entry_data.vsensors:
        sensors.append(PrismGridEnergy(entry_data, VSENSORS[0]))
    async_add_entities(sensors)


class PrismSensorEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """A class that describes prism binary sensor entities."""

    expire_after: float = 600
    topic: str = None


class PrismGridEnergy(SensorEntity, RestoreEntity):
    """A Sensor that compute the integral of energy take from grid."""

    _attr_should_poll = False
    _attr_translation_key = "input_grid_energy"

    def __init__(
        self, entry_data: RuntimeEntryData, description: SensorEntityDescription
    ) -> None:
        self._attr_device_info = entry_data.devices[0]
        self.entity_id = _get_entity_id(entry_data.serial, SENSOR_DOMAIN, description.key)
        self.entity_description = description
        self._attr_unique_id = _get_unique_id(entry_data.serial, description.key)
        self._integral: Decimal = Decimal(0)

    async def async_added_to_hass(self) -> None:
        """Called when sensor is added to hass"""
        _LOGGER.debug("async_added_to_hass %s", self.entity_description.key)
        await super().async_internal_added_to_hass()

        if state := await self.async_get_last_state():
            _LOGGER.debug("async_added_to_hass last state %s", state)
            if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                with suppress(ValueError):
                    self._integral = Decimal(state.state)
                    self._attr_native_value = round(self._integral, 1)
            else:
                _LOGGER.warning(
                    "async_added_to_hass can't restore state of %s",
                    self.entity_description.key,
                )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, "sensor.silla_prism_input_grid_power", self._calc_integral
            )
        )

    @callback
    def _calc_integral(self, event: Event[EventStateChangedData]) -> None:
        """Handle the sensor state changes."""
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]

        if old_state is None:
            return

        if old_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE) or new_state.state in (
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            if self._attr_available:
                self._attr_available = False
                self.async_write_ha_state()
            return

        elapsed_time = Decimal(
            (new_state.last_updated - old_state.last_updated).total_seconds() / 3600
        )
        average_value = (Decimal(new_state.state) + Decimal(old_state.state)) / Decimal(
            2
        )
        self._integral += elapsed_time * average_value
        self._attr_native_value = round(self._integral, 1)

        if not self._attr_available:
            self._attr_available = True
        self.async_write_ha_state()


class PrismSensor(PrismBaseEntity, SensorEntity):
    """A Sensor for Prism EVSE devices."""

    entity_description: PrismSensorEntityDescription

    def description(self, port: int, mulitport: bool, description: PrismSensorEntityDescription) -> PrismSensorEntityDescription:
        if port == 0:
            return description
        if mulitport:
            return PrismSensorEntityDescription(
                key=description.key.format(port),
                topic=description.topic.format(port),
                device_class=description.device_class,
                state_class=description.state_class,
                native_unit_of_measurement=description.native_unit_of_measurement,
                suggested_display_precision=description.suggested_display_precision,
                options=description.options,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
            )
        else:
            return PrismSensorEntityDescription(
                key=description.key[:-3],
                topic=description.topic.format(port),
                device_class=description.device_class,
                state_class=description.state_class,
                native_unit_of_measurement=description.native_unit_of_measurement,
                suggested_display_precision=description.suggested_display_precision,
                options=description.options,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
            )

    def __init__(
        self, entry_data: RuntimeEntryData, description: EntityDescription, port: int
    ) -> None:
        """Init Prism sensor."""
        ismultiport = entry_data.ports > 1
        if not ismultiport:
            device = entry_data.devices[0]
        else:
            device = entry_data.devices[port]
        super().__init__(
            entry_data,
            SENSOR_DOMAIN,
            self.description(port, ismultiport, description),
            device,
        )

    async def _subscribe_topic(self):
        """Subscribe to mqtt topic."""
        _LOGGER.debug("_subscribe_topic: %s", self._topic)
        self.config_entry.async_on_unload(
            await mqtt.async_subscribe(self.hass, self._topic, self.message_received)
        )

    @callback
    def _value_is_expired(self, *_: datetime) -> None:
        """Triggered when value is expired."""
        _LOGGER.debug("_value_is_expired %s", self._topic)
        self._expiration_trigger = None
        self._attr_available = False
        self.async_write_ha_state()

    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        # _LOGGER.debug("_message_received %s %s", self._topic, msg.payload)
        if self._expire_after is not None and self._expire_after > 0:
            # When self._expire_after is set, and we receive a message, assume
            # device is not expired since it has to be to receive the message
            self._attr_available = True
            # Reset old trigger
            if self._expiration_trigger:
                self._expiration_trigger()
            # Set new trigger
            self._expiration_trigger = async_call_later(
                self.hass, self._expire_after, self._value_is_expired
            )
        # Update native value
        if self.options is not None:
            try:
                self._attr_native_value = self.options[int(msg.payload) - 1]
            except IndexError:
                self._attr_native_value = None
        else:
            self._attr_native_value = msg.payload
        # Schedule update ha state
        self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to mqtt."""
        # _LOGGER.debug("async_added_to_hass")
        self._attr_available = False
        await self._subscribe_topic()

    async def async_will_remove_from_hass(self) -> None:
        """Remove entity from hass."""
        _LOGGER.debug("called async_will_remove_from_hass fir %s", self.entity_id)
        await super().async_will_remove_from_hass()
        # Clean up expire triggers
        if self._expiration_trigger:
            self._expiration_trigger()
            self._expiration_trigger = None
            self._attr_available = True


SENSORS: tuple[PrismSensorEntityDescription, ...] = (
    PrismSensorEntityDescription(
        key="current_state_{}",
        topic="{}/state",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "waiting", "charging", "pause"],
        has_entity_name=True,
        translation_key="current_state",
    ),
    PrismSensorEntityDescription(
        key="power_grid_voltage_{}",
        topic="{}/volt",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="power_grid_voltage",
    ),
    PrismSensorEntityDescription(
        key="output_power_{}",
        topic="{}/w",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="output_power",
    ),
    PrismSensorEntityDescription(
        key="output_current_{}",
        topic="{}/amp",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="output_current",
    ),
    PrismSensorEntityDescription(
        key="output_car_current_{}",
        topic="{}/pilot",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="output_car_current",
    ),
    PrismSensorEntityDescription(
        key="current_set_by_user_{}",
        topic="{}/user_amp",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="current_set_by_user",
    ),
    PrismSensorEntityDescription(
        key="session_time_{}",
        topic="{}/session_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="session_time",
    ),
    PrismSensorEntityDescription(
        key="session_output_energy_{}",
        topic="{}/wh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="session_output_energy",
    ),
    PrismSensorEntityDescription(
        key="total_output_energy_{}",
        topic="{}/wh_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="total_output_energy",
    ),
    # FIXME: suspended is not 4 but 7
    PrismSensorEntityDescription(
        key="current_port_mode_{}",
        topic="{}/mode",
        device_class=SensorDeviceClass.ENUM,
        options=["solar", "normal", "paused", "suspended"],
        has_entity_name=True,
        translation_key="current_port_mode",
    ),
)

BASE_SENSORS: tuple[PrismSensorEntityDescription, ...] = (
    PrismSensorEntityDescription(
        key="input_grid_power",
        topic="energy_data/power_grid",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="input_grid_power",
    ),
    PrismSensorEntityDescription(
        key="core_temperature",
        topic="0/info/temperature/core",
        expire_after=86400,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        has_entity_name=True,
        translation_key="core_temperature",
    ),
)

VSENSORS: List[SensorEntityDescription] = [
    SensorEntityDescription(
        key="input_grid_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        has_entity_name=True,
        translation_key="input_grid_energy",
    )
]
