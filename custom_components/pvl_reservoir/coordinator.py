"""Fetch current reservoir data from the PVL measurements page."""

from __future__ import annotations

import asyncio
import logging

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PVLMeasurements, PVLPageError, parse_current_measurements
from .const import DOMAIN, PVL_MEASUREMENTS_URL, REQUEST_TIMEOUT_SECONDS, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class PVLDataCoordinator(DataUpdateCoordinator[PVLMeasurements]):
    """Coordinate the ten-minute fetch of current PVL measurements."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> PVLMeasurements:
        """Download one HTML page and parse its current values."""
        try:
            async with self._session.get(
                PVL_MEASUREMENTS_URL,
                headers={"Accept": "text/html,application/xhtml+xml"},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"PVL returned HTTP status {response.status}")
                page = await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Unable to retrieve PVL measurements: {err}") from err
        try:
            return parse_current_measurements(page)
        except PVLPageError as err:
            raise UpdateFailed(f"Unable to parse the PVL measurements page: {err}") from err
