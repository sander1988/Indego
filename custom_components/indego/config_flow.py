from typing import Final, Any
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from pyIndego import IndegoAsyncClient

from .const import DOMAIN

from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD
)

DATA_SCHEMA: Final = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

_LOGGER: Final = logging.getLogger(__name__)


class IndegoFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by a user."""

        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

            api_client = IndegoAsyncClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            if await api_client.login():
                return self.async_create_entry(title=user_input[CONF_USERNAME], data=user_input)

            errors["base"] = "connection_failed"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
