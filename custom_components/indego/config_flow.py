from typing import Final, Any
from collections.abc import Mapping
import logging

import voluptuous as vol

from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.components.application_credentials import ClientCredential, async_import_client_credential
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import OptionsFlowWithConfigEntry, ConfigEntry, ConfigFlowResult, SOURCE_REAUTH, UnknownEntry
from homeassistant.core import callback

from pyIndego import IndegoAsyncClient

from .const import (
    DOMAIN,
    CONF_MOWER_SERIAL,
    CONF_MOWER_NAME,
    CONF_EXPOSE_INDEGO_AS_MOWER,
    CONF_EXPOSE_INDEGO_AS_VACUUM,
    CONF_SHOW_ALL_ALERTS,
    CONF_USER_AGENT,
    OAUTH2_CLIENT_ID,
    HTTP_HEADER_USER_AGENT,
    HTTP_HEADER_USER_AGENT_DEFAULT,
    HTTP_HEADER_USER_AGENT_DEFAULTS
)

_LOGGER: Final = logging.getLogger(__name__)


def default_user_agent_in_config(config: dict) -> bool:
    if CONF_USER_AGENT not in config:
        return True

    if config[CONF_USER_AGENT] is None:
        return True

    if config[CONF_USER_AGENT] == "":
        return True

    for default_header in HTTP_HEADER_USER_AGENT_DEFAULTS:
        # Not perfect, but the best what we can do...
        # Test for exact match and header + space, which probably has the version suffix.
        if config[CONF_USER_AGENT] == default_header or config[CONF_USER_AGENT].startswith(default_header + ' '):
            return True
    return False


