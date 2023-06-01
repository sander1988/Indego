from homeassistant.components.application_credentials import AuthImplementation
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from typing import cast
import time


class IndegoLocalOAuth2Implementation(
    AuthImplementation,
):
    """Indego Local OAuth2 implementation."""
    pass

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        return "com.bosch.indegoconnect://login"


class IndegoOAuth2Session(OAuth2Session):
    """Indego OAuth2 session implementation."""

    @property
    def valid_token(self) -> bool:
        """Return if token is still valid."""

        # The Bosch OAuth server returns an access and refresh token with the same value of 1 day (86400). Misconfiguration?
        # HomeAssistant only refreshes when the access token is expired (actually 20 seconds before expiring; see CLOCK_OUT_OF_SYNC_MAX_SEC).
        # So this could result in token refresh failure and the API start to respond with 400 Bad Request (which requires to the user to reauthenticate).
        # To prevent this we override the default implementation here and set it to expire 12 hours before the real expire time.
        # This means the token is refreshed twice a day.
        #
        # NOTE: The 400 Bad Request issue could still happen if HomeAssistant (or network connection) is offline for more than 12 hours. We can't ḟix this.
        #
        return (
            cast(float, self.token["expires_at"])
            > time.time() + 43200
        )
