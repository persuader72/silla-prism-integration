"""silla_prism_async."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_TOPIC, CONF_PORTS, CONF_SERIAL, CONF_VSENSORS, DOMAIN
from .domain_data import DomainData
from .entry_data import RuntimeEntryData

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]

def _get_device_identifier(port: int, serial: str) -> str:
    if serial == "" and port == 0:
        return "SillaPrism001"
    elif serial == "":
        return "PrismPort{}".format(port)
    else:
        return "Prism_Port{}_Serial{}".format(port, serial)


def _get_device_name(port: int, serial: str) -> str:
    if serial == "" and port == 0:
        return "Prism"
    elif serial == "":
        return "Prism Port {}".format(port)
    else:
        return "Prism Serial {} Port {}".format(serial, port)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Silla Prism component."""
    _LOGGER.debug("async_setup_entry for Silla Prism")
    _topic = entry.data[CONF_TOPIC]
    _ports = entry.data.get(CONF_PORTS, 1)
    _serial = entry.data.get(CONF_SERIAL, "")
    _vsensors = entry.data.get(CONF_VSENSORS, True)
    domain_data = DomainData.get(hass)
    _LOGGER.debug("entry.data: %s %s %s %s", _topic, _ports, _serial, _vsensors)

    _devices_info = []

    _devices_info.append(DeviceInfo(
        identifiers={(DOMAIN, _get_device_identifier(0, _serial))},
        name=_get_device_name(0, _serial),
        manufacturer="Silla",
        model="Prism",
        serial_number=_serial,
    ))

    for port in range(1, _ports+1):
        _devices_info.append(DeviceInfo(
            identifiers={(DOMAIN, _get_device_identifier(port, _serial))},
            name=_get_device_name(port, _serial),
            manufacturer="Silla",
            model="Prism",
            serial_number=_serial,
        ))

    entry_data = RuntimeEntryData(topic=_topic, ports=_ports, serial=_serial, vsensors=_vsensors, devices=_devices_info)
    domain_data.set_entry_data(entry, entry_data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
