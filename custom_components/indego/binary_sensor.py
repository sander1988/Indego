from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from . import Indego as API, GLOB_MOWER_NAME, DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the binary sensor platform."""
    _LOGGER.debug("Setup Indego Binary Sensor Platform")    

    online_sensor_name = GLOB_MOWER_NAME + ' online'
    add_devices([IndegoOnline(API, online_sensor_name)])

    update_available_sensor_name = GLOB_MOWER_NAME + ' update available'
    add_devices([IndegoUpdateAvailable(API, update_available_sensor_name)])

    alert_sensor_name = GLOB_MOWER_NAME + ' alert'
    add_devices([IndegoAlert(API, alert_sensor_name)])

    _LOGGER.debug("Finished Indego Binary Sensor Platform setup!")    

class IndegoOnline(Entity):
    """Indego Online Sensor."""
    def __init__(self, IAPI, device_label):
        """Initialize Online sensor"""
        self._IAPI = IAPI
        self._state = None
        self._device_label = device_label
    @property
    def name(self):
        """Return the name of the sensor."""
        #_LOGGER.debug("Online_name")    
        return self._device_label
    @property
    def state(self):
        return self._IAPI._online
    @property
    def is_on(self):
        """Return if entity is on."""
        #_LOGGER.debug("Online_is_on")    
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:cloud-check'
        return tmp_icon

class IndegoUpdateAvailable(Entity):
    def __init__(self, IAPI, device_label):
        self._IAPI = IAPI
        self._state = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI.update_available
    @property
    def is_on(self):
        return self.state
    @property
    def icon(self):
        tmp_icon = 'mdi:chip'
        return tmp_icon

class IndegoAlert(Entity):
    def __init__(self, IAPI, device_label):
        self._IAPI = IAPI
        self._state = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        if (self._IAPI.alerts_count > 0):
            return True
        else:
            return False
    @property
    def is_on(self):
        return self.state
    @property
    def icon(self):
        tmp_icon = 'mdi:alert-octagram-outline'
        return tmp_icon