from typing import Final, Any
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.components.application_credentials import ClientCredential, async_import_client_credential, DOMAIN as AC_DOMAIN, DATA_STORAGE as AC_DATA_STORAGE

from pyIndego import IndegoAsyncClient

from .const import (
    DOMAIN,
    CONF_MOWER_SERIAL,
    CONF_MOWER_NAME,
    OAUTH2_CLIENT_ID
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

# TODO: Reimplement mower selection in after auth.


class IndegoFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle a config flow."""

    DOMAIN = DOMAIN
    VERSION = 1
    _config = {}
    _mower_serials = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": "openid profile email offline_access https://prodindego.onmicrosoft.com/indego-mobile-api/Indego.Mower.User"}

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow start."""

        # Create the OAuth application credentials entry in HA.
        # No need to ask the user for input, settings are the same for everyone.
        credentials = self.hass.data[AC_DOMAIN][AC_DATA_STORAGE].async_client_credentials(DOMAIN)
        if DOMAIN not in credentials:
            try:
                _LOGGER.debug("Application credentials do NOT exist, creating...")
                await async_import_client_credential(
                    self.hass,
                    DOMAIN,
                    ClientCredential(OAUTH2_CLIENT_ID, "", DOMAIN)
                )
                _LOGGER.debug("OK: Imported OAuth client credentials")
            except Exception as exc:
                _LOGGER.error("Failed to create application credentials! Reason: %s", str(exc))
                raise
        else:
            _LOGGER.debug("Application credentials found, NOT creating")

        return await super().async_step_pick_implementation(user_input)

    # async def async_step_user(
    #     self, user_input: dict[str, Any] | None = None
    # ) -> FlowResult:
    #     """Handle a flow step where we configure the Bosch Indego account credentials."""
    #
    #     errors = {}
    #     if user_input is not None:
    #         api_client = IndegoAsyncClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
    #         if await api_client.login():
    #             self._config[CONF_USERNAME] = user_input[CONF_USERNAME]
    #             self._config[CONF_PASSWORD] = user_input[CONF_PASSWORD]
    #
    #             self._mower_serials = []
    #             for mower in api_client.mowers_in_account:
    #                 self._mower_serials.append(mower.get("alm_sn"))
    #
    #             return self.async_show_form(
    #                 step_id="mower", data_schema=self._build_mower_options_schema(), last_step=True
    #             )
    #
    #         errors["base"] = "connection_failed"
    #
    #     return self.async_show_form(
    #         step_id="user", data_schema=DATA_SCHEMA, errors=errors, last_step=False
    #     )
    #
    # async def async_step_mower(
    #     self, user_input: dict[str, Any] | None = None
    # ) -> FlowResult:
    #     """Handle a flow select mower step."""
    #
    #     errors = {}
    #     if user_input is not None:
    #         await self.async_set_unique_id(user_input[CONF_MOWER_SERIAL])
    #         self._abort_if_unique_id_configured()
    #
    #         self._config[CONF_MOWER_SERIAL] = user_input[CONF_MOWER_SERIAL]
    #         self._config[CONF_MOWER_NAME] = user_input[CONF_MOWER_NAME]
    #
    #         return self.async_create_entry(title=("%s (%s)" % (user_input[CONF_MOWER_NAME], user_input[CONF_MOWER_SERIAL])), data=self._config)
    #
    #     return self.async_show_form(
    #         step_id="mower", data_schema=self._build_mower_options_schema(), errors=errors, last_step=True
    #     )
    #
    # def _build_mower_options_schema(self):
    #     return vol.Schema(
    #         {
    #             vol.Required(CONF_MOWER_SERIAL): selector.selector({
    #                 "select": {
    #                     "options": self._mower_serials
    #                 }
    #             }),
    #             vol.Required(CONF_MOWER_NAME): str,
    #         })
