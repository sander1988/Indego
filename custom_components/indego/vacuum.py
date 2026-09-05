"""Vacuum platform for Bosch Indego mowers."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
    VacuumActivity,
    ENTITY_ID_FORMAT as VACUUM_SENSOR_FORMAT,
)

from .const import DOMAIN
from .mixins import IndegoEntity
from .error_codes import get_mower_state_info, get_error_severity, ErrorSeverity

_LOGGER = logging.getLogger(__name__)

# Mapping from state classification to VacuumActivity
STATE_CLASSIFICATION_TO_ACTIVITY = {
    "docked": VacuumActivity.DOCKED,
    "mowing": VacuumActivity.CLEANING,
    "returning": VacuumActivity.RETURNING,
    "paused": VacuumActivity.PAUSED,
    "idle": VacuumActivity.IDLE,
    "low_power": VacuumActivity.IDLE,
    "maintenance": VacuumActivity.IDLE,
    "updating": VacuumActivity.DOCKED,
    "mapping": VacuumActivity.CLEANING,
    "mapping_paused": VacuumActivity.PAUSED,
    "spot_mowing": VacuumActivity.CLEANING,
    "random_mowing": VacuumActivity.CLEANING,
    "zone_mowing": VacuumActivity.CLEANING,
    "leaving": VacuumActivity.CLEANING,
    "not_mapped": VacuumActivity.ERROR,
    "no_pin": VacuumActivity.ERROR,
    "disabled": VacuumActivity.ERROR,
    "unpaired": VacuumActivity.ERROR,
    "offline": VacuumActivity.ERROR,
    "error": VacuumActivity.ERROR,
    "unknown": VacuumActivity.ERROR,
}

INDEGO_VACUUM_FEATURES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the vacuum platform."""
    async_add_entities(
        [
            entity
            for entity in hass.data[DOMAIN][config_entry.entry_id].entities.values()
            if isinstance(entity, IndegoVacuum)
        ]
    )


class IndegoVacuum(IndegoEntity, StateVacuumEntity):
    """Class to expose the Indego mower as a vacuum."""

    def __init__(self, entity_id, name, device_info: DeviceInfo, indego_hub):
        """Initialize the vacuum entity."""
        super().__init__(
            VACUUM_SENSOR_FORMAT.format(entity_id),
            name,
            "mdi:robot-mower",
            None,
            device_info,
        )
        self._indego_hub = indego_hub
        self._attr_supported_features = INDEGO_VACUUM_FEATURES
        self._attr_indego_state = None
        self._attr_activity = VacuumActivity.ERROR
        self._attr_indego_state_detail = ""

    async def async_start(self) -> None:
        """Start or resume the cleaning task."""
        await self._indego_hub.async_send_command_to_client("mow")

    async def async_pause(self) -> None:
        """Pause the cleaning task."""
        await self._indego_hub.async_send_command_to_client("pause")

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self._indego_hub.async_send_command_to_client("returnToDock")

    @property
    def activity(self) -> VacuumActivity:
        """Return the current activity of the vacuum."""
        return self._attr_activity

    @property
    def indego_state(self) -> int:
        """Get the Indego mower state."""
        return self._attr_indego_state

    @indego_state.setter
    def indego_state(self, indego_state: int):
        """Set the mower state by converting the Indego mower state to a vacuum state."""
        self._attr_indego_state = indego_state
        self._update_activity()

    @property
    def indego_state_detail(self) -> str:
        """Return the detailed Indego state description."""
        return self._attr_indego_state_detail

    @indego_state_detail.setter
    def indego_state_detail(self, state_detail: str):
        """Set the detailed Indego state description and update activity."""
        self._attr_indego_state_detail = state_detail
        self._update_activity()

    def _update_activity(self) -> None:
        """Update the vacuum activity based on state code and details."""
        if self._attr_indego_state is None:
            self._attr_activity = VacuumActivity.ERROR
            return

        # Get state information from error_codes.py
        state_info = get_mower_state_info(str(self._attr_indego_state))

        # Determine activity from state classification
        if state_info:
            state_classification = state_info.get("state", "unknown")
            new_activity = STATE_CLASSIFICATION_TO_ACTIVITY.get(
                state_classification, VacuumActivity.ERROR
            )
        else:
            # Unknown state code -> error
            new_activity = VacuumActivity.ERROR
            _LOGGER.warning(
                "Unknown Indego state code: %d - setting vacuum activity to ERROR",
                self._attr_indego_state,
            )

        # Override for "Returning to" states based on detail text
        if self._attr_indego_state_detail.startswith("Returning to"):
            new_activity = VacuumActivity.RETURNING

        # Check for active unread alerts with severity ERROR or higher
        has_critical_unread = False
        if self._indego_hub and hasattr(self._indego_hub, "_indego_client"):
            alerts = getattr(self._indego_hub._indego_client, "alerts", [])
            for alert in alerts:
                read_status = getattr(alert, "read_status", None)
                is_unread = str(read_status).strip().lower() == "unread" or read_status is False
                if is_unread:
                    error_code = str(getattr(alert, "error_code", ""))
                    severity = get_error_severity(error_code)
                    if severity.value >= ErrorSeverity.ERROR.value:  # ERROR or CRITICAL
                        has_critical_unread = True
                        break

        if has_critical_unread:
            new_activity = VacuumActivity.ERROR

        # Update if changed
        if self._attr_activity != new_activity:
            self._attr_activity = new_activity
            self.async_schedule_update_ha_state()
            _LOGGER.debug(
                "Vacuum activity updated: %s (state: %d, detail: %s, critical_unread: %s)",
                self._attr_activity,
                self._attr_indego_state,
                self._attr_indego_state_detail,
                has_critical_unread,
            )

        # Log unsupported states - only for truly unknown states
        if self._attr_activity == VacuumActivity.ERROR and not has_critical_unread:
            # Check if this state was explicitly classified via STATE_CLASSIFICATION_TO_ACTIVITY
            if state_info and state_info.get("state") in STATE_CLASSIFICATION_TO_ACTIVITY:
                # State is known but classified as ERROR - log as debug
                _LOGGER.debug(
                    "Vacuum state %d classified as ERROR: %s (state: %s)",
                    self._attr_indego_state,
                    self._attr_indego_state_detail,
                    state_info.get("state"),
                )
            else:
                # Truly unknown state - log as warning
                _LOGGER.warning(
                    "Unsupported or unknown state detected: %d (%s)",
                    self._attr_indego_state,
                    self._attr_indego_state_detail,
                )