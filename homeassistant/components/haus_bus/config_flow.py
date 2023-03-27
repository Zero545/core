"""Config flow for hausbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    selector,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_GATEWAY_TYPE = "gateway_type"
TYPE_IP_GATEWAY = "ip_gateway"
TYPE_RS_485_ADAPTER = "rs_485"
CONF_DEVICE_PATH = "device_path"

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GATEWAY_TYPE): selector(
            {
                "select": {
                    "options": [TYPE_IP_GATEWAY, TYPE_RS_485_ADAPTER],
                    "translation_key": CONF_GATEWAY_TYPE,
                }
            }
        )
    }
)
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

    async def authenticate_ip_gateway(self, ip: str) -> bool:
        """Test if we can authenticate with the ip gateway."""
        # TODO validate the data can be used to set up a connection.
        return True

    async def authenticate_usb_rs485(self, path: str) -> bool:
        """Test if we can authenticate with the USB RS-485 adapter."""
        # TODO validate the data can be used to set up a connection.
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = HausBusHub(data[CONF_GATEWAY_TYPE])

    if hub.host_type == TYPE_IP_GATEWAY:
        if not await hub.authenticate_ip_gateway(data[CONF_IP_ADDRESS]):
            raise InvalidAuth

    if hub.host_type == TYPE_RS_485_ADAPTER:
        if not await hub.authenticate_usb_rs485(data[CONF_DEVICE_PATH]):
            raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hausbus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_GATEWAY_TYPE] == TYPE_IP_GATEWAY:
                return await self.async_step_ip_gateway()

            if user_input[CONF_GATEWAY_TYPE] == TYPE_RS_485_ADAPTER:
                return await self.async_step_rs_485_adapter()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_ip_gateway(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_GATEWAY_TYPE] = TYPE_IP_GATEWAY
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Haus-Bus", data=user_input)

        return self.async_show_form(
            step_id="ip_gateway", data_schema=STEP_IP_GATEWAY_SCHEMA, errors=errors
        )

    async def async_step_rs_485_adapter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_GATEWAY_TYPE] = TYPE_RS_485_ADAPTER
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Haus-Bus", data=user_input)

        return self.async_show_form(
            step_id="rs_485_adapter", data_schema=STEP_USB_RS485_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
