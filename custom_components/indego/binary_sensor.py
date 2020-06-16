from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from . import IndegoAPI_Instance as API, GLOB_MOWER_NAME, DOMAIN
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

#    @property
#    def device_class(self):
#        """Return the device class of the sensor."""
#        return connectivity

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:cloud-check'
        return tmp_icon

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
        #_LOGGER.debug("IndegoUpdateAvalable name")
        return self._device_label

    @property
    def state(self):
        #_LOGGER.debug("IndegoUpdateAvalable state")
        #_LOGGER.debug(f"_firmware_available {self._IAPI._firmware_available}")
        #return self._state
        return self._IAPI._firmware_available

    @property
    def is_on(self):
        """Return if entity is on."""
        #_LOGGER.debug("IndegoUpdateAvalable is_on")
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:chip'
        return tmp_icon

class IndegoAlert(Entity):
    """Indego Update Available Sensor."""

    def __init__(self, IAPI, device_label):
        """Initialize Alert sensor"""
        self._IAPI = IAPI
        self._state = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        _LOGGER.debug("IndegoAlert name")
        return self._device_label

    @property
    def state(self):
        _LOGGER.debug("IndegoAlert state")
        _LOGGER.debug(f"_alerts_count {self._IAPI._alerts_count}")
        #return self._state
        if (self._IAPI._alerts_count > 0):
            _LOGGER.debug("Alerts exists, True")
            return True
        else:
            _LOGGER.debug("No alerts, Sensor false!")
            return False
        #return self._IAPI._alerts_count

    @property
    def is_on(self):
        """Return if entity is on."""
        _LOGGER.debug("IndegoAlert is_on")
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:alert-octagram-outline'
        return tmp_icon