class IndegoOptionsFlowHandler(OptionsFlowWithConfigEntry):

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self._save_config(user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_USER_AGENT,
                    description={
                        "suggested_value": self.options.get(CONF_USER_AGENT, HTTP_HEADER_USER_AGENT_DEFAULT)
                    },
                ): str,
                vol.Optional(
                    CONF_EXPOSE_INDEGO_AS_MOWER, default=self.options.get(CONF_EXPOSE_INDEGO_AS_MOWER, False)
                ): bool,
                vol.Optional(
                    CONF_EXPOSE_INDEGO_AS_VACUUM, default=self.options.get(CONF_EXPOSE_INDEGO_AS_VACUUM, False)
                ): bool,
                vol.Optional(
                    CONF_SHOW_ALL_ALERTS, default=self.options.get(CONF_SHOW_ALL_ALERTS, False)
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    @callback
    def _save_config(self, data: dict[str, Any]) -> FlowResult:
        """Save the updated options."""

        if CONF_USER_AGENT in data and default_user_agent_in_config(data):
            del data[CONF_USER_AGENT]

        _LOGGER.debug("Updating config options: '%s'", data)

        if CONF_USER_AGENT in data:
            self.hass.data[DOMAIN][self.config_entry.entry_id].client.set_default_header(HTTP_HEADER_USER_AGENT, data[CONF_USER_AGENT])
            _LOGGER.debug("Applied new User-Agent '%s' to Indego API client.", data[CONF_USER_AGENT])

        return self.async_create_entry(title="", data=data)


class IndegoFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle a config flow."""

    DOMAIN = DOMAIN
    VERSION = 1
    _data = {}
    _options = {}
    _mower_serials = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": "openid profile email offline_access https://prodindego.onmicrosoft.com/indego-mobile-api/Indego.Mower.User"
        }

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle config flow start."""

        # Create the OAuth application credentials entry in HA.
        # No need to ask the user for input, settings are the same for everyone.
        try:
            await async_import_client_credential(
                self.hass,
                DOMAIN,
                ClientCredential(OAUTH2_CLIENT_ID, "", DOMAIN)
            )
            _LOGGER.debug("OK: Imported OAuth client credentials (or are already exists)")

        except Exception as exc:
            _LOGGER.error("Failed to create application credentials! Reason: %s", str(exc))
            raise

        # This will launch the HA OAuth (external webpage) opener.
        return await super().async_step_pick_implementation(user_input)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Test connection and load the available mowers."""
        if self.source == SOURCE_REAUTH:
            self._data.update(data)
        else:
            self._data = data
        return await self.async_step_advanced()

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle config flow advanced settings step ."""
        if user_input is not None:
            _LOGGER.debug("Testing API access by retrieving available mowers...")

            api_client = IndegoAsyncClient(
                token=self._data["token"]["access_token"],
                session=async_get_clientsession(self.hass),
                raise_request_exceptions=True
            )
            if not default_user_agent_in_config(user_input):
                self._options[CONF_USER_AGENT] = user_input[CONF_USER_AGENT]
                api_client.set_default_header(HTTP_HEADER_USER_AGENT, user_input[CONF_USER_AGENT])

            self._options[CONF_EXPOSE_INDEGO_AS_MOWER] = user_input[CONF_EXPOSE_INDEGO_AS_MOWER]
            self._options[CONF_EXPOSE_INDEGO_AS_VACUUM] = user_input[CONF_EXPOSE_INDEGO_AS_VACUUM]

            try:
                self._mower_serials = await api_client.get_mowers()
                _LOGGER.debug("Found mowers in account: %s", self._mower_serials)

                if len(self._mower_serials) == 0:
                    return self.async_abort(reason="no_mowers_found")

            except Exception as exc:
                _LOGGER.error("Error while retrieving mower serial in account! Reason: %s", str(exc))
                return self.async_abort(reason="connection_error")

            if self.source == SOURCE_REAUTH:
                if self._data[CONF_MOWER_SERIAL] not in self._mower_serials:
                    return self.async_abort(reason="mower_not_found")

                self.async_set_unique_id(self._data[CONF_MOWER_SERIAL])
                self._abort_if_unique_id_mismatch()

                _LOGGER.debug("Reauth entry with data: '%s'", self._data)
                _LOGGER.debug("Reauth entry with options: '%s'", self._options)

                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates=self._data,
                    options=self._options,
                )

            return await self.async_step_mower()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_USER_AGENT,
                    description={
                        "suggested_value": (self._options[CONF_USER_AGENT] if CONF_USER_AGENT in self._options else HTTP_HEADER_USER_AGENT_DEFAULT)
                    },
                ): str,
                vol.Optional(
                    CONF_EXPOSE_INDEGO_AS_MOWER, default=(self._options[CONF_EXPOSE_INDEGO_AS_MOWER] if CONF_EXPOSE_INDEGO_AS_MOWER in self._options else False)
                ): bool,
                vol.Optional(
                    CONF_EXPOSE_INDEGO_AS_VACUUM, default=(self._options[CONF_EXPOSE_INDEGO_AS_VACUUM] if CONF_EXPOSE_INDEGO_AS_VACUUM in self._options else False)
                ): bool,
            }
        )
        return self.async_show_form(step_id="advanced", data_schema=schema)

    async def async_step_mower(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle config flow choose mower step."""

        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_MOWER_SERIAL])
            self._abort_if_unique_id_configured()

            self._data[CONF_MOWER_SERIAL] = user_input[CONF_MOWER_SERIAL]
            self._data[CONF_MOWER_NAME] = user_input[CONF_MOWER_NAME]

            _LOGGER.debug("Creating entry with data: '%s'", self._data)
            _LOGGER.debug("Creating entry with options: '%s'", self._options)

            return self.async_create_entry(
                title=("%s (%s)" % (user_input[CONF_MOWER_NAME], user_input[CONF_MOWER_SERIAL])),
                data=self._data,
                options=self._options,
            )

        return self.async_show_form(
            step_id="mower",
            data_schema=self._build_mower_options_schema(),
            errors=errors,
            last_step=True
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        current_config = self._get_reauth_entry()

        self._data = dict(current_config.data)
        self._options = dict(current_config.options)

        _LOGGER.debug("Loaded reauth with data: '%s'", self._data)
        _LOGGER.debug("Loaded reauth with options: '%s'", self._options)

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> IndegoOptionsFlowHandler:
        """Get the options flow for this handler."""
        return IndegoOptionsFlowHandler(config_entry)
