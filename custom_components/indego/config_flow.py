from typing import Final, Any
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from pyIndego import IndegoAsyncClient

from .const import (
    DOMAIN,
    CONF_MOWER_SERIAL,
    CONF_MOWER_NAME
)

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
    _config = {}
    _mower_serials = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow step where we configure the Bosch Indego account credentials."""

        errors = {}
        if user_input is not None:
            api_client = IndegoAsyncClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            if await api_client.login():
                self._config[CONF_USERNAME] = user_input[CONF_USERNAME]
                self._config[CONF_PASSWORD] = user_input[CONF_PASSWORD]

                self._mower_serials = []
                for mower in api_client.mowers_in_account:
                    self._mower_serials.append(mower.get("alm_sn"))

                return self.async_show_form(
                    step_id="mower", data_schema=self._build_mower_options_schema(), last_step=True
                )

            errors["base"] = "connection_failed"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors, last_step=False
        )

    async def async_step_mower(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow select mower step."""

        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_MOWER_SERIAL])
            self._abort_if_unique_id_configured()

            self._config[CONF_MOWER_SERIAL] = user_input[CONF_MOWER_SERIAL]
            self._config[CONF_MOWER_NAME] = user_input[CONF_MOWER_NAME]

            return self.async_create_entry(title=("%s (%s)" % (user_input[CONF_MOWER_NAME], user_input[CONF_MOWER_SERIAL])), data=self._config)

        return self.async_show_form(
            step_id="mower", data_schema=self._build_mower_options_schema(), errors=errors, last_step=True
        )

    def _build_mower_options_schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_MOWER_SERIAL): selector.selector({
                    "select": {
                        "options": self._mower_serials
                    }
                }),
                vol.Required(CONF_MOWER_NAME): str,
            })
