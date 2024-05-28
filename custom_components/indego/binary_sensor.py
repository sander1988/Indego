"""Binary sensors for Indego."""
import logging

from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT as BINARY_SENSOR_FORMAT,
)
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .mixins import IndegoEntity
from .const import DATA_UPDATED, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    async_add_entities(
        [
            entity
            for entity in hass.data[DOMAIN][config_entry.entry_id].entities.values()
            if isinstance(entity, IndegoBinarySensor)
        ]
    )


class IndegoBinarySensor(IndegoEntity, BinarySensorEntity):
    """Class for Indego Binary Sensors."""

    def __init__(self, entity_id, name, icon, device_class, attributes, device_info: DeviceInfo, translation_key: str = None):
        """Initialize a binary sensor.

        Args:
            entity_id (str): entity_id of the sensor
            name (str): name of the sensor
            icon (str, Callable): string or function for icons
            device_class (str): device class of the sensor
            device_info (DeviceInfo): Initial device info
        """
        super().__init__(BINARY_SENSOR_FORMAT.format(entity_id), name, icon, attributes, device_info)

        self._device_class = device_class
        self._is_on = None
        self._attr_translation_key = translation_key

    async def async_added_to_hass(self):
        """Add sensor to HASS."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()

        if state is not None and state.state is not None:
            if state.state == STATE_ON:
                self._is_on = True
            elif state.state == STATE_OFF:
                self._is_on = False

        async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @property
    def device_class(self) -> str:
        """Return device class."""
        return self._device_class

    @property
    def state(self) -> str:
        """Return the state of the binary sensor."""
        if self.is_on is None:
            return STATE_UNKNOWN

        return STATE_ON if self.is_on else STATE_OFF

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._is_on

    @state.setter
    def state(self, new_on: bool):
        """Set state."""
        if self._is_on != new_on:
            self._is_on = new_on
            self.async_schedule_update_ha_state()
