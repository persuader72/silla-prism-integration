"""Contains sensors exposed by the Prism integration."""

from datetime import datetime
import logging

from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.event import async_call_later
from homeassistant.components import mqtt

from .entry_data import RuntimeEntryData

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
# ENTITY_ID_SENSOR_FORMAT = "{}." + DOMAIN + "_{}"


def _get_unique_id(serial: str, key: str) -> str:
    """Get a unique entity id."""
    if serial == "":
        return "prism_" + key + "_001"
    else:
        return "prism_{}_{}".format(serial, key)


def _get_entity_id(serial: str, entity_type: str, key: str) -> str:
    """Get a entity id."""
    if serial == "":
        return "{}.{}_{}".format(entity_type, DOMAIN, key)
    else:
        return "{}.{}_{}_{}".format(entity_type, DOMAIN, serial, key)


class PrismBaseEntityDescription(EntityDescription, frozen_or_thawed=True):
    """A class that describes base prism entities."""

    expire_after: float = 600
    topic: str = None


class PrismBaseEntity(Entity):
    """A base Entity that is registered under a Prism device."""

    _expire_after: int | None
    _expiration_trigger: CALLBACK_TYPE | None = None
    _attr_should_poll = False

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        sensor_domain: str,
        description: PrismBaseEntityDescription,
        device: DeviceInfo
    ) -> None:
        """Initialize the device info and set the update coordinator."""
        # Create device instance
        self._attr_device_info = device
        self.entity_description = description
        # _LOGGER.debug("sensor entity %s", description.key)
        # Preload attributes
        self.entity_id = _get_entity_id(entry_data.serial, sensor_domain, description.key)
        # _LOGGER.debug("entity id %s", self.entity_id)
        self._attr_unique_id = _get_unique_id(entry_data.serial, description.key)
        # _LOGGER.debug("entity unique id %s", self._attr_unique_id)
        self._topic = entry_data.topic + description.topic
        # TODO: Put this in config
        self._expire_after = description.expire_after
        # Init expire proceudre
        if self._expire_after is not None and self._expire_after > 0:
            self._attr_available = False
        self._unsubscribe = None

    @callback
    def _value_is_expired(self, *_: datetime) -> None:
        """Triggered when value is expired."""
        _LOGGER.debug("entity _value_is_expired for topic %s", self._topic)
        self._expiration_trigger = None
        self._attr_available = False
        self.async_write_ha_state()

    async def _subscribe_topic(self):
        """Subscribe to mqtt topic."""
        _LOGGER.debug("_subscribe_topic: %s", self._topic)
        self._unsubscribe = await mqtt.async_subscribe(
            self.hass,
            self._topic, 
            self.message_received
        )

    def _message_received(self, msg) -> None:
        """Change the selected option."""
        raise NotImplementedError

    def message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        self.hass.loop.call_soon_threadsafe(self._message_received, msg)

    async def _unsubscribe_topic(self):
        """Unsubscribe to mqtt topic."""
        _LOGGER.debug("_unsubscribe_topic: %s", self._topic)
        if self._unsubscribe is not None:
            await self._unsubscribe()

    def schedule_expiration_callback(self) -> None:
        """When self._expire_after is set, and we receive a message, assume device is not expired since it has to be to receive the message."""
        if self._expire_after is not None and self._expire_after > 0:
            self._attr_available = True
            # Reset old trigger
            if self._expiration_trigger:
                self._expiration_trigger()
            # Set new trigger
            self._expiration_trigger = async_call_later(
                self.hass, self._expire_after, self._value_is_expired
            )

    def cleanup_expiration_trigger(self) -> None:
        """Clean up expiration triggers."""
        if self._expiration_trigger:
            self._expiration_trigger()
            self._expiration_trigger = None
            self._attr_available = True
