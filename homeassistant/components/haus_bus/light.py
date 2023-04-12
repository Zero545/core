"""Support for Haus-Bus lights."""
from typing import Any, cast

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    DOMAIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN as HAUSBUSDOMAIN
from .gateway import HausbusChannel, HausbusDevice, HausbusGateway


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Haus-Bus lights from a config entry."""
    gateway = cast(HausbusGateway, hass.data[HAUSBUSDOMAIN][config_entry.entry_id])

    er.async_get(hass)

    # search for light entities in discovered devices
    entities: list[HausbusLight] = []
    for device in gateway.devices:
        for channel in device.channels:
            if isinstance(channel, HausbusLight):
                entities.append(channel)

    async_add_entities(entities)


class HausbusLight(HausbusChannel, LightEntity):
    """Representation of a Haus-Bus light."""

    TYPE = DOMAIN

    def __init__(
        self,
        channel_type: str,
        instance_id: int,
        device: HausbusDevice,
        gateway: HausbusGateway,
    ) -> None:
        """Set up light."""
        super().__init__(channel_type, instance_id, device, gateway)

        self._state = 0
        self._brightness = 255
        self._rgb = (255, 255, 255)

        self._attr_supported_color_modes: set[ColorMode] = set()
        if self._type == "dim":
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        elif self._type == "rgb":
            self._attr_supported_color_modes.add(ColorMode.RGB)

    @property
    def color_mode(self) -> str | None:
        """Return the color mode of the light."""
        if self._type == "dim":
            color_mode = ColorMode.BRIGHTNESS
        elif self._type == "rgb":
            color_mode = ColorMode.RGB
        else:
            color_mode = ColorMode.ONOFF
        return color_mode

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the brightness of this light between 0..255."""
        return self._rgb

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state == 1

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on action."""
        self._state = 1

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off action."""
        self._state = 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_RGB_COLOR in kwargs:
            self._rgb = kwargs[ATTR_RGB_COLOR]

        self.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off light."""
        self.turn_off()

    @callback
    def async_update_callback(self) -> None:
        """Light state push update."""
