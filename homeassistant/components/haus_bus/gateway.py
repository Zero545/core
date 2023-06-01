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

    def add_channel(self, instance: ABusFeature):
        """Add a new Haus-Bus Channel to this gateways channel list."""
        dummy, class_type = str(type(instance)).rsplit(".", 1)
        class_type = class_type[:-2]
        object_id = ObjectId(instance.getObjectId())
        if (
            str(object_id.getClassId()),
            str(object_id.getInstanceId()),
        ) not in self.channels[str(object_id.getDeviceId())]:
            if class_type == "Dimmer":
                dimmer = HausbusLight(
                    "dim",
                    object_id.getInstanceId(),
                    self.devices[str(object_id.getDeviceId())],
                    instance,
                )
                self.channels[str(object_id.getDeviceId())][
                    (str(object_id.getClassId()), str(object_id.getInstanceId()))
                ] = dimmer
                asyncio.run_coroutine_threadsafe(
                    self._listeners[LIGHT_DOMAIN](dimmer), self.hass.loop
                ).result()
            elif class_type == "RGBDimmer":
                dimmer = HausbusLight(
                    "rgb",
                    object_id.getInstanceId(),
                    self.devices[str(object_id.getDeviceId())],
                    instance,
                )
                self.channels[str(object_id.getDeviceId())][
                    (str(object_id.getClassId()), str(object_id.getInstanceId()))
                ] = dimmer
                asyncio.run_coroutine_threadsafe(
                    self._listeners[LIGHT_DOMAIN](dimmer), self.hass.loop
                ).result()

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
