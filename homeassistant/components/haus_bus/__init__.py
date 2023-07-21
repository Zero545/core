"""The hausbus integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .gateway import HausbusGateway

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.BINARY_SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hausbus from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    gateway = HausbusGateway(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = gateway

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug("start searching devices")

    # search devices after adding all callbacks to the gateway object
    gateway.home_server.searchDevices()

    # add device services: needs a services.yaml. Can be moved to separate services.py (see deconz integration)
    #    @callback
    #    def handle_reset(call):
    #        """Handle the service call."""
    #        device = call.data.get(ATTR_DEVICE_ID, None)
    #
    #        hass.states.set(f"{DOMAIN}.reset", device)
    #
    #    hass.services.async_register(
    #        DOMAIN, "reset", handle_reset, vol.Schema({vol.Required(ATTR_DEVICE_ID): str})
    #    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
