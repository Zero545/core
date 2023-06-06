"""Representation of a Haus-Bus gateway."""

import asyncio
from collections.abc import Callable, Coroutine
import colorsys
from typing import Any, cast

from pyhausbus.ABusFeature import ABusFeature
from pyhausbus.BusDataMessage import BusDataMessage
from pyhausbus.HomeServer import HomeServer
from pyhausbus.IBusDataListener import IBusDataListener
from pyhausbus.ObjectId import ObjectId
from pyhausbus.de.hausbus.homeassistant.proxy.Controller import Controller
from pyhausbus.de.hausbus.homeassistant.proxy.Dimmer import Dimmer
from pyhausbus.de.hausbus.homeassistant.proxy.Led import Led
from pyhausbus.de.hausbus.homeassistant.proxy.RGBDimmer import RGBDimmer
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.Configuration import (
    Configuration,
)
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.ModuleId import ModuleId
from pyhausbus.de.hausbus.homeassistant.proxy.controller.data.RemoteObjects import (
    RemoteObjects,
)
from pyhausbus.de.hausbus.homeassistant.proxy.dimmer.data.EvOff import (
    EvOff as DimmerEvOff,
)
from pyhausbus.de.hausbus.homeassistant.proxy.dimmer.data.EvOn import EvOn as DimmerEvOn
from pyhausbus.de.hausbus.homeassistant.proxy.dimmer.data.Status import (
    Status as DimmerStatus,
)
from pyhausbus.de.hausbus.homeassistant.proxy.led.data.EvOff import EvOff as ledEvOff
from pyhausbus.de.hausbus.homeassistant.proxy.led.data.EvOn import EvOn as ledEvOn
from pyhausbus.de.hausbus.homeassistant.proxy.led.data.Status import Status as ledStatus
from pyhausbus.de.hausbus.homeassistant.proxy.rGBDimmer.data.EvOff import (
    EvOff as rgbDimmerEvOff,
)
from pyhausbus.de.hausbus.homeassistant.proxy.rGBDimmer.data.EvOn import (
    EvOn as rgbDimmerEvOn,
)
from pyhausbus.de.hausbus.homeassistant.proxy.rGBDimmer.data.Status import (
    Status as rgbDimmerStatus,
)

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .channel import HausbusChannel
from .const import ATTR_ON_STATE
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
        self._new_channel_listeners: dict[
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

    def get_device(self, object_id: ObjectId) -> HausbusDevice:
        """Get the device referenced by ObjectId from the devices list."""
        return self.devices[str(object_id.getDeviceId())]

    def get_channel_list(
        self, object_id: ObjectId
    ) -> dict[tuple[str, str], HausbusChannel]:
        """Get the channel list of a device referenced by ObjectId."""
        return self.channels[str(object_id.getDeviceId())]

    def get_channel_id(self, object_id: ObjectId) -> tuple[str, str]:
        """Get the channel identifier from an ObjectId."""
        return (str(object_id.getClassId()), str(object_id.getInstanceId()))

    def get_channel(self, object_id: ObjectId) -> HausbusChannel:
        """Get channel from channel list."""
        channels = self.get_channel_list(object_id)
        channel_id = self.get_channel_id(object_id)
        return channels[channel_id]

    def is_light_channel(self, class_id: int) -> bool:
        """Check if a class_id is a light."""
        if class_id in (Dimmer.CLASS_ID, RGBDimmer.CLASS_ID, Led.CLASS_ID):
            return True
        return False

    def add_light_channel(self, instance: ABusFeature, object_id: ObjectId):
        """Add a new Haus-Bus Light Channel to this gateways channel list."""
        light = HausbusLight(
            object_id.getInstanceId(),
            self.get_device(object_id),
            instance,
        )
        self.get_channel_list(object_id)[self.get_channel_id(object_id)] = light
        asyncio.run_coroutine_threadsafe(
            self._new_channel_listeners[LIGHT_DOMAIN](light), self.hass.loop
        ).result()

    def add_channel(self, instance: ABusFeature):
        """Add a new Haus-Bus Channel to this gateways channel list."""
        object_id = ObjectId(instance.getObjectId())
        if self.get_channel_id(object_id) not in self.get_channel_list(object_id):
            if self.is_light_channel(object_id.getClassId()):
                self.add_light_channel(instance, object_id)

    def set_light_color(self, channel: HausbusChannel, red: int, green: int, blue: int):
        """Set the brightness of a light channel."""
        hue, saturation, value = colorsys.rgb_to_hsv(
            red / 100.0,
            green / 100.0,
            blue / 100.0,
        )
        params = {
            ATTR_ON_STATE: 1,
            ATTR_BRIGHTNESS: round(value * 255),
            ATTR_HS_COLOR: (round(hue * 360), round(saturation * 100)),
        }
        channel.async_update_callback(**params)

    def set_light_brightness(self, channel: HausbusChannel, brightness: int):
        """Set the brightness of a light channel."""
        params = {ATTR_ON_STATE: 1, ATTR_BRIGHTNESS: (brightness * 255) // 100}
        channel.async_update_callback(**params)

    def light_turn_off(self, channel: HausbusChannel):
        """Turn off a light channel."""
        params = {
            ATTR_ON_STATE: 0,
        }
        channel.async_update_callback(**params)

    def busDataReceived(self, busDataMessage: BusDataMessage):
        """Handle Haus-Bus messages."""
        object_id = ObjectId(busDataMessage.getSenderObjectId())
        data = busDataMessage.getData()

        if object_id.getDeviceId() == 9998:
            # ignore messages sent from this module
            return

        controller = Controller(object_id.getValue())

        if isinstance(data, ModuleId):
            self.add_device(
                str(object_id.getDeviceId()),
                data,
            )
            controller.getConfiguration()
        if isinstance(data, Configuration):
            config = cast(Configuration, data)
            device = self.get_device(object_id)
            device.set_type(config.getFCKE())
            controller.getRemoteObjects()
        if isinstance(data, RemoteObjects):
            instances: list[ABusFeature] = self.home_server.getDeviceInstances(
                object_id.getValue(), data
            )
            for instance in instances:
                # handle channels for the sending device
                self.add_channel(instance)
        # dimmer event handling
        if isinstance(data, DimmerEvOn):
            channel = self.get_channel(object_id)
            event = cast(DimmerEvOn, data)
            self.set_light_brightness(channel, event.getBrightness())
        if isinstance(data, DimmerStatus):
            channel = self.get_channel(object_id)
            event = cast(DimmerStatus, data)
            if event.getBrightness() > 0:
                self.set_light_brightness(channel, event.getBrightness())
            else:
                self.light_turn_off(channel)
        # rgb dimmmer event handling
        if isinstance(data, rgbDimmerEvOn):
            channel = self.get_channel(object_id)
            event = cast(rgbDimmerEvOn, data)
            self.set_light_color(
                channel,
                event.getBrightnessRed(),
                event.getBrightnessGreen(),
                event.getBrightnessBlue(),
            )
        if isinstance(data, rgbDimmerStatus):
            channel = self.get_channel(object_id)
            event = cast(rgbDimmerStatus, data)
            if (
                event.getBrightnessBlue() > 0
                or event.getBrightnessGreen() > 0
                or event.getBrightnessRed() > 0
            ):
                self.set_light_color(
                    channel,
                    event.getBrightnessRed(),
                    event.getBrightnessGreen(),
                    event.getBrightnessBlue(),
                )
            else:
                self.light_turn_off(channel)
        # led event handling
        if isinstance(data, ledEvOn):
            channel = self.get_channel(object_id)
            event = cast(ledEvOn, data)
            self.set_light_brightness(channel, event.getBrightness())
        if isinstance(data, ledStatus):
            channel = self.get_channel(object_id)
            event = cast(ledStatus, data)
            if event.getBrightness() > 0:
                self.set_light_brightness(channel, event.getBrightness())
            else:
                self.light_turn_off(channel)
        # light off events
        if isinstance(data, (DimmerEvOff, ledEvOff, rgbDimmerEvOff)):
            channel = self.get_channel(object_id)
            self.light_turn_off(channel)

    def register_platform_add_channel_callback(
        self,
        add_channel_callback: Callable[[HausbusChannel], Coroutine[Any, Any, None]],
        platform: str,
    ):
        """Register add channel callbacks."""
        self._new_channel_listeners[platform] = add_channel_callback
