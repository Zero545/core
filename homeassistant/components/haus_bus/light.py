"""Support for Haus-Bus lights."""
from typing import Any, cast

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    DOMAIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN as HAUSBUSDOMAIN
from .gateway import HausbusGateway


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the deCONZ lights and groups from a config entry."""
    gateway = cast(HausbusGateway, hass.data[HAUSBUSDOMAIN][config_entry.entry_id])

    er.async_get(hass)

    # search for light entities in discovered devices

    light_device = HausbusDevice()

    async_add_entities([HausbusLight(light_device, gateway)])


class HausbusDevice:
    """Test device implementation."""

    name = "Dimmer"
    id = 123456
    channels = ["dim1", "dim2"]
    brightness = 0
    state = False

    def turn_on(self) -> None:
        """Turn on action."""
        self.state = True

    def turn_off(self) -> None:
        """Turn off action."""
        self.state = False


class HausbusLight(LightEntity):
    """Representation of a Haus-Bus light."""

    TYPE = DOMAIN

    def __init__(self, device: HausbusDevice, gateway: HausbusGateway) -> None:
        """Set up light."""
        super().__init__()

        self._device = device
        self.gateway = gateway

    @property
    def color_mode(self) -> str | None:
        """Return the color mode of the light."""
        if self._device.brightness is not None:
            color_mode = ColorMode.BRIGHTNESS
        else:
            color_mode = ColorMode.ONOFF
        return color_mode

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self._device.brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._device.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        self._device.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        self._device.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        self._device.turn_off()

    @callback
    def async_update_callback(self) -> None:
        """Light state push update."""
