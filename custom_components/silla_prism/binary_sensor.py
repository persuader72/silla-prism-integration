"""Contains numbers configurations for Prism wallbox integration."""

from datetime import datetime
import logging
from typing import FrozenSet, override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

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
    _LOGGER.debug("async_setup_entry for binary sensors: %s", entry_data)
    binsens = [
        PrismBinarySensor(entry_data, description) for description in BINARYSENSORS
    ]
    evsens = [
        PrismEventBinarySensor(entry_data, description) for description in EVENTSENSORS
    ]
    async_add_entities(binsens + evsens)


class PrismBinarySensorEntityDescription(
    BinarySensorEntityDescription, frozen_or_thawed=True
):
    """A class that describes prism binary sensor entities."""

    expire_after: float = 600
    topic: str = None


class PrismEventBinarySensorEntityDescription(
    PrismBinarySensorEntityDescription, frozen_or_thawed=True
):
    """A class that describes prism button event sensor entities."""

    sequence: FrozenSet[int] = (1,)


class PrismBinarySensor(PrismBaseEntity, BinarySensorEntity):
    """Prism binary sensor entity."""

    entity_description: PrismBinarySensorEntityDescription

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismBinarySensorEntityDescription,
    ) -> None:
        """Init Prism select."""
        super().__init__(entry_data, "binary_sensor", description)
        self._attr_is_on = False

    @override
    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        self.schedule_expiration_callback()

        # Handle online presence
        if not self._attr_is_on:
            self._attr_is_on = True
            self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        """Subscribe to mqtt."""
        await self._subscribe_topic()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from mqtt."""
        _LOGGER.debug("async_will_remove_from_hass")
        await super().async_will_remove_from_hass()
        self.cleanup_expiration_trigger()
        if self._unsubscribe is not None:
            await self._unsubscribe_topic()


class PrismEventBinarySensor(PrismBinarySensor):
    """Prism button event sensor entity"""

    entity_description: PrismEventBinarySensorEntityDescription

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismEventBinarySensorEntityDescription,
    ) -> None:
        """Init Prism event binary sensor."""
        super().__init__(entry_data, description)
        self._sequence: FrozenSet[int] = description.sequence

    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        self.schedule_expiration_callback()

        # Handle input touch button
        _seq = msg.payload.split(",")
        try:
            _seq_int = [int(x) for x in _seq]
            if len(_seq_int) == len(self._sequence):
                for i, s in enumerate(_seq_int):
                    if self._sequence[i] != s:
                        break
            self._attr_is_on = True
            self._expiration_trigger = async_call_later(
                self.hass, 2.0, self._restore_value
            )
            self.schedule_update_ha_state()
        except ValueError:
            pass

    @callback
    def _restore_value(self, *_: datetime) -> None:
        """Triggered when value is expired."""
        _LOGGER.debug("entity _value_is_expired for topic %s", self._topic)
        self._expiration_trigger = None
        self._attr_is_on = False
        self.async_write_ha_state()


BINARYSENSORS = [
    PrismBinarySensorEntityDescription(
        key="online",
        topic="energy_data/power_grid",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        has_entity_name=True,
        translation_key="online",
        expire_after=0,
    ),
]

EVENTSENSORS = [
    PrismEventBinarySensorEntityDescription(
        key="touch_sigle",
        topic="1/input/touch",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.MOTION,
        has_entity_name=True,
        sequence=(1,),
        translation_key="touch_sigle",
        expire_after=0,
    ),
    PrismEventBinarySensorEntityDescription(
        key="touch_double",
        topic="1/input/touch",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.MOTION,
        has_entity_name=True,
        sequence=(
            1,
            1,
        ),
        translation_key="touch_double",
        expire_after=0,
    ),
    PrismEventBinarySensorEntityDescription(
        key="touch_long",
        topic="1/input/touch",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.MOTION,
        has_entity_name=True,
        sequence=(3,),
        translation_key="touch_long",
        expire_after=0,
    ),
]
