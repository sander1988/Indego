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

STATE_MOWING = LawnMowerActivity.MOWING
STATE_DOCKED = LawnMowerActivity.DOCKED
STATE_PAUSED = LawnMowerActivity.PAUSED
STATE_ERROR = LawnMowerActivity.ERROR
# The Lawn Mower Entity as a limited amount of states
STATE_IDLE = LawnMowerActivity.PAUSED
STATE_RETURNING = LawnMowerActivity.MOWING


_LOGGER = logging.getLogger(__name__)

INDEGO_STATE_TO_LAWN_MOWER_MAPPING = {
    0: STATE_DOCKED,
    101: STATE_DOCKED,
    257: STATE_DOCKED,
    258: STATE_DOCKED,
    259: STATE_DOCKED,
    260: STATE_DOCKED,
    261: STATE_DOCKED,
    262: STATE_DOCKED,
    263: STATE_DOCKED,
    266: STATE_MOWING,
    512: STATE_MOWING,
    513: STATE_MOWING,
    514: STATE_MOWING,
    515: STATE_MOWING,
    516: STATE_MOWING,
    517: STATE_PAUSED,
    518: STATE_MOWING,
    519: STATE_IDLE,
    520: STATE_MOWING,
    521: STATE_MOWING,
    522: STATE_MOWING,
    523: STATE_MOWING,
    524: STATE_MOWING,
    525: STATE_MOWING,
    768: STATE_RETURNING,
    769: STATE_RETURNING,
    770: STATE_RETURNING,
    771: STATE_RETURNING,
    772: STATE_RETURNING,
    773: STATE_RETURNING,
    774: STATE_RETURNING,
    775: STATE_RETURNING,
    776: STATE_RETURNING,
    1005: STATE_MOWING,
    1025: STATE_ERROR,
    1026: STATE_ERROR,
    1027: STATE_ERROR,
    1038: STATE_ERROR,
    1281: STATE_DOCKED,
    1537: STATE_ERROR,
    64513: STATE_DOCKED,
    99999: STATE_ERROR,
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
        super().__init__(LAWN_MOWER_DOMAIN_FORMAT.format(entity_id), name, "mdi:robot-mower", None, device_info)
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
        self._attr_state = INDEGO_STATE_TO_LAWN_MOWER_MAPPING.get(indego_state)
        _LOGGER.debug("Mower state updated to: %s", self._attr_state)

        if self._attr_state is None:
            _LOGGER.warning("Received unsupported Indego mower state: %i", indego_state)

