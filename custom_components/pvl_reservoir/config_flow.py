"""Config flow for the public PVL Slapy measurements."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, RESERVOIR_NAME


class PVLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Add the fixed public measurement page for Slapy Reservoir."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, object] | None = None):
        """Create the single Slapy config entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=RESERVOIR_NAME, data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
