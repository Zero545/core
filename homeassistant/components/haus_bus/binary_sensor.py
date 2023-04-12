"""Support for Haus-Bus binary sensors."""
from typing import cast

from homeassistant.components.binary_sensor import DOMAIN, BinarySensorEntity
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
    """Set up the Haus-Bus binary sensors from a config entry."""
    gateway = cast(HausbusGateway, hass.data[HAUSBUSDOMAIN][config_entry.entry_id])

    er.async_get(hass)

    # search for binary sensor entities in discovered devices
    entities: list[HausbusBinarySensor] = []
    for device in gateway.devices:
        for channel in device.channels:
            if isinstance(channel, HausbusBinarySensor):
                entities.append(channel)

    async_add_entities(entities)


class HausbusBinarySensor(HausbusChannel, BinarySensorEntity):
    """Representation of a Haus-Bus light."""

    TYPE = DOMAIN

    def __init__(
        self, channel_type: str, instance_id: int, device: HausbusDevice
    ) -> None:
        """Set up binary sensor."""
        super().__init__(channel_type, instance_id, device)

        self._state = False

    @property
    def is_on(self) -> bool | None:
        """Return binary sensor state."""
        return self._state

    @callback
    def async_update_callback(self) -> None:
        """Binary sensor state push update."""
