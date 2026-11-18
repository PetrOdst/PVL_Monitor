"""Sensor platform for PVL Slapy measurements."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfLength, UnitOfTemperature, UnitOfVolume, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PVLConfigEntry
from .api import PVLMeasurements
from .const import DOMAIN, RESERVOIR_ID, RESERVOIR_NAME
from .coordinator import PVLDataCoordinator


@dataclass(frozen=True, kw_only=True)
class PVLSensorDescription(SensorEntityDescription):
    """Describe a sensor and the source field it reads."""

    value_fn: Callable[[PVLMeasurements], float | None]


SENSORS: tuple[PVLSensorDescription, ...] = (
    PVLSensorDescription(key="water_level", name="PVL Reservoir Slapy Water Level", device_class=SensorDeviceClass.DISTANCE, native_unit_of_measurement=UnitOfLength.METERS, suggested_display_precision=2, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda data: data.water_level_m),
    PVLSensorDescription(key="volume", name="PVL Reservoir Slapy Volume", device_class=SensorDeviceClass.VOLUME, native_unit_of_measurement=UnitOfVolume.CUBIC_METERS, suggested_display_precision=0, value_fn=lambda data: data.volume_million_m3 * 1_000_000 if data.volume_million_m3 is not None else None),
    PVLSensorDescription(key="inflow", name="PVL Reservoir Slapy Inflow", device_class=SensorDeviceClass.VOLUME_FLOW_RATE, native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND, suggested_display_precision=2, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda data: data.inflow_m3_s),
    PVLSensorDescription(key="outflow", name="PVL Reservoir Slapy Outflow", device_class=SensorDeviceClass.VOLUME_FLOW_RATE, native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND, suggested_display_precision=2, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda data: data.outflow_m3_s),
    PVLSensorDescription(key="precipitation_24h", name="PVL Reservoir Slapy Precipitation 24h", device_class=SensorDeviceClass.PRECIPITATION, native_unit_of_measurement="mm", suggested_display_precision=1, value_fn=lambda data: data.precipitation_24h_mm),
    PVLSensorDescription(key="air_temperature", name="PVL Reservoir Slapy Air Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=1, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda data: data.air_temperature_c),
)


async def async_setup_entry(hass: HomeAssistant, entry: PVLConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up PVL sensors from the shared coordinator."""
    coordinator = entry.runtime_data
    async_add_entities(PVLReservoirSensor(coordinator, description) for description in SENSORS)


class PVLReservoirSensor(CoordinatorEntity[PVLDataCoordinator], SensorEntity):
    """Represent one current value from the PVL page."""

    entity_description: PVLSensorDescription

    def __init__(self, coordinator: PVLDataCoordinator, description: PVLSensorDescription) -> None:
        """Initialize a sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{DOMAIN}_{RESERVOIR_ID}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, RESERVOIR_ID)},
            "name": RESERVOIR_NAME,
            "manufacturer": "Povodí Vltavy",
            "model": "Public reservoir measurements",
        }

    @property
    def native_value(self) -> float | None:
        """Return the latest numeric value, or None for an empty PVL field."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Mark an entity unavailable when PVL leaves its value blank."""
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the source measurement time on the level sensor."""
        if self.entity_description.key == "water_level" and self.coordinator.data is not None:
            return {"measurement_time": self.coordinator.data.measured_at.isoformat()}
        return None
