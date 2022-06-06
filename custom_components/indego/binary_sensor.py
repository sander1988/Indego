"""Binary sensors for Indego."""
import logging

from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY
from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT as BINARY_SENSOR_FORMAT,
)
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    CONF_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_UPDATED, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the binary sensor platform."""
    async_add_devices(
        [
            device
            for device in hass.data[DOMAIN].entities.values()
            if isinstance(device, IndegoBinarySensor)
        ]
    )
    return True


class IndegoBinarySensor(BinarySensorEntity, RestoreEntity):
    """Class for Indego Binary Sensors."""

    def __init__(self, entity_id, name, icon, device_class, attributes):
        """Initialize a binary sensor.

        Args:
            serial (str): serial of the mower
            entity_id (str): entity_id of the sensor
            name (str): name of the sensor
            icon (str, Callable): string or function for icons
            device_class (str): device class of the sensor

        """
        self.entity_id = BINARY_SENSOR_FORMAT.format(entity_id)
        self._unique_id = entity_id
        self._name = name
        self._updateble_icon = callable(icon)
        if self._updateble_icon:
            self._icon_func = icon
            self._icon = icon(None)
        else:
            self._icon = icon
        self._device_class = device_class
        self._attr = {key: None for key in attributes}
        self._should_poll = False
        self._state = None
        self._is_on = None

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

    @callback
    def _schedule_immediate_update(self):
        """Schedule update."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return self._unique_id

    @property
    def account(self) -> str:
        """Return device account."""
        return self._account

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        return self._icon

    @property
    def extra_state_attributes(self) -> dict:
        """Return attributes."""
        return self._attr

    def add_attribute(self, attr: dict):
        """Update attributes."""
        self._attr.update(attr)

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
            # if self._updateble_icon:
            #     self._icon = self._icon_func(self._state)
            self.async_schedule_update_ha_state()
