import asyncio
import logging
import time
from typing import cast

from homeassistant.components.application_credentials import AuthImplementation
from homeassistant.exceptions import OAuth2TokenRequestTransientError
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session


_LOGGER = logging.getLogger(__name__)


class IndegoLocalOAuth2Implementation(AuthImplementation):
    """Indego Local OAuth2 implementation."""

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        return "com.bosch.indegoconnect://login"


class IndegoOAuth2Session(OAuth2Session):
    """Indego OAuth2 session implementation."""

    TOKEN_REFRESH_BACKOFF = 60

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._token_refresh_backoff_until = 0.0
        self._indego_refresh_lock = asyncio.Lock()

    @property
    def valid_token(self) -> bool:
        """Return if token is still valid."""
        return (
            cast(float, self.token["expires_at"])
            > time.time() + 43200
        )

    async def async_ensure_token_valid(self) -> None:
        """Ensure token is valid while protecting the OAuth endpoint."""

        if self.valid_token:
            return

        if time.monotonic() < self._token_refresh_backoff_until:
            raise OAuth2TokenRequestTransientError()

        async with self._indego_refresh_lock:
            # Another coroutine may have refreshed the token while
            # this coroutine was waiting for the lock.
            if self.valid_token:
                return

            if time.monotonic() < self._token_refresh_backoff_until:
                raise OAuth2TokenRequestTransientError()

            try:
                await super().async_ensure_token_valid()

            except OAuth2TokenRequestTransientError:
                self._token_refresh_backoff_until = (
                    time.monotonic() + self.TOKEN_REFRESH_BACKOFF
                )

                _LOGGER.warning(
                    "OAuth token refresh temporarily failed; "
                    "suppressing further refresh attempts for %d seconds",
                    self.TOKEN_REFRESH_BACKOFF,
                )

                raise

            else:
                self._token_refresh_backoff_until = 0.0
