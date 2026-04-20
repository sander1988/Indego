"""System health integration for Indego."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get system health information."""
    from .const import ENTITY_ONLINE
    from .__init__ import IndegoHub

    info: dict[str, Any] = {
        "can_reach_auth_service": system_health.async_check_can_reach_url(
            hass,
            "https://prodindego.b2clogin.com/",
        ),
    }

    # Get mower status from active instances
    try:
        if DOMAIN in hass.data and hass.data[DOMAIN]:
            hub = None
            # Get first active hub (skip special keys like connection_issue_reported, health_registered, services_registered)
            for entry_id, instance in hass.data[DOMAIN].items():
                if isinstance(instance, IndegoHub):
                    hub = instance
                    break

            if hub:
                # Bosch API connectivity (based on last successful update)
                if hub._last_successful_update:
                    import time
                    seconds_since_update = int(time.time() - hub._last_successful_update)
                    if seconds_since_update < 600:  # Less than 10 minutes
                        api_status = "ok"
                        api_value = "Connected"
                    elif seconds_since_update < 3600:  # Less than 1 hour
                        api_status = "warning"
                        api_value = f"Last update: {seconds_since_update // 60} minutes ago"
                    else:
                        api_status = "error"
                        api_value = "No recent updates"
                else:
                    api_status = "unknown"
                    api_value = "No updates yet"

                info["bosch_api_status"] = {
                    "type": "string",
                    "status": api_status,
                    "value": api_value,
                }

                # Bosch service status
                service_status = "ok" if not hub._last_service_error else "error"
                service_value = (
                    "OK"
                    if not hub._last_service_error
                    else f"Last error: {hub._last_service_error}"
                )

                info["bosch_service_status"] = {
                    "type": "string",
                    "status": service_status,
                    "value": service_value,
                }

                # Mower online status
                online_entity = hub.entities.get(ENTITY_ONLINE)
                if online_entity:
                    is_online = online_entity.state
                    info["mower_online"] = {
                        "type": "string",
                        "status": "ok" if is_online else "unknown",
                        "value": "Online" if is_online else "Offline",
                    }

                # Last API response time
                if hub._last_successful_update:
                    import time

                    seconds_ago = int(time.time() - hub._last_successful_update)
                    if seconds_ago < 60:
                        time_str = f"{seconds_ago} seconds ago"
                    elif seconds_ago < 3600:
                        minutes_ago = seconds_ago // 60
                        time_str = f"{minutes_ago} minutes ago"
                    else:
                        hours_ago = seconds_ago // 3600
                        time_str = f"{hours_ago} hours ago"

                    response_status = (
                        "ok" if seconds_ago < 600 else "warning"
                    )  # 10 minutes warning threshold
                    info["last_api_response"] = {
                        "type": "string",
                        "status": response_status,
                        "value": time_str,
                    }

    except Exception as err:
        _LOGGER.warning("Error gathering system health info: %s", err, exc_info=True)

    return info
