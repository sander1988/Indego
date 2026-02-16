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
    VacuumActivity
)

from homeassistant.components.vacuum import (
    ENTITY_ID_FORMAT as VACUUM_SENSOR_FORMAT,
)

from .const import DOMAIN
from .mixins import IndegoEntity

_LOGGER = logging.getLogger(__name__)

INDEGO_STATE_TO_VACUUM_MAPPING = {
    0: VacuumActivity.DOCKED,
    101: VacuumActivity.DOCKED,
    257: VacuumActivity.DOCKED,
    258: VacuumActivity.DOCKED,
    259: VacuumActivity.DOCKED,
    260: VacuumActivity.DOCKED,
    261: VacuumActivity.DOCKED,
    262: VacuumActivity.DOCKED,
    263: VacuumActivity.DOCKED,
    266: VacuumActivity.CLEANING,
    512: VacuumActivity.CLEANING,
    513: VacuumActivity.CLEANING,
    514: VacuumActivity.CLEANING,
    515: VacuumActivity.CLEANING,
    516: VacuumActivity.CLEANING,
    517: VacuumActivity.PAUSED,
    518: VacuumActivity.CLEANING,
    519: VacuumActivity.IDLE,
    520: VacuumActivity.CLEANING,
    521: VacuumActivity.CLEANING,
    522: VacuumActivity.CLEANING,
    523: VacuumActivity.CLEANING,
    524: VacuumActivity.CLEANING,
    525: VacuumActivity.CLEANING,
    768: VacuumActivity.RETURNING,
    769: VacuumActivity.RETURNING,
    770: VacuumActivity.RETURNING,
    771: VacuumActivity.RETURNING,
    772: VacuumActivity.RETURNING,
    773: VacuumActivity.RETURNING,
    774: VacuumActivity.RETURNING,
    775: VacuumActivity.RETURNING,
    776: VacuumActivity.RETURNING,
    1005: VacuumActivity.CLEANING,
    1025: VacuumActivity.ERROR,
    1026: VacuumActivity.ERROR,
    1027: VacuumActivity.ERROR,
    1038: VacuumActivity.ERROR,
    1281: VacuumActivity.DOCKED,
    1537: VacuumActivity.ERROR,
    64513: VacuumActivity.DOCKED,
    99999: VacuumActivity.ERROR,
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
