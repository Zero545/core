"""Support for Haus-Bus switches."""
from typing import Any, cast

from homeassistant.components.switch import DOMAIN, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN as HAUSBUSDOMAIN
from .device import HausbusChannel, HausbusDevice
from .gateway import HausbusGateway


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Haus-Bus lights from a config entry."""
    gateway = cast(HausbusGateway, hass.data[HAUSBUSDOMAIN][config_entry.entry_id])

    er.async_get(hass)

    # search for light entities in discovered devices

    switch_device = HausbusDevice(gateway)

    switch_device.channels.append(HausbusSwitch("out", 210, switch_device, gateway))

    async_add_entities(switch_device.channels)


class HausbusSwitch(HausbusChannel, SwitchEntity):
    """Representation of a Haus-Bus switch."""

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

        self._state = False

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on action."""
        self._state = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off action."""
        self._state = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on switch."""
        self.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off switch."""
        self.turn_off()

    @callback
    def async_update_callback(self) -> None:
        """Light state push update."""
