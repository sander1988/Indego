"""Class for Indego Sensors."""
import logging

from homeassistant.components.sensor import SensorEntity, ENTITY_ID_FORMAT as SENSOR_FORMAT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.icon import icon_for_battery_level
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
            if isinstance(entity, IndegoSensor)
        ]
    )


class IndegoSensor(IndegoEntity, SensorEntity):
    """Class for Indego Sensors."""

    def __init__(self, entity_id, name, icon, device_class, unit_of_measurement, attributes, device_info: DeviceInfo, translation_key: str = None):
        """Initialize a sensor.

        Args:
            entity_id (str): entity_id of the sensor
            name (str): name of the sensor
            icon (str, Callable): string or function for icons
            device_class (str): device class of the sensor
            unit_of_measurement (str): unit of measurement of the sensor
            device_info (DeviceInfo): Initial device info
            translation_key: Optional translation key for (custom state) translations
        """
        super().__init__(SENSOR_FORMAT.format(entity_id), name, icon, attributes, device_info)

        self._device_class = device_class
        self._unit = unit_of_measurement
        self.charging = False
        self._attr_translation_key = translation_key

    async def async_added_to_hass(self):
        """Once the sensor is added, see if it was there before and pull in that state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()

        if state is None or state.state is None:
            return

        self.state = state.state
        async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @property
    def state(self):
        """Get the state."""
        return self._state

    @state.setter
    def state(self, new):
        """Set the state to new."""
        if self._state != new:
            self._state = new
            self.async_schedule_update_ha_state()

    @property
    def device_class(self) -> str:
        """Return device class."""
        return self._device_class

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        if self._updateble_icon:
            return self._icon_func(self._state)
        if self._icon == "battery":
            return icon_for_battery_level(
                int(self._state) if self._state is not None and (isinstance(self._state, int) or self._state.isdigit()) else None, self.charging
            )
        return self._icon

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit
