"""Silla Prism for Home Assistant."""

import asyncio
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_MAX_CURRENT,
    CONF_PORTS,
    CONF_SERIAL,
    CONF_TOPIC,
    CONF_VSENSORS,
    DEFAULT_MAX_CURRENT,
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
        vol.Optional(CONF_MAX_CURRENT, default=DEFAULT_MAX_CURRENT): cv.positive_int,
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
        self._max_current: int = DEFAULT_MAX_CURRENT

    async def fetch_device_info(self) -> str | None:
        """Fetech information from MQTT."""
        assert self._topic is not None
        error = None
        event = asyncio.Event()

        async def message_received(msg):
            """Handle new messages on MQTT."""
            _LOGGER.debug("New intent: %s", msg.payload)
            event.set()

        topic1 = self._topic + "0/info/temperature/core"
        _LOGGER.debug("Subscribing test topic1: %s", topic1)
        unsub_topic1 = await mqtt.async_subscribe(self.hass, topic1, message_received)

        topic2 = self._topic + "energy_data/power_grid"
        _LOGGER.debug("Subscribing test topic2: %s", topic2)
        unsub_topic2 = await mqtt.async_subscribe(self.hass, topic2, message_received)

        topic3 = self._topic + "hello"
        _LOGGER.debug("Subscribing test topic3: %s", topic3)
        unsub_topic3 = await mqtt.async_subscribe(self.hass, topic3, message_received)

        try:
            await asyncio.wait_for(event.wait(), 5)
        except TimeoutError:
            error = "Timeout expired"

        unsub_topic1()
        unsub_topic2()
        unsub_topic3()
        return error

    async def _async_validate_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        _LOGGER.debug("Called with user input: %s source: %s", user_input, self.source)

        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            self._ports = entry.data.get(CONF_PORTS, DEFAULT_PORTS)
            self._serial = entry.data.get(CONF_SERIAL, DEFAULT_SERIAL)
            self._vsensors = entry.data.get(CONF_VSENSORS, DEFAULT_VSENSORS)
        else:
            self._ports = user_input[CONF_PORTS]
            self._serial = re.sub(r"[^a-zA-Z0-9]", "", user_input[CONF_SERIAL])
            self._vsensors = user_input[CONF_VSENSORS]

        self._topic = user_input[CONF_TOPIC]
        self._max_current = max(
            min(user_input[CONF_MAX_CURRENT], 32), 6
        )  # clamp between 6 and 32

        return await self._async_try_fetch_device_info()

    async def _async_step_user_base(
        self, user_input: dict[str, Any] | None = None, error: str | None = None
    ) -> ConfigFlowResult:
        _LOGGER.info("Async_step_user %s", DOMAIN)
        if user_input is not None:
            return await self._async_validate_device(user_input)

        errors = {}
        if error is not None:
            errors["base"] = error

        if self.source == SOURCE_RECONFIGURE:
            # We are reconfiguring an existing device
            entry = self._get_reconfigure_entry()
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_TOPIC, default=entry.data[CONF_TOPIC]
                        ): cv.string,
                        vol.Optional(
                            CONF_MAX_CURRENT,
                            default=entry.data.get(
                                CONF_MAX_CURRENT, DEFAULT_MAX_CURRENT
                            ),
                        ): cv.positive_int,
                    }
                ),
                errors=errors,
            )
        # We are creating a new device
        return self.async_show_form(
            step_id="user",
            data_schema=SILLA_PRISM_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        if user_input is not None:
            return await self._async_validate_device(user_input)

        return await self._async_step_user_base()

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
            if self.source == SOURCE_RECONFIGURE:
                return await self._async_update_entry()
            return await self._async_create_entry()

        if self.source == SOURCE_RECONFIGURE:
            return await self.async_step_reconfigure()
        return await self._async_step_user_base(error=error)

    async def _async_create_entry(self) -> ConfigFlowResult:
        config_data = {
            CONF_TOPIC: self._topic,
            CONF_PORTS: self._ports,
            CONF_SERIAL: self._serial,
            CONF_VSENSORS: self._vsensors,
            CONF_MAX_CURRENT: self._max_current,
        }
        return self.async_create_entry(
            title="SillaPrism",
            data=config_data,
        )

    async def _async_update_entry(self) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()

        config_data = {
            CONF_TOPIC: self._topic,
            CONF_PORTS: entry.data[CONF_PORTS],
            CONF_SERIAL: entry.data[CONF_SERIAL],
            CONF_VSENSORS: entry.data[CONF_VSENSORS],
            CONF_MAX_CURRENT: self._max_current,
        }
        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(),
            data_updates=config_data,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.info("Async_step_user %s", DOMAIN)
        return await self._async_step_user_base(user_input=user_input)
