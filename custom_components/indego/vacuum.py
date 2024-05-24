import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
    STATE_DOCKED,
    STATE_CLEANING,
    STATE_RETURNING,
    STATE_ERROR,
)
from homeassistant.const import (
    STATE_IDLE,
    STATE_PAUSED
)
from homeassistant.components.vacuum import (
    ENTITY_ID_FORMAT as VACUUM_SENSOR_FORMAT,
)

from .const import DOMAIN
from .mixins import IndegoEntity

_LOGGER = logging.getLogger(__name__)

INDEGO_STATE_TO_VACUUM_MAPPING = {
    0: STATE_DOCKED,
    101: STATE_DOCKED,
    257: STATE_DOCKED,
    258: STATE_DOCKED,
    259: STATE_DOCKED,
    260: STATE_DOCKED,
    261: STATE_DOCKED,
    262: STATE_DOCKED,
    263: STATE_DOCKED,
    266: STATE_CLEANING,
    512: STATE_CLEANING,
    513: STATE_CLEANING,
    514: STATE_CLEANING,
    515: STATE_CLEANING,
    516: STATE_CLEANING,
    517: STATE_PAUSED,
    518: STATE_CLEANING,
    519: STATE_IDLE,
    520: STATE_CLEANING,
    521: STATE_CLEANING,
    522: STATE_CLEANING,
    523: STATE_CLEANING,
    524: STATE_CLEANING,
    525: STATE_CLEANING,
    768: STATE_RETURNING,
    769: STATE_RETURNING,
    770: STATE_RETURNING,
    771: STATE_RETURNING,
    772: STATE_RETURNING,
    773: STATE_RETURNING,
    774: STATE_RETURNING,
    775: STATE_RETURNING,
    776: STATE_RETURNING,
    1005: STATE_CLEANING,
    1025: STATE_ERROR,
    1026: STATE_ERROR,
    1027: STATE_ERROR,
    1038: STATE_ERROR,
    1281: STATE_DOCKED,
    1537: STATE_ERROR,
    64513: STATE_DOCKED,
    99999: STATE_ERROR,
}

INDEGO_VACUUM_FEATURES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.BATTERY
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
    """Class to expose the Indego mower a vacuum."""

    def __init__(self, entity_id, name, device_info: DeviceInfo, indego_hub):
        super().__init__(VACUUM_SENSOR_FORMAT.format(entity_id), name, "mdi:robot-mower", None, device_info)

        self._indego_hub = indego_hub
        self._attr_supported_features = INDEGO_VACUUM_FEATURES
        self._attr_indego_state = None
        self._attr_state = None
        self._attr_battery_level = None
        self._attr_battery_charging = False

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
    def indego_state(self) -> int:
        """Get the Indego mower state."""
        return self._attr_indego_state

    @indego_state.setter
    def indego_state(self, indego_state: int):
        """Set the mower state by converting the Indego mower state to a vacuum state."""
        self._attr_indego_state = indego_state
        new_state = INDEGO_STATE_TO_VACUUM_MAPPING[indego_state] \
            if indego_state in INDEGO_STATE_TO_VACUUM_MAPPING \
            else None

        if self._attr_state != new_state:
            self._attr_state = new_state
            self.async_schedule_update_ha_state()
            _LOGGER.debug("Mower/vacuum state updated to: %s", self._attr_state)

            if self._attr_state is None:
                _LOGGER.warning("Received unsupported Indego mower state: %i", indego_state)

    @property
    def battery_level(self) -> int | None:
        """Get the battery level of the mower."""
        return self._attr_battery_level

    @battery_level.setter
    def battery_level(self, level: int):
        """Set the battery level of the mower."""
        try:
            self._attr_battery_level = int(level)
            _LOGGER.debug("Battery level updated to %i%%", self._attr_battery_level)

        except ValueError:
            _LOGGER.debug("Battery level update failed for value: %s", level)
            self._attr_battery_level = None

    @property
    def battery_charging(self) -> bool:
        """Get the battery charging state of the mower."""
        return self._attr_battery_charging

    @battery_charging.setter
    def battery_charging(self, charging: bool):
        """Set the battery charging state of the mower."""
        self._attr_battery_charging = bool(charging)
        _LOGGER.debug("Battery charging state updated to %s", self._attr_battery_charging)

    @property
    def battery_icon(self) -> str:
        """Return the battery icon for the vacuum cleaner."""
        return icon_for_battery_level(
            battery_level=self.battery_level, charging=self.battery_charging
        )
