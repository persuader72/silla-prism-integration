"""Contains numbers configurations for Prism wallbox integration."""

import logging
from typing import override

from homeassistant.components import mqtt
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.components.number.const import NumberDeviceClass, NumberMode
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
    _LOGGER.debug("async_setup_entry for numbers: %s", entry_data)

    ports = entry_data.ports
    numbers = []

    for port in range(1, ports+1):
        for description in NUMBERS:
            numbers.append(PrismNumber(entry_data, description, port))

    async_add_entities(numbers)


class PrismNumberEntityDescription(NumberEntityDescription, frozen_or_thawed=True):
    """A class that describes prism binary sensor entities."""

    expire_after: float = 0
    topic: str = None
    topic_out: str = None


class PrismNumber(PrismBaseEntity, NumberEntity):
    """Prism number entity."""

    entity_description: PrismNumberEntityDescription

    def description(self, port: int, mulitport: bool, description: PrismNumberEntityDescription) -> PrismNumberEntityDescription:
        if mulitport:
            return PrismNumberEntityDescription(
                key=description.key.format(port),
                topic=description.topic.format(port),
                entity_category=description.entity_category,
                device_class=description.device_class,
                native_min_value=description.native_min_value,
                native_max_value=description.native_max_value,
                mode=description.mode,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
            )
        else:
            return PrismNumberEntityDescription(
                key=description.key[:-3],
                topic=description.topic.format(port),
                entity_category=description.entity_category,
                device_class=description.device_class,
                native_min_value=description.native_min_value,
                native_max_value=description.native_max_value,
                mode=description.mode,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
            )

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismNumberEntityDescription,
        port: int
    ) -> None:
        """Init Prism select."""
        ismultiport = entry_data.ports > 1
        if not ismultiport:
            device = entry_data.devices[0]
        else:
            device = entry_data.devices[port]
        super().__init__(entry_data, "number", self.description(port, ismultiport, description), device)
        self._topic_out = entry_data.topic + description.topic_out
        self._attr_native_value = self.native_min_value

    @override
    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        self._attr_native_value = msg.payload
        self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to mqtt."""
        await self._subscribe_topic()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from mqtt."""
        _LOGGER.debug("async_will_remove_from_hass key:%s", self.entity_description.key)
        await super().async_will_remove_from_hass()
        self.cleanup_expiration_trigger()
        if self._unsubscribe is not None:
            await self._unsubscribe_topic()

    def set_native_value(self, _: float) -> None:
        return NotImplementedError

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        _LOGGER.debug(
            "async_set_native_value key:%s topic:%s value:%f",
            self.entity_description.key,
            self._topic_out,
            value,
        )
        await mqtt.async_publish(self.hass, self._topic_out, int(value))


NUMBERS: tuple[PrismNumberEntityDescription, ...] = (
    PrismNumberEntityDescription(
        key="set_max_current_{}",
        topic="{}/user_amp",
        topic_out="{}/command/set_current_user",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.CURRENT,
        native_min_value=6,
        native_max_value=16,
        mode=NumberMode.BOX,
        has_entity_name=True,
        translation_key="set_max_current",
    ),
    PrismNumberEntityDescription(
        key="set_current_limit_{}",
        topic="{}/pilot",
        topic_out="{}/command/set_current_limit",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.CURRENT,
        native_min_value=6,
        native_max_value=16,
        has_entity_name=True,
        translation_key="set_current_limit",
    ),
)
