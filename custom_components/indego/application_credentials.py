from .const import OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from .api import IndegoLocalOAuth2Implementation

from homeassistant.components.application_credentials import AuthorizationServer, ClientCredential
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import HomeAssistant

async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return custom auth implementation."""

    # Secret needs to be unset or auth fails.
    # But ClientCredential() fail to store when it's set to None.
    # So we store "" in the config_flow.py and clear it here before use.
    credential.client_secret = None

    return IndegoLocalOAuth2Implementation(
        hass,
        auth_domain,
        credential,
        AuthorizationServer(
            authorize_url=OAUTH2_AUTHORIZE,
            token_url=OAUTH2_TOKEN,
        ),
    )
