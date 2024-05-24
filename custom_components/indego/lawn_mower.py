import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.lawn_mower import (
    LawnMowerEntity,
    LawnMowerEntityFeature,
    LawnMowerActivity
)
from homeassistant.components.lawn_mower import (
    DOMAIN as LAWN_MOWER_DOMAIN
)

from .const import DOMAIN
from .mixins import IndegoEntity

LAWN_MOWER_DOMAIN_FORMAT = LAWN_MOWER_DOMAIN + ".{}"

_LOGGER = logging.getLogger(__name__)

INDEGO_STATE_TO_LAWN_MOWER_MAPPING = {
    0: LawnMowerActivity.DOCKED,
    101: LawnMowerActivity.DOCKED,
    257: LawnMowerActivity.DOCKED,
    258: LawnMowerActivity.DOCKED,
    259: LawnMowerActivity.DOCKED,
    260: LawnMowerActivity.DOCKED,
    261: LawnMowerActivity.DOCKED,
    262: LawnMowerActivity.DOCKED,
    263: LawnMowerActivity.DOCKED,
    266: LawnMowerActivity.MOWING,
    512: LawnMowerActivity.MOWING,
    513: LawnMowerActivity.MOWING,
    514: LawnMowerActivity.MOWING,
    515: LawnMowerActivity.MOWING,
    516: LawnMowerActivity.MOWING,
    517: LawnMowerActivity.PAUSED,
    518: LawnMowerActivity.MOWING,
    519: LawnMowerActivity.PAUSED,
    520: LawnMowerActivity.MOWING,
    521: LawnMowerActivity.MOWING,
    522: LawnMowerActivity.MOWING,
    523: LawnMowerActivity.MOWING,
    524: LawnMowerActivity.MOWING,
    525: LawnMowerActivity.MOWING,
    768: LawnMowerActivity.MOWING,
    769: LawnMowerActivity.MOWING,
    770: LawnMowerActivity.MOWING,
    771: LawnMowerActivity.MOWING,
    772: LawnMowerActivity.MOWING,
    773: LawnMowerActivity.MOWING,
    774: LawnMowerActivity.MOWING,
    775: LawnMowerActivity.MOWING,
    776: LawnMowerActivity.MOWING,
    1005: LawnMowerActivity.MOWING,
    1025: LawnMowerActivity.ERROR,
    1026: LawnMowerActivity.ERROR,
    1027: LawnMowerActivity.ERROR,
    1038: LawnMowerActivity.ERROR,
    1281: LawnMowerActivity.DOCKED,
    1537: LawnMowerActivity.ERROR,
    64513: LawnMowerActivity.DOCKED,
    99999: LawnMowerActivity.ERROR,
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

    def __init__(self, entity_id, name, device_info: DeviceInfo, indego_hub):
        super().__init__(LAWN_MOWER_DOMAIN_FORMAT.format(entity_id), name, None, None, device_info)
        self._indego_hub = indego_hub

        self._attr_supported_features = INDEGO_LAWN_MOWER_FEATURES
        self._attr_indego_state = None
        self._attr_state = None

    async def async_start_mowing(self) -> None:
        await self._indego_hub.async_send_command_to_client("mow")

    async def async_dock(self) -> None:
        await self._indego_hub.async_send_command_to_client("returnToDock")

    async def async_pause(self) -> None:
        await self._indego_hub.async_send_command_to_client("pause")

    @property
    def indego_state(self) -> int:
        return self._attr_indego_state

    @indego_state.setter
    def indego_state(self, indego_state: int):
        self._attr_indego_state = indego_state

        new_activity = INDEGO_STATE_TO_LAWN_MOWER_MAPPING.get(indego_state)
        if self._attr_activity != new_activity:
            self._attr_activity = new_activity
            self.async_schedule_update_ha_state()
            _LOGGER.debug("Mower state/activity updated to: %s", self._attr_activity)

            if self._attr_activity is None:
                _LOGGER.warning("Received unsupported Indego mower state: %i", indego_state)
