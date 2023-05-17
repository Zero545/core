"""Helper functions for Haus-Bus tests."""

from homeassistant.components.haus_bus.config_flow import (
    CONF_DEVICE_PATH,
    CONF_GATEWAY_TYPE,
    CONF_IP_ADDRESS,
    TYPE_IP_GATEWAY,
    TYPE_RS_485_ADAPTER,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult


async def create_configuration(
    hass: HomeAssistant, flow: FlowResult, conf_type: str, conf_option: str
) -> FlowResult:
    """Fill configuration form."""
    await hass.config_entries.flow.async_configure(
        flow["flow_id"],
        {CONF_GATEWAY_TYPE: conf_type},
    )
    if conf_type == TYPE_IP_GATEWAY:
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {CONF_IP_ADDRESS: conf_option},
        )
    if conf_type == TYPE_RS_485_ADAPTER:
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {CONF_DEVICE_PATH: conf_option},
        )
    await hass.async_block_till_done()
    return result
