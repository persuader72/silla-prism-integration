"""Contains numbers configurations for Prism wallbox integration."""

from datetime import datetime
import logging
from typing import override

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

from .const import BINARY_SENSOR_DOMAIN
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
        PrismBinarySensor(entry_data, description, 0)
        for description in BASE_BINARYSENSORS
    ]

    ports = entry_data.ports
    for port in range(1, ports + 1):
        binsens.extend(
            [
                PrismErrorBinarySensor(entry_data, description, port)
                for description in ERROR_BINARYSENSORS
            ]
        )
        binsens.extend(
            [
                PrismEventBinarySensor(entry_data, description, port)
                for description in EVENTS_BINARYSENSORS
            ]
        )

    async_add_entities(binsens)


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

    sequence: frozenset[int] = (1,)


class PrismBinarySensor(PrismBaseEntity, BinarySensorEntity):
    """Prism binary sensor entity."""

    entity_description: PrismBinarySensorEntityDescription

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismBinarySensorEntityDescription,
        port: int,
    ) -> None:
        """Init Prism select."""
        _LOGGER.debug("PrismBinarySensor.__init__: %s", entry_data)
        ismultiport = entry_data.ports > 1
        if not ismultiport:
            device = entry_data.devices[0]
        else:
            device = entry_data.devices[port]
        super().__init__(entry_data, BINARY_SENSOR_DOMAIN, description, device)
        self._attr_is_on = False

    @override
    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        self.schedule_expiration_callback()

        # Handle online presence
        if not self._attr_is_on:
            self._attr_is_on = True
            self.schedule_update_ha_state()

    @override
    def _value_is_expired(self):
        """Triggered when value is expired."""
        self._attr_is_on = False


class PrismErrorBinarySensor(PrismBinarySensor):
    """Prism error binary sensor entity."""

    entity_description: PrismBinarySensorEntityDescription

    def _get_description(
        self,
        port: int,
        mulitport: bool,
        description: PrismBinarySensorEntityDescription,
    ) -> PrismBinarySensorEntityDescription:
        if port == 0:
            return description
        if mulitport:
            return PrismBinarySensorEntityDescription(
                key=description.key.format(port),
                topic=description.topic.format(port),
                entity_category=description.entity_category,
                device_class=description.device_class,
                has_entity_name=description.has_entity_name,
                translation_key=description.translation_key,
                expire_after=description.expire_after,
            )
        return PrismBinarySensorEntityDescription(
            key=description.key[:-3],
            topic=description.topic.format(port),
            entity_category=description.entity_category,
            device_class=description.device_class,
            has_entity_name=description.has_entity_name,
            translation_key=description.translation_key,
            expire_after=description.expire_after,
        )

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismBinarySensorEntityDescription,
        port: int,
    ) -> None:
        """Init Prism error binary sensor."""
        ismultiport = entry_data.ports > 1
        super().__init__(
            entry_data, self._get_description(port, ismultiport, description), port
        )

    @override
    def _message_received(self, msg) -> None:
        """Update the error sensor with the most recent event."""
        self.schedule_expiration_callback()

        try:
            error_value = int(msg.payload)
            # OFF when value is 0, ON when different from 0
            self._attr_is_on = error_value != 0
        except (ValueError, TypeError):
            # If we can't parse the value, assume there's an error
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


class PrismEventBinarySensor(PrismBinarySensor):
    """Prism button event sensor entity."""

    entity_description: PrismEventBinarySensorEntityDescription

    def _get_description(
        self,
        port: int,
        mulitport: bool,
        description: PrismEventBinarySensorEntityDescription,
    ) -> PrismEventBinarySensorEntityDescription:
        if port == 0:
            return description
        if mulitport:
            return PrismEventBinarySensorEntityDescription(
                key=description.key.format(port),
                topic=description.topic.format(port),
                entity_category=description.entity_category,
                device_class=description.device_class,
                has_entity_name=description.has_entity_name,
                sequence=description.sequence,
                translation_key=description.translation_key,
                expire_after=description.expire_after,
            )
        return PrismEventBinarySensorEntityDescription(
            key=description.key[:-3],
            topic=description.topic.format(port),
            entity_category=description.entity_category,
            device_class=description.device_class,
            has_entity_name=description.has_entity_name,
            sequence=description.sequence,
            translation_key=description.translation_key,
            expire_after=description.expire_after,
        )

    def __init__(
        self,
        entry_data: RuntimeEntryData,
        description: PrismEventBinarySensorEntityDescription,
        port: int,
    ) -> None:
        """Init Prism event binary sensor."""
        ismultiport = entry_data.ports > 1
        super().__init__(
            entry_data, self._get_description(port, ismultiport, description), port
        )
        self._sequence: frozenset[int] = description.sequence

    def _message_received(self, msg) -> None:
        """Update the sensor with the most recent event."""
        self.schedule_expiration_callback()

        # Handle input touch button
        _seq = msg.payload.split(",")
        try:
            _seq_int = tuple(int(x) for x in _seq)
            if _seq_int == self._sequence:
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


BASE_BINARYSENSORS = [
    PrismBinarySensorEntityDescription(
        key="online",
        topic="1/volt",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        has_entity_name=True,
        translation_key="online",
        expire_after=150,
    ),
]

ERROR_BINARYSENSORS = [
    PrismBinarySensorEntityDescription(
        key="error_{}",
        topic="{}/error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        has_entity_name=True,
        translation_key="error",
    ),
]

EVENTS_BINARYSENSORS = [
    PrismEventBinarySensorEntityDescription(
        key="touch_sigle_{}",
        topic="{}/input/touch",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.MOTION,
        has_entity_name=True,
        sequence=(1,),
        translation_key="touch_sigle",
        expire_after=0,
    ),
    PrismEventBinarySensorEntityDescription(
        key="touch_double_{}",
        topic="{}/input/touch",
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
        key="touch_long_{}",
        topic="{}/input/touch",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.MOTION,
        has_entity_name=True,
        sequence=(3,),
        translation_key="touch_long",
        expire_after=0,
    ),
]
