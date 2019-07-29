from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from . import IndegoAPI_Instance as API, CONF_MOWER_NAME, DOMAIN
import logging

MOWING_MODE = {
    'smart':    'SmartMowing',
    'calendar': 'Calendar',
    'manual':   'Manual'
}

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.debug("Setup Sensor Platform")    

    mower_state_sensor_name = CONF_MOWER_NAME + '_mower_state'
    add_devices([IndegoStateSensor(mower_state_sensor_name)])
    
    lawn_mowed_sensor_name = CONF_MOWER_NAME + '_lawn_mowed'
    add_devices([IndegoLawnMowedSensor(lawn_mowed_sensor_name)])

    mower_alert_sensor_name = CONF_MOWER_NAME + '_mower_alert'
    add_devices([IndegoAlertSensor(mower_alert_sensor_name)])

    mowing_mode_sensor_name = CONF_MOWER_NAME + '_mowing_mode'
    add_devices([IndegoMowingMode(mowing_mode_sensor_name)])

    _LOGGER.debug("Finished Sensor Platform setup!")    

class IndegoStateSensor(Entity):
    """Indego State Sensor."""

    def __init__(self, device_label):
        """Initialize state sensor"""
        self._state = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device_label

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        return 'mdi:robot'

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.debug("Update Sensor")    
        self._state = API.getState()
        _LOGGER.debug("Finished Sensor update")    

class IndegoLawnMowedSensor(Entity):
    """Indego Lawn Mowed Sensor."""

    def __init__(self, device_label):
        """Initialize state sensor"""
        self._state = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device_label

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return '%'

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        return 'mdi:percent'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug("Update Lawn mowed")    
        self._state = API.getMowed()
        _LOGGER.debug("Finished Lawn mowed update")    

class IndegoAlertSensor(Entity):
    """Indego Alert Sensor."""

    def __init__(self, device_label):
        """Initialize alert sensor"""
        self._state = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device_label

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:check-circle-outline'
        if self._state:
            if self._state > 0:
                tmp_icon = 'mdi:alert-outline'
            else:
                tmp_icon = 'mdi:check-circle-outline'
        return tmp_icon
    
    def update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug("Update Alert State")    
        self._state = API.getAlerts()
        _LOGGER.debug("Finished Alert update")    

class IndegoMowingMode(Entity):
    """Indego Mowing Mode Sensor."""

    def __init__(self, device_label):
        """Initialize mowing mode sensor"""
        self._state = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device_label

    @property
    def state(self):
        """Return the mowing mode."""
        return self._state

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        tmp_icon = 'mdi:alpha-m-circle-outline'
        return tmp_icon
    
    def update(self):
        """Fetch mowing mode for the sensor.
        """
        _LOGGER.debug("Update Mowing Mode State")    
        tmp_mode = API.getMowingMode()
        _LOGGER.debug(f"Mowing Mode State = {tmp_mode}")    
        self._state = MOWING_MODE.get(tmp_mode)
        _LOGGER.debug("Finished update mowing mode")    