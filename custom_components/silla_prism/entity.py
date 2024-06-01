"""Contains sensors exposed by the Prism integration."""

from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from .const import DOMAIN


class PrismBaseEntity(Entity):
    """A base Entity that is registered under a Prism device."""

    def __init__(self, base_topic: str, description: EntityDescription) -> None:
        """Initialize the device info and set the update coordinator."""
        self._topic = base_topic + "1/" + description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "SillaPrism001")},
            name="Prism",
            manufacturer="Silla",
            model="Prism",
        )
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_unique_id = "prism_" + description.key + "_001"
        self.entity_description = description


class PrismEntity(Entity):
    """A base Entity that is registered under a Prism device."""

    def __init__(self, base_topic: str, description: EntityDescription) -> None:
        """Initialize the device info and set the update coordinator."""
        if "energy_data" in description.key:
            self._topic = base_topic + description.key
        else:
            self._topic = base_topic + "1/" + description.key
        self.entity_id = "sensor.prism_" + description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "SillaPrism001")},
            name="Prism",
            manufacturer="Silla",
            model="Prism",
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = "prism_" + description.key + "_001"
        self.entity_description = description
