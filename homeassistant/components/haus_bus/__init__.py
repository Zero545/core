"""The hausbus integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant, callback

from .binary_sensor import HausbusBinarySensor
from .const import DOMAIN
from .gateway import HausbusChannel, HausbusDevice, HausbusGateway
from .light import HausbusLight
from .switch import HausbusSwitch

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hausbus from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access

    gateway = HausbusGateway(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = gateway

    # double RGB dimmer dummy device
    device = HausbusDevice(gateway.bridge_id, "123456", "Test 1.2", "Test")

    device.channels.append(HausbusLight("dim", 1, device, gateway))
    device.channels.append(HausbusLight("dim", 2, device, gateway))
    device.channels.append(HausbusLight("dim", 3, device, gateway))
    device.channels.append(HausbusLight("dim", 4, device, gateway))
    device.channels.append(HausbusLight("dim", 5, device, gateway))
    device.channels.append(HausbusLight("dim", 6, device, gateway))
    device.channels.append(HausbusLight("rgb", 1, device, gateway))
    device.channels.append(HausbusLight("rgb", 2, device, gateway))

    device.channels.append(HausbusBinarySensor("btn", 17, device, gateway))
    device.channels.append(HausbusBinarySensor("btn", 18, device, gateway))
    device.channels.append(HausbusBinarySensor("btn", 19, device, gateway))
    device.channels.append(HausbusBinarySensor("btn", 20, device, gateway))
    device.channels.append(HausbusBinarySensor("btn", 21, device, gateway))
    device.channels.append(HausbusChannel("tst", 22, device))

    device.channels.append(HausbusSwitch("out", 210, device, gateway))

    gateway.devices.append(device)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # search devices after adding all callbacks to the gateway object
    gateway.home_server.searchDevices()

    # add device services: needs a services.yaml. Can be moved to separate services.py (see deconz integration)
    @callback
    def handle_reset(call):
        """Handle the service call."""
        device = call.data.get(ATTR_DEVICE_ID, None)

        hass.states.set(f"{DOMAIN}.reset", device)

    hass.services.async_register(
        DOMAIN, "reset", handle_reset, vol.Schema({vol.Required(ATTR_DEVICE_ID): str})
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
