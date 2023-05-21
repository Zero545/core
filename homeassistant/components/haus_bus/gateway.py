"""Representation of a Haus-Bus gateway."""
from collections.abc import Callable

from pyhausbus import HausBusUtils
from pyhausbus.BusDataMessage import BusDataMessage
from pyhausbus.HomeServer import HomeServer
from pyhausbus.IBusDataListener import IBusDataListener
from pyhausbus.de.hausbus.homeassistant.proxy.Controller import Controller
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.ModuleId import ModuleId
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.RemoteObjects import (
    RemoteObjects,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity

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
            hw_version=self.hardware_version,
            via_device=(DOMAIN, self.bridge_id),
        )


class HausbusChannel(Entity):
    """Common base for HausBus channels."""

    _attr_has_entity_name = True

    def __init__(
        self, channel_type: str, instance_id: int, device: HausbusDevice
    ) -> None:
        """Set up channel."""
        self._type = channel_type
        self._instance_id = instance_id
        self._device = device

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


class HausbusGateway(IBusDataListener):
    """Manages a single Haus-Bus gateway."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the system."""
        self.hass = hass
        self.config_entry = config_entry
        self.bridge_id = "1"
        self.devices: list[HausbusDevice] = []
        self.home_server = HomeServer()
        self.home_server.addBusEventListener(self)
        self._listeners: dict[str, Callable[[HausbusChannel], None]] = {}

    def add_device(self, device_id: str, module: ModuleId):
        """Add a new Haus-Bus Device to this gateways devies list."""
        device = HausbusDevice(
            self.bridge_id,
            device_id,
            module.getFirmwareId().getTemplateId()
            + " "
            + str(module.getMajorRelease())
            + "."
            + str(module.getMinorRelease()),
            module.getName(),
        )
        self.devices.append(device)

    def busDataReceived(self, busDataMessage: BusDataMessage):
        """Handle Haus-Bus messages."""
        if HausBusUtils.getDeviceId(busDataMessage.getSenderObjectId()) == 9998:
            # ignore messages sent from this module
            return

        if isinstance(busDataMessage.getData(), ModuleId):
            self.add_device(
                str(HausBusUtils.getDeviceId(busDataMessage.getSenderObjectId())),
                busDataMessage.getData(),
            )
            Controller(busDataMessage.getSenderObjectId()).getRemoteObjects()

        if isinstance(busDataMessage.getData(), RemoteObjects):
            instances = self.home_server.getDeviceInstances(
                busDataMessage.getSenderObjectId(), busDataMessage.getData()
            )
            for _act_instance in instances:
                # handle channels for the sending device
                pass

    def register_platform_add_device_callback(
        self, add_device_callback: Callable[[HausbusChannel], None], platform: str
    ):
        """Register add device callbacks."""
        self._listeners[platform] = add_device_callback
