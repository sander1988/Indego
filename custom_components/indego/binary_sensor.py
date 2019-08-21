from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from . import IndegoAPI_Instance as API, CONF_MOWER_NAME, DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the binary sensor platform."""
    _LOGGER.debug("Setup Binary Sensor Platform")    

    update_available_sensor_name = CONF_MOWER_NAME + ' update available'
    add_devices([IndegoUpdateAvailable(API, update_available_sensor_name)])

    _LOGGER.debug("Finished Binary Sensor Platform setup!")    

class IndegoUpdateAvailable(Entity):
    """Indego Update Available Sensor."""

    def __init__(self, IAPI, device_label):
        """Initialize Update Avaliable sensor"""
        self._IAPI = IAPI
        self._state = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device_label

    @property
    def state(self):
        """Return the user adjustment."""
        #return self._state
        return self._IAPI._firmware_available

    @property
    def is_on(self):
        """Return if entity is on."""
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:check-decagram'
        #if self._state:
        #    if self._state = '1':
        #        tmp_icon = 'mdi:alert-decagram'
        #else:
        #    tmp_icon = 'mdi:check-decagram'
        return tmp_icon

    def update(self):
        """Request an update from the BloomSky API."""
        self._IAPI.refresh_devices()