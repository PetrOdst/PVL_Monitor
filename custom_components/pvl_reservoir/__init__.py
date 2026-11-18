"""Set up the PVL Reservoir Monitor integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PVLDataCoordinator

type PVLConfigEntry = ConfigEntry[PVLDataCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PVLConfigEntry) -> bool:
    """Set up PVL Reservoir Monitor from a config entry."""
    coordinator = PVLDataCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PVLConfigEntry) -> bool:
    """Unload the integration platforms."""
    return await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
