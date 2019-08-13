from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from . import IndegoAPI_Instance as API, Mower as mower, GLOB_MOWER_NAME, DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.debug("Setup Sensor Platform with all sensors")    

    mower_state_sensor_name = GLOB_MOWER_NAME + ' mower state'
    add_devices([IndegoStateSensor(API, mower_state_sensor_name)])

    mower_state_sensor_name = GLOB_MOWER_NAME + ' mower state detail'
    add_devices([IndegoStateSensorDetail(API, mower_state_sensor_name)])
    
    lawn_mowed_sensor_name = GLOB_MOWER_NAME + ' lawn mowed'
    add_devices([IndegoLawnMowedSensor(API, lawn_mowed_sensor_name)])

    runtime_total_sensor_name = GLOB_MOWER_NAME + ' runtime total'
    add_devices([IndegoRuntimeTotal(API, runtime_total_sensor_name)])

    mowing_mode_sensor_name = GLOB_MOWER_NAME + ' mowing mode'
    add_devices([IndegoMowingMode(API, mowing_mode_sensor_name)])

    battery_sensor_name = GLOB_MOWER_NAME + ' battery %'
    add_devices([IndegoBattery(API, battery_sensor_name)])

    batt_voltage_sensor_name = GLOB_MOWER_NAME + ' battery V'
    add_devices([IndegoBatt_Voltage(API, batt_voltage_sensor_name)])

    mower_alert_sensor_name = GLOB_MOWER_NAME + ' mower alert'
    add_devices([IndegoAlertSensor(API, mower_alert_sensor_name)])

    _LOGGER.debug("Finished Sensor Platform setup!")    

