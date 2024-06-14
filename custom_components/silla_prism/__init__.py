"""silla_prism_async."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import CONF_TOPIC, DOMAIN
from .domain_data import DomainData
from .entry_data import RuntimeEntryData

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Silla Prism component."""
    _LOGGER.debug("async_setup_entry for Silla Prism")
    _topic = entry.data[CONF_TOPIC]
    domain_data = DomainData.get(hass)
    entry_data = RuntimeEntryData(topic=_topic)
    domain_data.set_entry_data(entry, entry_data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
