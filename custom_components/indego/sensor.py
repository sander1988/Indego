"""Class for Indego Sensors."""
import logging
from datetime import datetime

from homeassistant.components.sensor import ENTITY_ID_FORMAT as SENSOR_FORMAT
from homeassistant.const import CONF_ID, TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_UPDATED, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the sensor platform."""
    async_add_devices(
        [
            device
            for device in hass.data[DOMAIN].entities.values()
            if isinstance(device, IndegoSensor)
        ]
    )
    return True


class IndegoSensor(RestoreEntity):
    """Class for Indego Sensors."""

    def __init__(
        self, entity_id, name, icon, device_class, unit_of_measurement, attributes
    ):
        """Initialize a sensor.

        Args:
            serial (str): serial of the mower
            entity_id (str): entity_id of the sensor
            name (str): name of the sensor
            icon (str, Callable): string or function for icons
            device_class (str): device class of the sensor
            unit_of_measurement (str): unit of measurement of the sensor

        """
        self.entity_id = SENSOR_FORMAT.format(entity_id)
        self._unique_id = entity_id
        self._name = name
        self._updateble_icon = callable(icon)
        if self._updateble_icon:
            self._icon_func = icon
            self._icon = None
        else:
            self._icon = icon
        self._device_class = device_class
        self._unit = unit_of_measurement
        self._attr = {key: None for key in attributes}
        self._state = None
        self._should_poll = False
        self.charging = False

    async def async_added_to_hass(self):
        """Once the sensor is added, see if it was there before and pull in that state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is not None and state.state is not None:
            self.state = state.state
        else:
            return
        async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @callback
    def _schedule_immediate_update(self):
        """Schedule update."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    @property
    def state(self):
        """Get the state."""
        return self._state

    @state.setter
    def state(self, new):
        """Set the state to new."""
        if self._state != new:
            self._state = new
            # if self._updateble_icon:
            #     self._icon = self._icon_func(self._state)
            self.async_schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Get unique_id."""
        return self._unique_id

    @property
    def device_class(self) -> str:
        """Return device class."""
        return self._device_class

    @property
    def extra_state_attributes(self) -> dict:
        """Return attributes."""
        return self._attr

    def add_attribute(self, attr: dict):
        """Update attributes."""
        self._attr.update(attr)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        if self._updateble_icon:
            return self._icon_func(self._state)
        if self._icon == "battery":
            return icon_for_battery_level(
                int(self._state) if self._state is not None else None, self.charging
            )
        return self._icon

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit

    # @property
    # def device_info(self) -> dict:
    #     """Return the device_info."""
    #     return {
    #         "identifiers": {(DOMAIN, self._serial)},
    #         "name": self.name,

    #         "Model": self._IAPI.generic_data.model_description,
    #         "Serial": self._IAPI.generic_data.alm_sn,
    #         "Firmware": self._IAPI.generic_data.alm_firmware_version,
    #         "via_device": (DOMAIN, self._serial),
    #     }
