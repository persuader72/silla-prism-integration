"""Silla Prism button entity module."""

from collections.abc import Coroutine
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BUTTON_DOMAIN
from .domain_data import DomainData
from .entity import _get_entity_id, _get_unique_id
from .entry_data import RuntimeEntryData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add entities for passed config_entry in HA."""
    entry_data: RuntimeEntryData = DomainData.get(hass).get_entry_data(entry)

    ports = entry_data.ports
    selects = []
    for port in range(1, ports + 1):
        selects.extend(
            [PrismCommand(entry_data, description, port) for description in BUTTONS]
        )
    async_add_entities(selects)


class PrismCommandEntityDescription(ButtonEntityDescription, frozen_or_thawed=True):
    """A class that describes prism binary sensor entities."""

    command: str = None
    parameter: str = None


class PrismCommand(ButtonEntity):
    """A Command entity for Prism wallbox devices."""

    entity_description: PrismCommandEntityDescription

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismCommandEntityDescription,
        port: int,
    ) -> None:
        """Init Prism select."""
        super().__init__()
        self._base_topic = entry_data.topic
        self._port = port
        self._attr_device_info = self._get_device(entry_data, port)
        self.entity_description = description
        self.entity_id = _get_entity_id(
            entry_data.serial, BUTTON_DOMAIN, description.key
        )
        self._attr_unique_id = _get_unique_id(entry_data.serial, description.key)

    async def async_added_to_hass(self) -> Coroutine[Any, Any, None]:
        """Subscribe to mqtt."""
        return super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> Coroutine[Any, Any, None]:
        """Unsubscribe from mqtt."""
        await super().async_will_remove_from_hass()

    async def async_press(self) -> None:
        """Press the button."""
        await mqtt.async_publish(
            self.hass,
            self._get_topic(),
            self.entity_description.parameter,
        )

    def _get_device(self, entry_data: RuntimeEntryData, port: int) -> DeviceInfo:
        """Get the device info."""
        ismultiport = entry_data.ports > 1
        if not ismultiport:
            return entry_data.devices[0]
        return entry_data.devices[port]

    def _get_topic(self) -> str:
        """Get the topic."""
        return (
            f"{self._base_topic}{self._port}/command/{self.entity_description.command}"
        )


BUTTONS: tuple[PrismCommandEntityDescription, ...] = (
    PrismCommandEntityDescription(
        key="set_mode_traps_auth",
        has_entity_name=True,
        translation_key="set_mode_traps_auth",
        command="set_mode_traps",
        device_class=ButtonDeviceClass.IDENTIFY,
        parameter="+auth",
    ),
    PrismCommandEntityDescription(
        key="set_mode_traps_noauth",
        has_entity_name=True,
        translation_key="set_mode_traps_noauth",
        command="set_mode_traps",
        device_class=ButtonDeviceClass.IDENTIFY,
        parameter="-auth",
    ),
)
