"""Representation of a Haus-Bus gateway."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from pyhausbus import HausBusUtils
from pyhausbus.ABusFeature import ABusFeature
from pyhausbus.BusDataMessage import BusDataMessage
from pyhausbus.HomeServer import HomeServer
from pyhausbus.IBusDataListener import IBusDataListener
from pyhausbus.ObjectId import ObjectId
from pyhausbus.de.hausbus.homeassistant.proxy.Controller import Controller
from pyhausbus.de.hausbus.homeassistant.proxy.Dimmer import Dimmer
from pyhausbus.de.hausbus.homeassistant.proxy.RGBDimmer import RGBDimmer
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.Configuration import (
    Configuration,
)
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.ModuleId import ModuleId
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.RemoteObjects import (
    RemoteObjects,
)

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .channel import HausbusChannel
from .device import HausbusDevice
from .event_handler import IEventHandler
from .light import HausbusLight


class HausbusGateway(IBusDataListener, IEventHandler):
    """Manages a single Haus-Bus gateway."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the system."""
        self.hass = hass
        self.config_entry = config_entry
        self.bridge_id = "1"
        self.devices: dict[str, HausbusDevice] = {}
        self.channels: dict[str, dict[tuple[str, str], HausbusChannel]] = {}
        self.home_server = HomeServer()
        self.home_server.addBusEventListener(self)
        self._listeners: dict[
            str, Callable[[HausbusChannel], Coroutine[Any, Any, None]]
        ] = {}

    def add_device(self, device_id: str, module: ModuleId):
        """Add a new Haus-Bus Device to this gateways devices list."""
        device = HausbusDevice(
            self.bridge_id,
            device_id,
            module.getFirmwareId().getTemplateId()
            + " "
            + str(module.getMajorRelease())
            + "."
            + str(module.getMinorRelease()),
            module.getName(),
            module.getFirmwareId(),
        )
        if device_id not in self.devices:
            self.devices[device_id] = device
        if device_id not in self.channels:
            self.channels[device_id] = {}

    def add_light_channel(
        self, instance: ABusFeature, object_id: ObjectId, light_type: str
    ):
        """Add a new Haus-Bus Light Channel to this gateways channel list."""
        light = HausbusLight(
            light_type,
            object_id.getInstanceId(),
            self.devices[str(object_id.getDeviceId())],
            instance,
        )
        self.channels[str(object_id.getDeviceId())][
            (str(object_id.getClassId()), str(object_id.getInstanceId()))
        ] = light
        asyncio.run_coroutine_threadsafe(
            self._listeners[LIGHT_DOMAIN](light), self.hass.loop
        ).result()

    def add_channel(self, instance: ABusFeature):
        """Add a new Haus-Bus Channel to this gateways channel list."""
        object_id = ObjectId(instance.getObjectId())
        class_id = object_id.getClassId()
        if (
            str(class_id),
            str(object_id.getInstanceId()),
        ) not in self.channels[str(object_id.getDeviceId())]:
            match class_id:
                case Dimmer.CLASS_ID:
                    self.add_light_channel(instance, object_id, "dim")
                case RGBDimmer.CLASS_ID:
                    self.add_light_channel(instance, object_id, "rgb")

    def busDataReceived(self, busDataMessage: BusDataMessage):
        """Handle Haus-Bus messages."""
        if HausBusUtils.getDeviceId(busDataMessage.getSenderObjectId()) == 9998:
            # ignore messages sent from this module
            return

        controller = Controller(busDataMessage.getSenderObjectId())

        if isinstance(busDataMessage.getData(), ModuleId):
            self.add_device(
                str(HausBusUtils.getDeviceId(busDataMessage.getSenderObjectId())),
                busDataMessage.getData(),
            )
            controller.getConfiguration()

        if isinstance(busDataMessage.getData(), Configuration):
            config: Configuration = busDataMessage.getData()
            device = self.devices[
                str(HausBusUtils.getDeviceId(busDataMessage.getSenderObjectId()))
            ]
            device.set_type(config.getFCKE())
            controller.getRemoteObjects()

        if isinstance(busDataMessage.getData(), RemoteObjects):
            instances: list[ABusFeature] = self.home_server.getDeviceInstances(
                busDataMessage.getSenderObjectId(), busDataMessage.getData()
            )
            for instance in instances:
                # handle channels for the sending device
                self.add_channel(instance)

    def register_platform_add_device_callback(
        self,
        add_device_callback: Callable[[HausbusChannel], Coroutine[Any, Any, None]],
        platform: str,
    ):
        """Register add device callbacks."""
        self._listeners[platform] = add_device_callback
