"""Support for MELCloud switches."""
from __future__ import annotations

from typing import Any

from .src.pymelcloud import DEVICE_TYPE_ATW, AtwDevice
from .src.pymelcloud.device import PROPERTY_POWER



"""Support for MELCloud switches."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from . import DOMAIN, MelCloudDevice
from .const import ATTR_STATUS, MEL_DEVICES






async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:    
    """Set up MELCloud device sensors based on config_entry."""
    
    mel_devices = hass.data[DOMAIN][entry.entry_id].get(MEL_DEVICES)
    entities = []

    for mel_device in mel_devices[DEVICE_TYPE_ATW]:
        entities.append(PowerSwitch(mel_device, mel_device.device))

    async_add_entities(entities, True)




class PowerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Switch."""


    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize water heater device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:power"        
        self._attr_name = f"{api.name} Power"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-power"
        


    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def available(self) -> bool:
        """Return True if steering wheel heater is available."""
        return True

    @property
    def is_on(self):
        """Return True if steering wheel heater is on."""
        return self._device.power

    async def async_turn_on(self, **kwargs):
        """Send the on command."""
        await self._api.async_set({PROPERTY_POWER: True})

    async def async_turn_off(self, **kwargs):
        """Send the off command."""
        await self._api.async_set({PROPERTY_POWER: False})