"""Platform for water_heater integration."""
from __future__ import annotations
import time
from typing import Any
import logging


from .src.pymelcloud import DEVICE_TYPE_ATW, AtwDevice
from .src.pymelcloud.atw_device import (
    PROPERTY_OPERATION_MODE,
    PROPERTY_TARGET_TANK_TEMPERATURE,
    ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
    ZONE_OPERATION_MODE_COOL_THERMOSTAT,
    ZONE_OPERATION_MODE_HEAT_FLOW,
    ZONE_OPERATION_MODE_COOL_FLOW,
    Zone
)
from .src.pymelcloud.device import PROPERTY_POWER

from homeassistant.components.water_heater import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, MelCloudDevice
from .const import ATTR_STATUS, MEL_DEVICES


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up MelCloud device climate based on config_entry."""
    mel_devices = hass.data[DOMAIN][entry.entry_id].get(MEL_DEVICES)

    entities = []


    for mel_device in mel_devices[DEVICE_TYPE_ATW]:
        
        if (mel_device.device._device_conf['Device']['HasHotWaterTank'] and
            mel_device.device._device_conf['Device']['CanSetTankTemperature']):
            entities.append(HotWaterAccumulator(mel_device, mel_device.device))
        if mel_device.device._device_conf['Device']['CanHeat']:
            [
            entities.append(HeatingWaterAccumulator(mel_device, mel_device.device, zone))
            for zone in mel_device.device.zones
            ]
    
    
    async_add_entities(entities, False)



class HotWaterAccumulator(CoordinatorEntity, WaterHeaterEntity):
    """Air-to-Water water heater."""

    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize water heater device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_name = f"{api.name} Hot water Accumulator"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-hot_water_accumulator"

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._api.async_set({PROPERTY_POWER: True})

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self._api.async_set({PROPERTY_POWER: False})

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes with device specific additions."""
        data = {ATTR_STATUS: self._device.status}
        return data

    @property
    def current_operation(self) -> str | None:
        """Return current operation as reported by pymelcloud."""
        return self._device.operation_mode

    @property
    def operation_list(self) -> list[str]:
        """Return the list of available operation modes as reported by pymelcloud."""
        return self._device.operation_modes

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.tank_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.target_tank_temperature

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        await self._api.async_set(
            {
                PROPERTY_TARGET_TANK_TEMPERATURE: kwargs.get(
                    "temperature", self.target_temperature
                )
            }
        )

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        await self._api.async_set({PROPERTY_OPERATION_MODE: operation_mode})

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self._device._device_conf['Device']['MinSetTemperature'] or 10

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self._device._device_conf['Device']['MaxSetTemperature'] or 60


class HeatingWaterAccumulator(CoordinatorEntity, WaterHeaterEntity):
    """Air-to-Water water heater."""

    
    def __init__(self, api: MelCloudDevice, device: AtwDevice, zone: Zone) -> None:
        """Initialize water heater device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._zone = zone
        self._attr_name = f"{api.name} Zone {zone.zone_index} Heating water Accumulator"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_{zone.zone_index}_heating_water_accumulator"

    
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

 

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
   
    @property
    def supported_features(self) -> list[str]:
        """Return the list of available operation modes as reported by pymelcloud."""
        if self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_THERMOSTAT,
            ZONE_OPERATION_MODE_HEAT_FLOW,
            ZONE_OPERATION_MODE_COOL_FLOW, ]:
            return WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.OPERATION_MODE
        
        else :
            return WaterHeaterEntityFeature.OPERATION_MODE
        

    @property
    def current_operation(self) -> str | None:
        """Return current operation as reported by pymelcloud."""
        return self._zone.operation_mode

    @property
    def operation_list(self) -> list[str]:
        """Return the list of available operation modes as reported by pymelcloud."""
        return self._zone.operation_modes
        


    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_FLOW,
            ZONE_OPERATION_MODE_COOL_FLOW ]:
            return self._device._device_conf['Device']['FlowTemperature']
        
        elif self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_THERMOSTAT ]:
            return self._zone.room_temperature

    
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_FLOW,
            ZONE_OPERATION_MODE_COOL_FLOW ]:
            return self._zone.target_flow_temperature
        
        elif self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_THERMOSTAT ]:
            return self._zone.target_temperature


    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""

        if self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_FLOW,
            ZONE_OPERATION_MODE_COOL_FLOW ]:
            await self._zone.set_target_flow_temperature(kwargs.get("temperature", self.target_temperature))

        
        elif self._zone.operation_mode in [
            ZONE_OPERATION_MODE_HEAT_THERMOSTAT,
            ZONE_OPERATION_MODE_COOL_THERMOSTAT ]:
            await self._zone.set_target_temperature(kwargs.get("temperature", self.target_temperature))


    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        await self._zone.set_operation_mode(operation_mode)
    
    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 10

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self._device._device_conf['Device']['MaxSetTemperature'] or 60

