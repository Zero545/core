"""Representation of a Haus-Bus gateway."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .device import HausbusDevice


class HausbusGateway:
    """Manages a single Haus-Bus gateway."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the system."""
        self.hass = hass
        self.config_entry = config_entry
        self.bridge_id = "1"
        self.devices: list[HausbusDevice] = []
