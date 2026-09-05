"""Lawn Mower platform for Bosch Indego mowers."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.lawn_mower import (
    LawnMowerEntity,
    LawnMowerEntityFeature,
    LawnMowerActivity,
)
from homeassistant.components.lawn_mower import DOMAIN as LAWN_MOWER_DOMAIN

from .const import DOMAIN
from .mixins import IndegoEntity
from .error_codes import get_mower_state_info, get_error_severity, ErrorSeverity

LAWN_MOWER_DOMAIN_FORMAT = LAWN_MOWER_DOMAIN + ".{}"

_LOGGER = logging.getLogger(__name__)

# Mapping from state classification to LawnMowerActivity
STATE_CLASSIFICATION_TO_ACTIVITY = {
    "docked": LawnMowerActivity.DOCKED,
    "mowing": LawnMowerActivity.MOWING,
    "returning": LawnMowerActivity.RETURNING,
    "paused": LawnMowerActivity.PAUSED,
    "idle": LawnMowerActivity.PAUSED,
    "low_power": LawnMowerActivity.PAUSED,
    "maintenance": LawnMowerActivity.PAUSED,
    "updating": LawnMowerActivity.PAUSED,
    "mapping": LawnMowerActivity.MOWING,
    "mapping_paused": LawnMowerActivity.PAUSED,
    "spot_mowing": LawnMowerActivity.MOWING,
    "random_mowing": LawnMowerActivity.MOWING,
    "zone_mowing": LawnMowerActivity.MOWING,
    "leaving": LawnMowerActivity.MOWING,
    "not_mapped": LawnMowerActivity.ERROR,
    "no_pin": LawnMowerActivity.ERROR,
    "disabled": LawnMowerActivity.ERROR,
    "unpaired": LawnMowerActivity.ERROR,
    "offline": LawnMowerActivity.ERROR,
    "error": LawnMowerActivity.ERROR,
    "unknown": LawnMowerActivity.ERROR,
}

INDEGO_LAWN_MOWER_FEATURES = (
    LawnMowerEntityFeature.START_MOWING
    | LawnMowerEntityFeature.DOCK
    | LawnMowerEntityFeature.PAUSE
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the lawn mower platform."""
    async_add_entities(
        [
            entity
            for entity in hass.data[DOMAIN][config_entry.entry_id].entities.values()
            if isinstance(entity, IndegoLawnMower)
        ]
    )


class IndegoLawnMower(IndegoEntity, LawnMowerEntity):
    """Representation of a Bosch Indego lawn mower."""

    def __init__(self, entity_id, name, device_info: DeviceInfo, indego_hub):
        """Initialize the lawn mower entity."""
        super().__init__(
            LAWN_MOWER_DOMAIN_FORMAT.format(entity_id),
            name,
            None,
            None,
            device_info,
        )
        self._indego_hub = indego_hub
        self._attr_supported_features = INDEGO_LAWN_MOWER_FEATURES
        self._attr_indego_state = None
        self._attr_indego_state_detail = ""
        self._attr_activity = LawnMowerActivity.ERROR

    async def async_start_mowing(self) -> None:
        """Start mowing."""
        await self._indego_hub.async_send_command_to_client("mow")

    async def async_dock(self) -> None:
        """Return to dock."""
        await self._indego_hub.async_send_command_to_client("returnToDock")

    async def async_pause(self) -> None:
        """Pause mowing."""
        await self._indego_hub.async_send_command_to_client("pause")

    @property
    def indego_state(self) -> int:
        """Return the raw Indego state code."""
        return self._attr_indego_state

    @indego_state.setter
    def indego_state(self, indego_state: int):
        """Set the raw Indego state code and update activity."""
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
        """Update the lawn mower activity based on state code and details."""
        if self._attr_indego_state is None:
            self._attr_activity = LawnMowerActivity.ERROR
            return

        # Get state information from error_codes.py
        state_info = get_mower_state_info(str(self._attr_indego_state))

        # Determine activity from state classification
        if state_info:
            state_classification = state_info.get("state", "unknown")
            new_activity = STATE_CLASSIFICATION_TO_ACTIVITY.get(
                state_classification, LawnMowerActivity.ERROR
            )
        else:
            # Unknown state code -> error
            new_activity = LawnMowerActivity.ERROR
            _LOGGER.warning(
                "Unknown Indego state code: %d - setting activity to ERROR",
                self._attr_indego_state,
            )

        # Override for "Returning to" states based on detail text
        if self._attr_indego_state_detail.startswith("Returning to"):
            new_activity = LawnMowerActivity.RETURNING

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
            new_activity = LawnMowerActivity.ERROR

        # Update if changed
        if self._attr_activity != new_activity:
            self._attr_activity = new_activity
            self.async_schedule_update_ha_state()
            _LOGGER.debug(
                "Lawn mower activity updated: %s (state: %d, detail: %s, critical_unread: %s)",
                self._attr_activity,
                self._attr_indego_state,
                self._attr_indego_state_detail,
                has_critical_unread,
            )

        # Log unsupported states - only for truly unknown states
        if self._attr_activity == LawnMowerActivity.ERROR and not has_critical_unread:
            # Check if this state was explicitly classified via STATE_CLASSIFICATION_TO_ACTIVITY
            if state_info and state_info.get("state") in STATE_CLASSIFICATION_TO_ACTIVITY:
                # State is known but classified as ERROR - log as debug
                _LOGGER.debug(
                    "Mower state %d classified as ERROR: %s (state: %s)",
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