"""Contains sensors exposed by the Prism integration."""

from datetime import datetime
import logging

from homeassistant.const import EntityCategory
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PrismBaseEntityDescription:
    """A class that describes base prism entities."""

    expire_after: float = 600


class PrismBaseEntity(Entity):
    """A base Entity that is registered under a Prism device."""

    _expire_after: int | None
    _expiration_trigger: CALLBACK_TYPE | None = None

    def __init__(
        self, base_topic: str, description: PrismBaseEntityDescription
    ) -> None:
        """Initialize the device info and set the update coordinator."""
        if "energy_data" in description.key:
            self._topic = base_topic + description.key
        else:
            self._topic = base_topic + "1/" + description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "SillaPrism001")},
            name="Prism",
            manufacturer="Silla",
            model="Prism",
        )
        self._attr_unique_id = "prism_" + description.key + "_001"
        self.entity_description = description

        # TODO: Put this in config
        self._expire_after = description.expire_after
        # Init expire proceudre
        if self._expire_after is not None and self._expire_after > 0:
            self._attr_available = False

    @callback
    def _value_is_expired(self, *_: datetime) -> None:
        """Triggered when value is expired."""
        _LOGGER.debug("entity _value_is_expired for topic %s", self._topic)
        self._expiration_trigger = None
        self._attr_available = False
        self.async_write_ha_state()

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


class PrismEntity(Entity):
    """A base Entity that is registered under a Prism device."""

    def __init__(self, base_topic: str, description: EntityDescription) -> None:
        """Initialize the device info and set the update coordinator."""
        if "energy_data" in description.key:
            self._topic = base_topic + description.key
        else:
            self._topic = base_topic + "1/" + description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "SillaPrism001")},
            name="Prism",
            manufacturer="Silla",
            model="Prism",
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = "prism_" + description.key + "_001"
        self.entity_description = description
