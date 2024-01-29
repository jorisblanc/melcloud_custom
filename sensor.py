"""Support for MelCloud device sensors."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional


from .src.pymelcloud import DEVICE_TYPE_ATA, DEVICE_TYPE_ATW, AtwDevice
from .src.pymelcloud.atw_device import Zone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfFrequency,
    PERCENTAGE,

)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory


from . import MelCloudDevice
from .const import DOMAIN, MEL_DEVICES


@dataclass
class MelcloudRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], float]
    enabled: Callable[[Any], bool]


@dataclass
class MelcloudSensorEntityDescription(
    SensorEntityDescription, MelcloudRequiredKeysMixin
):
    """Describes Melcloud sensor entity."""


ATA_SENSORS: tuple[MelcloudSensorEntityDescription, ...] = (
    MelcloudSensorEntityDescription(
        key="wifi_signal",
        name="WiFi Signal",
        icon="mdi:signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        value_fn=lambda x: x.wifi_signal,
        enabled=lambda x: True,
        entity_registry_enabled_default=True,
    ),
    MelcloudSensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda x: x.device.room_temperature,
        enabled=lambda x: True,
        entity_registry_enabled_default=True,
    ),
    MelcloudSensorEntityDescription(
        key="energy",
        name="Energy",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.device.total_energy_consumed,
        enabled=lambda x: x.device.has_energy_consumed_meter,
        entity_registry_enabled_default=True,
    ),
    MelcloudSensorEntityDescription(
        key="daily_energy_consumed",
        name="Daily Energy Consumed",
        icon="mdi:factory",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda x: x.device.daily_energy_consumed,
        enabled=lambda x: True,
        entity_registry_enabled_default=True,
    ),
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up MELCloud device sensors based on config_entry."""
    entry_config = hass.data[DOMAIN][entry.entry_id]

    mel_devices = entry_config.get(MEL_DEVICES)
    entities = []
    entities.extend(
        [
            MelDeviceSensor(mel_device, description)
            for description in ATA_SENSORS
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if description.enabled(mel_device)
        ]
        
    )  
    for mel_device in mel_devices[DEVICE_TYPE_ATW]:
        entities.append(LastApiUpdate(mel_device, mel_device.device))
        entities.append(CondensingTemperature(mel_device, mel_device.device))
        entities.append(OutdoorTemperature(mel_device, mel_device.device))
        entities.append(FlowTemperature(mel_device, mel_device.device))
        entities.append(ReturnTemperature(mel_device, mel_device.device))

        entities.append(DefrostMode(mel_device, mel_device.device))
        entities.append(WaterPump1Status(mel_device, mel_device.device))
        entities.append(BoosterHeater1Status(mel_device, mel_device.device))
        entities.append(BoosterHeater2Status(mel_device, mel_device.device))

        entities.append(DemandPercentage(mel_device, mel_device.device))
        entities.append(HeatPumpFrequency(mel_device, mel_device.device))
        entities.append(HeatPumpOperationMode(mel_device, mel_device.device))
        entities.append(WifiSignal(mel_device, mel_device.device))
        entities.append(ErrorCode(mel_device, mel_device.device))
        entities.append(ErrorMessage(mel_device, mel_device.device))

        entities.append(CurrentEnergyConsumed(mel_device, mel_device.device))
        entities.append(CurrentEnergyProduced(mel_device, mel_device.device))

        if mel_device.device._device_conf['Device']['CanHeat']:
            entities.append(DailyHeatingEnergyConsumed(mel_device, mel_device.device))
            entities.append(DailyHeatingEnergyProduced(mel_device, mel_device.device))

        if mel_device.device._device_conf['Device']['CanCool']:
            entities.append(DailyCoolingEnergyConsumed(mel_device, mel_device.device))
            entities.append(DailyCoolingEnergyProduced(mel_device, mel_device.device))

        if mel_device.device._device_conf['Device']['HasHotWaterTank']:
            entities.append(DailyHotWaterEnergyConsumed(mel_device, mel_device.device))
            entities.append(DailyHotWaterEnergyProduced(mel_device, mel_device.device))
            entities.append(ForcedHotWaterMode(mel_device, mel_device.device))
            entities.append(TankWaterTemperature(mel_device, mel_device.device))

        if mel_device.device._device_conf['Device']['HasThermostatZone1']:
            entities.append(TargetHCTemperatureZone1(mel_device, mel_device.device))
            entities.append(FlowTemperatureZone1(mel_device, mel_device.device))
            entities.append(ReturnTemperatureZone1(mel_device, mel_device.device))
            entities.append(RoomTemperatureZone1(mel_device, mel_device.device))
            entities.append(WaterPump2Status(mel_device, mel_device.device))
        
        if (mel_device.device._device_conf['Device']['HasThermostatZone2'] and 
            mel_device.device._device_conf['Device']['HasZone2']): 
            entities.append(TargetHCTemperatureZone2(mel_device, mel_device.device))
            entities.append(FlowTemperatureZone2(mel_device, mel_device.device))
            entities.append(ReturnTemperatureZone2(mel_device, mel_device.device))
            entities.append(RoomTemperatureZone2(mel_device, mel_device.device))
            entities.append(WaterPump3Status(mel_device, mel_device.device))
        
        if(mel_device.device._device_conf['Device']['HasHotWaterTank'] and
            mel_device.device._device_conf['Device']['HasThermostatZone1']):
            entities.append(ValveStatus3Way(mel_device, mel_device.device))
        
        if mel_device.device._device_conf['Device']['MixingTankWaterTemperature'] != 25:
            entities.append(MixingTankTemperature(mel_device, mel_device.device))

        

    async_add_entities(entities, False)


class MelDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    entity_description: MelcloudSensorEntityDescription

    def __init__(
        self,
        api: MelCloudDevice,
        description: MelcloudSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(api.coordinator)
        self._api = api
        self.entity_description = description

        self._attr_name = f"{api.name} {description.name}"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-{description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._api)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        return self._api.extra_attributes



class LastApiUpdate(CoordinatorEntity, SensorEntity):
    """Representation of the last api update."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:update"
        self._attr_name = f"{api.name} Last Update"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-last_update"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> Optional[datetime]:
        """Return time charge complete."""
        #return datetime.fromisoformat(self._device._device_conf['Device']['LastTimeStamp']).astimezone()
        return self._api.device.last_seen.replace(tzinfo=timezone.utc).astimezone(tz=None)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info



### Heat Pump temperatures
class CondensingTemperature(CoordinatorEntity, SensorEntity):
    """Representation of the condening temperature TH2."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Condensing Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-condensing_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
 
    @property
    def native_value(self) -> Optional[datetime]:
        """Return condensing temperature."""
        return round(self._device._device_conf['Device']['CondensingTemperature'], 1)   

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class OutdoorTemperature(CoordinatorEntity, SensorEntity):
    """Representation of the outside temperature TH7."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Outside Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-outside_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
 
    @property
    def native_value(self) -> Optional[datetime]:
        """Return outside temperature."""
        return round(self._device._device_conf['Device']['OutdoorTemperature'], 1)
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class FlowTemperature(CoordinatorEntity, SensorEntity):
    """Representation of flow temperature."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Flow Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-flow_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return flow temperature."""
        return self._device._device_conf['Device']['FlowTemperature']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
   
class ReturnTemperature(CoordinatorEntity, SensorEntity):
    """Representation of return temperature."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Return Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-return_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return return temperature."""
        return self._device._device_conf['Device']['ReturnTemperature']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class MixingTankTemperature(CoordinatorEntity, SensorEntity):
    """Representation of the mixing tank temperature THW10."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Mixing Tank Water Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-mixing_tank_water_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
 
    @property
    def available(self) -> bool:
        """Return True if Zone 1 exists."""
        return self._device._device_conf['Device']['MixingTankWaterTemperature'] > 25

    @property
    def native_value(self) -> Optional[datetime]:
        """Return mixing tank water temperature."""
        return round(self._device._device_conf['Device']['MixingTankWaterTemperature'], 1)
        
    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class TankWaterTemperature(CoordinatorEntity, SensorEntity):
    """Representation of the tank water temperature THW5B."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Tank Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-tank_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
 
    @property
    def available(self) -> bool:
        """Return True if Zone 1 exists."""
        return self._device._device_conf['Device']['HasHotWaterTank']
    
    @property
    def native_value(self) -> Optional[datetime]:
        """Return tank temperature."""
        return self._device._device_conf['Device']['TankWaterTemperature']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info


### Heat Pump parameters
class DemandPercentage(CoordinatorEntity, SensorEntity):
    """Representation of the demand percentage of the heat pump."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:sine-wave"
        self._attr_name = f"{api.name} Demand percentage"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-demand_percentage"
        self._attr_device_class = SensorDeviceClass.POWER_FACTOR
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=PERCENTAGE

    @property
    def native_value(self) -> Optional[datetime]:
        """Return mixing tank water temperature."""
        return self._device._device_conf['Device']['DemandPercentage']
        
    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class HeatPumpFrequency(CoordinatorEntity, SensorEntity):
    """Representation of the frequency of the heat pump compressor."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:sine-wave"
        self._attr_name = f"{api.name} Heat Pump Frequency"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-heat_pump_frequency"
        self._attr_device_class = SensorDeviceClass.FREQUENCY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfFrequency.HERTZ
    
    @property
    def native_value(self) -> Optional[datetime]:
        """Return tank temperature."""
        return self._device._device_conf['Device']['HeatPumpFrequency']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
    
class HeatPumpOperationMode(CoordinatorEntity, SensorEntity):
    """Representation of the current operation mode of the heat pump."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:list-box"
        self._attr_name = f"{api.name} Operation Mode"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-heat_pump_operation_mode"
        #self._attr_device_class = SensorDeviceClass.ENUM
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        return self._device.status

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
     
class WifiSignal(CoordinatorEntity, SensorEntity):
    """Representation of the WiFi signal strength."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:signal"
        self._attr_name = f"{api.name} WiFi Signal"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-wifi_signal"
        self._attr_native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_device_class=SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[str]:
        """Return wifi strength."""
        return self._device.wifi_signal

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
    
class ErrorCode(CoordinatorEntity, SensorEntity):
    """Representation of the WiFi signal strength."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:alert-circle"
        self._attr_name = f"{api.name} Error Code"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-error_code"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[str]:
        """Return wifi strength."""
        return self._device.error_code

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
        
class ErrorMessage(CoordinatorEntity, SensorEntity):
    """Representation of the WiFi signal strength."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:alert-circle"
        self._attr_name = f"{api.name} Error Message"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-error_message"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[str]:
        """Return error message."""
        return self._device.error_message

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info


class DefrostMode(CoordinatorEntity, SensorEntity):
    """Representation of the defrost mode."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:snowflake-melt"
        self._attr_name = f"{api.name} Defrost Mode"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-defrost_mode"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        return self._device._device_conf['Device']['DefrostMode']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
 
class BoosterHeater1Status(CoordinatorEntity, SensorEntity):
    """Representation of the booster heater 1 status."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_name = f"{api.name} Booster Heater 1 Status"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-booster_heater_1_status"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['BoosterHeater1Status']:
            return "On"
        return "Off"
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
 
class BoosterHeater2Status(CoordinatorEntity, SensorEntity):
    """Representation of the booster heater 2 status."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_name = f"{api.name} Booster Heater 2 Status"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-booster_heater_2_status"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['BoosterHeater2Status']:
            return "On"
        return "Off"

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
  
class WaterPump1Status(CoordinatorEntity, SensorEntity):
    """Representation of the water pump 1 status."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_name = f"{api.name} Water Pump 1 Status"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-water_pump_1_status"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['WaterPump1Status']:
            return "On"
        return "Off"
    
    @property
    def icon(self) -> str | None:
        if self._device._device_conf['Device']['WaterPump1Status']:
            return "mdi:pump"
        return "mdi:pump-off"
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class WaterPump2Status(CoordinatorEntity, SensorEntity):
    """Representation of the water pump 2 status."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:pump"
        self._attr_name = f"{api.name} Water Pump 2 Status"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-water_pump_2_status"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['WaterPump2Status']:
            return "On"
        return "Off"
        
    @property
    def icon(self) -> str | None:
        if self._device._device_conf['Device']['WaterPump2Status']:
            return "mdi:pump"
        return "mdi:pump-off"

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
 
class WaterPump3Status(CoordinatorEntity, SensorEntity):
    """Representation of the water pump 3 status."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_name = f"{api.name} Water Pump 3 Status"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-water_pump_3_status"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['WaterPump3Status']:
            return "On"
        return "Off"

    @property
    def icon(self) -> str | None:
        if self._device._device_conf['Device']['WaterPump3Status']:
            return "mdi:pump"
        return "mdi:pump-off"
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
 
class ValveStatus3Way(CoordinatorEntity, SensorEntity):
    """Representation of the 3 way valve status."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:pipe-valve"
        self._attr_name = f"{api.name} 3 Way Valve"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-valve_status_3_way"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['ValveStatus3Way']:
            return "ECS"
        return "Chauffage"
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
 
class ForcedHotWaterMode(CoordinatorEntity, SensorEntity):
    """Representation of the forced hot water mode."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer-water"
        self._attr_name = f"{api.name} Forced Hot Water Mode"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-forced_hot_water_mode"
    
    @property
    def native_value(self) -> Optional[str]:
        """Return tank temperature."""
        if self._device._device_conf['Device']['ForcedHotWaterMode']:
            return "On"
        return "Off"  

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
 
 


## Energy

class CurrentEnergyConsumed(CoordinatorEntity, SensorEntity):
    """Representation of the current energy consumed."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Current Energy Consumed"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-current_energy_consumed"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return tank temperature."""
        return self._device._device_conf['Device']['CurrentEnergyConsumed']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class CurrentEnergyProduced(CoordinatorEntity, SensorEntity):
    """Representation of the current energy produced."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Current Energy Produced"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-current_energy_produced"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return tank temperature."""
        return self._device._device_conf['Device']['CurrentEnergyProduced']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
  
class DailyHeatingEnergyConsumed(CoordinatorEntity, SensorEntity):
    """Representation of the daily heating energy consumed."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Daily Heating Energy Consumed"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-daily_heating_energy_consumed"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return value."""
        return self._device._device_conf['Device']['DailyHeatingEnergyConsumed']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class DailyHeatingEnergyProduced(CoordinatorEntity, SensorEntity):
    """Representation of the daily heating energy produced."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Daily Heating Energy Produced"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-daily_heating_energy_produced"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return value."""
        return self._device._device_conf['Device']['DailyHeatingEnergyProduced']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
   

class DailyHotWaterEnergyConsumed(CoordinatorEntity, SensorEntity):
    """Representation of the daily hot water energy consumed."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Daily Hot Water Energy Consumed"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-daily_hot_water_energy_consumed"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return value."""
        return self._device._device_conf['Device']['DailyHotWaterEnergyConsumed']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class DailyHotWaterEnergyProduced(CoordinatorEntity, SensorEntity):
    """Representation of the daily heating energy produced."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Daily Hot Water Energy Produced"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-daily_hot_water_energy_produced"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return value."""
        return self._device._device_conf['Device']['DailyHotWaterEnergyProduced']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info


class DailyCoolingEnergyConsumed(CoordinatorEntity, SensorEntity):
    """Representation of the daily cooling energy consumed."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Daily Cooling Energy Consumed"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-daily_cooling_energy_consumed"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return value."""
        return self._device._device_conf['Device']['DailyCoolingEnergyConsumed']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class DailyCoolingEnergyProduced(CoordinatorEntity, SensorEntity):
    """Representation of the daily cooling energy produced."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:factory"
        self._attr_name = f"{api.name} Daily Cooling Energy Produced"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-daily_cooling_energy_produced"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
    
    @property
    def native_value(self) -> float:
        """Return value."""
        return self._device._device_conf['Device']['DailyCoolingEnergyProduced']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
     



### Zone 1
class TargetHCTemperatureZone1(CoordinatorEntity, SensorEntity):
    """Representation of target temperature of Zone 1."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 1 Target Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_1_target_hc_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return target temperature."""
        return self._device._device_conf['Device']['TargetHCTemperatureZone1']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

class FlowTemperatureZone1(CoordinatorEntity, SensorEntity):
    """Representation of flow temperature of Zone 1."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 1 Flow Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_1_flow_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return flow temperature."""
        return self._device._device_conf['Device']['FlowTemperatureZone1']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
   
class ReturnTemperatureZone1(CoordinatorEntity, SensorEntity):
    """Representation of retun temperature of Zone 1."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 1 Return Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_1_return_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return return temperature."""
        return self._device._device_conf['Device']['ReturnTemperatureZone1']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
      
class RoomTemperatureZone1(CoordinatorEntity, SensorEntity):
    """Representation of flow temperature of Zone 1."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 1 Room Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_1_room_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return flow temperature."""
        return self._device._device_conf['Device']['RoomTemperatureZone1']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info


### Zone 2
class TargetHCTemperatureZone2(CoordinatorEntity, SensorEntity):
    """Representation of target temperature of Zone 2."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 2 Target Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_2_target_hc_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    
    @property
    def native_value(self) -> Optional[datetime]:
        """Return target temperature."""
        return self._device._device_conf['Device']['TargetHCTemperatureZone2']
        

    @property
    def device_info(self):
        return self._api.device_info

class FlowTemperatureZone2(CoordinatorEntity, SensorEntity):
    """Representation of flow temperature of Zone 2."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 2 Flow Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_2_flow_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return flow temperature."""
        return self._device._device_conf['Device']['FlowTemperatureZone2']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
   
class ReturnTemperatureZone2(CoordinatorEntity, SensorEntity):
    """Representation of retun temperature of Zone 1."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 2 Return Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_2_return_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return return temperature."""
        return self._device._device_conf['Device']['ReturnTemperatureZone2']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
      
class RoomTemperatureZone2(CoordinatorEntity, SensorEntity):
    """Representation of flow temperature of Zone 1."""

    def __init__(self, api: MelCloudDevice, device: AtwDevice) -> None:
        """Initialize  device."""
        super().__init__(api.coordinator)
        self._api = api
        self._device = device
        self._attr_icon = "mdi:thermometer"
        self._attr_name = f"{api.name} Zone 2 Room Temperature"
        self._attr_unique_id = f"{api.device.serial}-{api.device.mac}-zone_2_room_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    

    @property
    def native_value(self) -> Optional[datetime]:
        """Return flow temperature."""
        return self._device._device_conf['Device']['RoomTemperatureZone2']
        

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info
  