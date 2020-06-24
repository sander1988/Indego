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

    def __init__(self, serial, entity_id, name, icon, device_class):
        """Initialize a binary sensor.

        Args:
            serial (str): serial of the mower
            entity_id (str): entity_id of the sensor
            name (str): name of the sensor
            icon (str, Callable): string or function for icons
            device_class (str): device class of the sensor

        """
        self._serial = serial
        self.entity_id = BINARY_SENSOR_FORMAT.format(entity_id)
        self._unique_id = entity_id
        self._name = name
        self._icon = icon
        self._device_class = device_class
        self._attr = {}
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
        if isinstance(self._icon, str):
            return self._icon
        return self._icon(self.state)

    @property
    def device_state_attributes(self) -> dict:
        """Return attributes."""
        return self._attr

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
        self._is_on = new_on
        self.async_schedule_update_ha_state()


# class IndegoOnline(Entity):
#     """Indego Online Sensor."""

#     def __init__(self, IAPI, device_label):
#         """Initialize Online sensor"""
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         """Return the name of the sensor."""
#         # _LOGGER.debug("Online_name")
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI._online

#     @property
#     def is_on(self):
#         """Return if entity is on."""
#         # _LOGGER.debug("Online_is_on")
#         return self._state

#     @property
#     def icon(self):
#         """Return the icon for the frontend based on the status."""
#         tmp_icon = "mdi:cloud-check"
#         return tmp_icon


# class IndegoUpdateAvailable(Entity):
#     def __init__(self, IAPI, device_label):
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI.update_available

#     @property
#     def is_on(self):
#         return self.state

#     @property
#     def icon(self):
#         tmp_icon = "mdi:chip"
#         return tmp_icon


# class IndegoAlert(Entity):
#     def __init__(self, IAPI, device_label):
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         if self._IAPI.alerts_count > 0:
#             return True
#         else:
#             return False

#     @property
#     def is_on(self):
#         return self.state

#     @property
#     def icon(self):
#         tmp_icon = "mdi:alert-octagram-outline"
#         return tmp_icon
