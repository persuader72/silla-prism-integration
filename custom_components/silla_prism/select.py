"""Silla Prism select entity module."""

from dataclasses import dataclass
import logging

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
    selects = [
        PrismSelect(hass, entry_data.topic, description) for description in SELECTS
    ]
    async_add_entities(selects)


@dataclass(frozen=True, kw_only=True)
class PrismSelectEntityDescription(SelectEntityDescription):
    """A class that describes prism binary sensor entities."""

    expire_after: float = 600


class PrismSelect(PrismBaseEntity, SelectEntity):
    """A Select for Prism wallbox devices."""

    entity_description: PrismSelectEntityDescription

    def __init__(
        self,
        hass: HomeAssistant,
        base_topic: str,
        description: PrismSelectEntityDescription,
    ) -> None:
        """Init Prism select."""
        super().__init__(base_topic, description)
        self._hass: HomeAssistant = hass
        self._attr_current_option = "normal"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(
            "async_select_option: %s(%d)", option, self.options.index(option) + 1
        )
        await mqtt.async_publish(
            self._hass, self._topic, self.options.index(option) + 1
        )


SELECTS: tuple[PrismSelectEntityDescription, ...] = (
    PrismSelectEntityDescription(
        key="set_mode",
        entity_category=EntityCategory.CONFIG,
        options=["solar", "normal", "paused"],
        has_entity_name=True,
        translation_key="set_mode",
    ),
)
