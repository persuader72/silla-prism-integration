"""Silla Prism for Home Assistant."""

import asyncio
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_PORTS,
    CONF_SERIAL,
    CONF_TOPIC,
    CONF_VSENSORS,
    DEFAULT_PORTS,
    DEFAULT_SERIAL,
    DEFAULT_TOPIC,
    DEFAULT_VSENSORS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SILLA_PRISM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOPIC, default=DEFAULT_TOPIC): cv.string,
        vol.Required(CONF_PORTS, default=DEFAULT_PORTS): cv.positive_int,
        vol.Optional(CONF_SERIAL, default=DEFAULT_SERIAL): cv.string,
        vol.Optional(CONF_VSENSORS, default=DEFAULT_VSENSORS): cv.boolean,
    }
)


class SillaPrismConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Silla Prism config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._topic: str | None = DEFAULT_TOPIC
        self._ports: int = DEFAULT_PORTS
        self._vsensors: bool = DEFAULT_VSENSORS
        self._serial: str = DEFAULT_SERIAL

    async def fetch_device_info(self) -> str | None:
        """Fetech information from MQTT."""
        assert self._topic is not None
        error = None
        event = asyncio.Event()

        async def message_received(msg):
            """Handle new messages on MQTT."""
            _LOGGER.debug("New intent: %s", msg.payload)
            event.set()

        test_topic = self._topic + "0/info/temperature/core"
        _LOGGER.debug("Subscribing test topic: %s", test_topic)
        await mqtt.async_subscribe(self.hass, test_topic, message_received)
        try:
            await asyncio.wait_for(event.wait(), 5)
        except TimeoutError:
            error = "Timeout expired"

        return error

    async def _async_step_user_base(
        self, user_input: dict[str, Any] | None = None, error: str | None = None
    ) -> ConfigFlowResult:
        _LOGGER.info("Async_step_user %s", DOMAIN)
        if user_input is not None:
            _LOGGER.debug("Called with user input: %s", user_input)
            self._topic = user_input[CONF_TOPIC]
            self._ports = user_input[CONF_PORTS]
            self._serial = re.sub(r"[^a-zA-Z0-9]", "", user_input[CONF_SERIAL])
            self._vsensors = user_input[CONF_VSENSORS]
            return await self._async_try_fetch_device_info()

        errors = {}
        if error is not None:
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=SILLA_PRISM_SCHEMA,
            errors=errors,
        )

    async def _async_try_fetch_device_info(self) -> ConfigFlowResult:
        """Try to fetch device info and return any errors."""
        error = None

        # Make sure MQTT integration is enabled and the client is available
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            error = "MQTT integration is not available"
            _LOGGER.error(error)

        if error is None:
            error = await self.fetch_device_info()

        if error is None:
            return await self._async_get_entry()

        return await self._async_step_user_base(error=error)

    async def _async_get_entry(self) -> ConfigFlowResult:
        config_data = {
            CONF_TOPIC: self._topic,
            CONF_PORTS: self._ports,
            CONF_SERIAL: self._serial,
            CONF_VSENSORS: self._vsensors,
        }
        return self.async_create_entry(
            title="SillaPrism",
            data=config_data,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.info("Async_step_user %s", DOMAIN)
        return await self._async_step_user_base(user_input=user_input)
