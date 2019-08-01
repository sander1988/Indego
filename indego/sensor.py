#from homeassistant.const import TEMP_CELSIUS
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
    _LOGGER.debug("Setup Sensor Platform with all sensors")    

    mower_state_sensor_name = CONF_MOWER_NAME + ' mower state'
    add_devices([IndegoStateSensor(mower_state_sensor_name)])
    
    lawn_mowed_sensor_name = CONF_MOWER_NAME + ' lawn mowed'
    add_devices([IndegoLawnMowedSensor(lawn_mowed_sensor_name)])

    mower_alert_sensor_name = CONF_MOWER_NAME + ' mower alert'
    add_devices([IndegoAlertSensor(mower_alert_sensor_name)])

    mowing_mode_sensor_name = CONF_MOWER_NAME + ' mowing mode'
    add_devices([IndegoMowingMode(mowing_mode_sensor_name)])

    runtime_total_sensor_name = CONF_MOWER_NAME + ' runtime total'
    add_devices([IndegoRuntimeTotal(runtime_total_sensor_name)])
    
    _LOGGER.debug("Finished Sensor Platform setup!")    

class IndegoStateSensor(Entity):
    """Indego State Sensor."""

    def __init__(self, device_label):
        """Initialize state sensor"""
        self._state = None
        self._model = None
        self._serial = None
        self._firmware = None
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
    def model(self):
        """Return the state of the sensor."""
        return self._model

    @property
    def serial(self):
        """Return the state of the sensor."""
        return self._serial

    @property
    def firmware(self):
        """Return the state of the sensor."""
        return self._firmware

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
        self._model = API.getModel()
        self._serial = API.getSerial()
        self._firmware = API.getFirmware()
        _LOGGER.debug("Finished Sensor update")    

    @property
    def device_state_attributes(self):
        """Return the classifier attributes."""
        return {
            'Model':    self._model,
            'Serial':   self._serial,
            'Firmware': self._firmware
            }

class IndegoLawnMowedSensor(Entity):
    """Indego Lawn Mowed Sensor."""

    def __init__(self, device_label):
        """Initialize state sensor"""
        self._state             = None
        self._session_operation = None
        self._session_cut       = None
        self._session_charge    = None
        self._device_label      = device_label
            
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

    @property
    def session_operation(self):
        """Return the session cut time."""
        return self._session_operation

    @property
    def session_cut(self):
        """Return the session cut time."""
        return self._session_cut

    @property
    def session_charge(self):
        """Return the session cut time."""
        return self._session_charge

    def update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug("Update Lawn mowed")    
        self._state = API.getMowed()
        tmp_session = API.getRuntimeSession()
        session_cut = tmp_session['operate']-tmp_session['charge']
        self._session_operation = round(tmp_session['operate']/60)
        self._session_cut = round(session_cut/60)
        self._session_charge = round(tmp_session['charge']/60)
        _LOGGER.debug("Finished Lawn mowed update")    

    @property
    def device_state_attributes(self):
        """Return the classifier attributes."""
        return {
            'Last session Operation': self._session_operation,
            'Last session Cut': self._session_cut,
            'Last session Charge': self._session_charge
            }

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

class IndegoRuntimeTotal(Entity):
    """Indego Runtime Sensor."""

    def __init__(self, device_label):
        """Initialize runtime sensor"""
        self._state        = None
        self._total        = None
        self._mowing       = None
        self._charging     = None
        self._device_label = device_label
            
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device_label

    @property
    def state(self):
        """Return the runtime."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'h'

    @property
    def total(self):
        """Return the runtime."""
        return self._total

    @property
    def mowing(self):
        """Return the runtime."""
        return self._mowing

    @property
    def charging(self):
        """Return the runtime."""
        return self._charging

    @property
    def state(self):
        """Return the runtime."""
        return self._state

    @property
    def icon(self):
        """Return the icon."""
        tmp_icon = 'mdi:information-outline'
        return tmp_icon
    
    def update(self):
        """Fetch runtime sensor."""
        _LOGGER.debug("Update Model Sensor")    
        tmp = API.getRuntimeTotal()
        _LOGGER.debug(f"Runtime = {tmp}")    
        #self._total = API.getRuntimeTotal()
        self._total = round(tmp['operate']/60)
        tmp_mowing = tmp['operate'] - tmp['charge']
        self._mowing = round(tmp_mowing/60)
        self._charging = round(tmp['charge']/60)
        self._state = round(tmp['operate']/60)
        _LOGGER.debug("Finished update runtime sensor")    

    @property
    def device_state_attributes(self):
        """Return the classifier attributes."""
        return {
            'Total operation time': self._total,
            'Total mowing time': self._mowing,
            'Total charging time': self._charging
            }

