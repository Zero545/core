"""Config flow for hausbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_GATEWAY_TYPE = "gateway_type"
TYPE_IP_GATEWAY = "ip_gateway"
TYPE_RS_485_ADAPTER = "rs_485"
CONF_DEVICE_PATH = "device_path"

STEP_USER_SCHEMA = vol.Schema({})

STEP_IP_GATEWAY_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_IP_ADDRESS, description={"suggested_value": "127.0.0.1"}
        ): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL, autocomplete="url")
        )
    }
)
STEP_USB_RS485_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_DEVICE_PATH, description={"suggested_value": "/dev/ttyUSB0"}
        ): str
    }
)


class HausBusHub:
    """Haus-Bus config flow class."""

    def __init__(self, host_type: str) -> None:
        """Initialize."""
        self.host_type = host_type


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hausbus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="Haus-Bus", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
