from homeassistant.components.application_credentials import AuthImplementation

class IndegoLocalOAuth2Implementation(
    AuthImplementation,
):
    """Indego Local OAuth2 implementation."""
    pass

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        return "com.bosch.indegoconnect://login"
