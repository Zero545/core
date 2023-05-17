"""Test the hausbus config flow."""
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.haus_bus.config_flow import (
    CONF_DEVICE_PATH,
    CONF_GATEWAY_TYPE,
    CONF_IP_ADDRESS,
    TYPE_IP_GATEWAY,
    TYPE_RS_485_ADAPTER,
    InvalidAuth,
)
from homeassistant.components.haus_bus.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .helpers import create_configuration

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


async def test_form_ip_gateway(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form and create a ip gateway configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await create_configuration(hass, result, TYPE_IP_GATEWAY, "127.0.0.1")

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Haus-Bus"
    assert result2["data"] == {
        CONF_GATEWAY_TYPE: TYPE_IP_GATEWAY,
        CONF_IP_ADDRESS: "127.0.0.1",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_rs485_gateway(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form and create a rs485 configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await create_configuration(
        hass, result, TYPE_RS_485_ADAPTER, "/dev/ttyUSB0"
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Haus-Bus"
    assert result2["data"] == {
        CONF_GATEWAY_TYPE: TYPE_RS_485_ADAPTER,
        CONF_DEVICE_PATH: "/dev/ttyUSB0",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect_ip_gateway(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error for ip gateway."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.haus_bus.config_flow.HausBusHub.verify_ip_gateway",
        return_value=False,
    ):
        result2 = await create_configuration(hass, result, TYPE_IP_GATEWAY, "127.0.0.1")

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_cannot_connect_rs485_gateway(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error for rs485 adapter."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.haus_bus.config_flow.HausBusHub.verify_usb_rs485",
        return_value=False,
    ):
        result2 = await create_configuration(
            hass, result, TYPE_RS_485_ADAPTER, "/dev/ttyUSB0"
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth_ip_gateway(hass: HomeAssistant) -> None:
    """Test we handle invalid auth error while configuring ip gateway."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.haus_bus.config_flow.validate_input",
        side_effect=InvalidAuth,
    ):
        result2 = await create_configuration(hass, result, TYPE_IP_GATEWAY, "127.0.0.1")

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_unknown_error_ip_gateway(hass: HomeAssistant) -> None:
    """Test we handle unknown errors while configuring ip gateway."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.haus_bus.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await create_configuration(hass, result, TYPE_IP_GATEWAY, "127.0.0.1")

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_invalid_auth_rs485(hass: HomeAssistant) -> None:
    """Test we handle invalid auth error while configuring rs485 adapter."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.haus_bus.config_flow.validate_input",
        side_effect=InvalidAuth,
    ):
        result2 = await create_configuration(
            hass, result, TYPE_RS_485_ADAPTER, "/dev/ttyUSB0"
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_unknown_error_rs485(hass: HomeAssistant) -> None:
    """Test we handle unknown errors while configuring rs485 adapter."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.haus_bus.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await create_configuration(
            hass, result, TYPE_RS_485_ADAPTER, "/dev/ttyUSB0"
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}
