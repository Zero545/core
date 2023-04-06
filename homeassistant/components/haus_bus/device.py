"""Base class for Haus-Bus devices."""
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN
from .gateway import HausbusGateway


class HausbusDevice:
    """Common base for Haus-Bus devices."""

    def __init__(self, gateway: HausbusGateway) -> None:
        """Set up Haus-Bus device."""
        self._device_id = "123456"
        self.manufacturer = "Haus-Bus.de"
        self.model_id = "Doppel RGB Dimmer"
        self.name = f"RGB Dimmer ID {self._device_id}"
        self.software_version = "1.0"
        self._gateway = gateway
        self._gateway.bridge_id = "42"
        self.channels: list[HausbusChannel] = []

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
            via_device=(DOMAIN, self._gateway.bridge_id),
        )


class HausbusChannel(Entity):
    """Common base for HausBus channels."""

    _attr_has_entity_name = True

    def __init__(
        self,
        channel_type: str,
        instance_id: int,
        device: HausbusDevice,
        gateway: HausbusGateway,
    ) -> None:
        """Set up channel."""
        self._type = channel_type
        self._instance_id = instance_id
        self._device = device
        self._gateway = gateway

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this channel."""
        return f"{self._device.device_id}-{self._type}{self._instance_id}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return a device description for device registry."""
        return self._device.device_info

    @property
    def translation_key(self) -> str | None:
        """Return the translation key to translate the entity's states."""
        if self._instance_id != 210:
            return self._type
        return "redled"

    @property
    def name(self) -> str | None:
        """Return the channel name."""
        if self._instance_id != 210:
            return f"{super().name} {self._instance_id}"
        return super().name