class IndegoStateSensor(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI._mower_state_description
    @property
    def icon(self):
        return 'mdi:robot'
    #def update(self):
    #    self._mower.update(self)
    @property
    def device_state_attributes(self):
        return {
            'Model':    self._IAPI._model_description,
            'Serial':   self._IAPI._serial,
            'Firmware': self._IAPI._alm_firmware_version
            }

class IndegoStateSensorDetail(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI._mower_state_description_detailed
    @property
    def icon(self):
        return 'mdi:robot'
    #def update(self):
    #    self._mower.update(self)
    @property
    def device_state_attributes(self):
        return {
            'State #':  self._IAPI._mower_state,
            'State description':  self._IAPI._mower_state_description_detailed
            }
            

class IndegoLawnMowedSensor(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def unit_of_measurement(self):
        return '%'
    @property
    def icon(self):
        return 'mdi:percent'
    @property
    def state(self):
        return self._IAPI._mowed
    #def update(self):
    #    self._mower.update(self)
    @property
    def device_state_attributes(self):
        operation_unit = str(self._IAPI._session_operation) + " min"
        cut_unit       = str(self._IAPI._session_cut) + " min"
        charge_unit    = str(self._IAPI._session_charge) + " min"
        return {
            'Last session Operation': operation_unit,
            'Last session Cut':       cut_unit,
            'Last session Charge':    charge_unit
            }
    def should_poll(self):
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False


class IndegoRuntimeTotal(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI._total_operation
    @property
    def unit_of_measurement(self):
        return 'h'
    @property
    def icon(self):
        tmp_icon = 'mdi:information-outline'
        return tmp_icon
    #def update(self):
    #    self._mower.update(self)
    @property
    def device_state_attributes(self):
        operation_unit = str(self._IAPI._total_operation) + " h"
        cut_unit    = str(self._IAPI._total_cut) + " h"
        charge_unit  = str(self._IAPI._total_charge) + " h"
        return {
            'Total operation time': operation_unit,
            'Total mowing time': cut_unit,
            'Total charging time': charge_unit
            }
    def should_poll(self):
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False


class IndegoMowingMode(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        #return self._IAPI._alm_mode
        return self._IAPI._mowingmode_description
    @property
    def icon(self):
        tmp_icon = 'mdi:alpha-m-circle-outline'
        return tmp_icon
    #def update(self):
    #    #self._IAPI.refresh_devices()
    #    self._mower.update(self)
    def should_poll(self):
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False

class IndegoBattery(Entity):
    def __init__(self, IAPI, device_label):
        self._IAPI                  = IAPI
        self._state                 = None
        self._device_label          = device_label
        self._battery_percent_max   = self._IAPI._battery_percent
        self._battery_percent_min   = self._IAPI._battery_percent
    @property
    def name(self):
        return self._device_label
    @property
    def unit_of_measurement(self):
        return '%'
    @property
    def state(self):
        if (self._IAPI._battery_percent > self._battery_percent_max):
            self._battery_percent_max = self._IAPI._battery_percent
        if (self._IAPI._battery_percent < self._battery_percent_min):
            self._battery_vpercent_min = self._IAPI._battery_percent
        return self._IAPI._battery_percent_adjusted
    @property
    def icon(self):
        tmp_icon = 'mdi:battery-50'
        return tmp_icon
#    def update(self):
#        self._IAPI.refresh_devices()
    @property
    def device_state_attributes(self):
        voltage_unit = str(self._IAPI._battery_voltage) + " V"
        discharge_unit = str(self._IAPI._battery_discharge) + " Ah?"
        ambient_unit = str(self._IAPI._battery_ambient_temp) + " " + TEMP_CELSIUS
        battery_unit = str(self._IAPI._battery_temp) + " " + TEMP_CELSIUS
        raw_unit = str(self._IAPI._battery_percent) + " %"
        max_unit = str(self._battery_percent_max) + " %"
        min_unit = str(self._battery_percent_min) + " %"
        return {
            'Voltage': voltage_unit,
            'Cycles': self._IAPI._battery_cycles,
            'Discharge': discharge_unit,
            'Ambient temp': ambient_unit,
            'Battery temp': battery_unit,
            '(Percent raw)': raw_unit,
            '(Percent max)': max_unit,
            '(Percent min)': min_unit    
            }

class IndegoBatt_Voltage(Entity):
    def __init__(self, IAPI, device_label):
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
        self._battery_voltage_max   = self._IAPI._battery_voltage
        self._battery_voltage_min   = self._IAPI._battery_voltage
            
    @property
    def name(self):
        return self._device_label
    @property
    def unit_of_measurement(self):
        return 'V'
    @property
    def state(self):
        if (self._IAPI._battery_voltage > self._battery_voltage_max):
            self._battery_voltage_max = self._IAPI._battery_voltage
        if (self._IAPI._battery_voltage < self._battery_voltage_min):
            self._battery_voltage_min = self._IAPI._battery_voltage
        return self._IAPI._battery_voltage
    @property
    def icon(self):
        tmp_icon = 'mdi:current-dc'
        return tmp_icon
#    def update(self):
#        """Request an update from the BloomSky API."""
#        self._IAPI.refresh_devices()
    @property
    def device_state_attributes(self):
        max_unit = str(self._battery_voltage_max) + ' V'
        min_unit = str(self._battery_voltage_min) + ' V'
        return {
            'Voltage max': max_unit,
            'Voltage min': min_unit
        }

class IndegoAlertSensor(Entity):
    def __init__(self, IAPI, device_label):
        self._IAPI         = IAPI
        self._state = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI._alerts_count
    @property
    def icon(self):
        tmp_icon = 'mdi:check-circle-outline'
        if self.state:
            if self.state > 0:
                tmp_icon = 'mdi:alert-outline'
            else:
                tmp_icon = 'mdi:check-circle-outline'
        return tmp_icon
#    def update(self):
#        self._state = API.getAlerts()
    @property
    def device_state_attributes(self):
        alert_1 = 'Test'
        alert_2 = 'Test2'
        return {
            self._IAPI._alert1_name: self._IAPI._alert1_error,
            self._IAPI._alert2_name: self._IAPI._alert2_error,
            self._IAPI._alert3_name: self._IAPI._alert3_error
        }

#End of sensor.py