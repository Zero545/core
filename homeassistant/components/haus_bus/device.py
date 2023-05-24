"""Representation of a Haus-Bus device."""
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


class HausbusDevice:
    """Common base for Haus-Bus devices."""

    def __init__(
        self, bridge_id: str, device_id: str, sw_version: str, hw_version: str
    ) -> None:
        """Set up Haus-Bus device."""
        self._device_id = device_id
        self.manufacturer = "Haus-Bus.de"
        self.model_id = "Doppel RGB Dimmer"
        self.name = f"RGB Dimmer ID {self._device_id}"
        self.software_version = sw_version
        self.hardware_version = hw_version
        self.bridge_id = bridge_id

    @property
    def device_id(self) -> str | None:
        """Return a serial number for this device."""
        return self._device_id

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return a device description for device registry."""
        if self.device_id is None:
            return None

        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            manufacturer=self.manufacturer,
            model=self.model_id,
            name=self.name,
            sw_version=self.software_version,
            hw_version=self.hardware_version,
            via_device=(DOMAIN, self.bridge_id),
        )
