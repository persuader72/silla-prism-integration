"""Silla Prism select entity module."""

import logging
from typing import override

from homeassistant.components import mqtt
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .domain_data import DomainData
from .entity import PrismBaseEntity
from .entry_data import RuntimeEntryData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add entities for passed config_entry in HA."""
    entry_data: RuntimeEntryData = DomainData.get(hass).get_entry_data(entry)
    _LOGGER.debug("async_setup_entry for sensors: %s", entry_data)

    ports = entry_data.ports
    selects = []
    for port in range(1, ports+1):
        for description in SELECTS:
            selects.append(PrismSelect(entry_data, description, port))
    async_add_entities(selects)


class PrismSelectEntityDescription(SelectEntityDescription, frozen_or_thawed=True):
    """A class that describes prism binary sensor entities."""

    expire_after: float = 0
    topic: str = None
    topic_out: str = None


class PrismSelect(PrismBaseEntity, SelectEntity):
    """A Select for Prism wallbox devices."""

    entity_description: PrismSelectEntityDescription

    def description(self, port: int, mulitport: bool, description: PrismSelectEntityDescription) -> PrismSelectEntityDescription:
        if mulitport:
            return PrismSelectEntityDescription(
                key=description.key.format(port),
                topic=description.topic.format(port),
                entity_category=description.entity_category,
                device_class=description.device_class,
                options=description.options,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
                topic_out=description.topic_out.format(port),
            )
        else:
            return PrismSelectEntityDescription(
                key=description.key[0:-3],
                topic=description.topic.format(port),
                entity_category=description.entity_category,
                device_class=description.device_class,
                options=description.options,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
                topic_out=description.topic_out.format(port),
            )
        
    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismSelectEntityDescription,
        port: int
    ) -> None:
        """Init Prism select."""
        ismultiport = entry_data.ports > 1
        if not ismultiport:
            device = entry_data.devices[0]
        else:
            device = entry_data.devices[port]
        super().__init__(entry_data, "select", self.description(port, ismultiport, description), device)
        if port == 0:
            self._topic_out = entry_data.topic + description.topic_out
        else:
            self._topic_out = entry_data.topic + description.topic_out.format(port)
        self._attr_current_option = "normal"

    @override
    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        try:
            _sel = int(msg.payload) - 1
            if _sel >= 0 and _sel < len(self.options):
                self._attr_current_option = self.options[_sel]
                self.schedule_update_ha_state()
        except ValueError:
            pass

    async def async_added_to_hass(self) -> None:
        """Subscribe to mqtt."""
        await self._subscribe_topic()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from mqtt."""
        _LOGGER.debug("async_will_remove_from_hass key:%s", self.entity_description.key)
        await super().async_will_remove_from_hass()
        self.cleanup_expiration_trigger()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(
            "async_select_option: key:%s topic:%s %s(%d)",
            self.entity_description.key,
            self._topic_out,
            option,
            self.options.index(option) + 1,
        )
        await mqtt.async_publish(
            self.hass, self._topic_out, self.options.index(option) + 1
        )


SELECTS: tuple[PrismSelectEntityDescription, ...] = (
    PrismSelectEntityDescription(
        key="set_mode_{}",
        topic="{}/command/set_mode",
        topic_out="{}/command/set_mode",
        entity_category=EntityCategory.CONFIG,
        options=["solar", "normal", "paused"],
        has_entity_name=True,
        translation_key="set_port_mode",
    ),
)
# type: ignore
