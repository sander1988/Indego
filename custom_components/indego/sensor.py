from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from . import Indego as API, Mower as mower, GLOB_MOWER_NAME, DOMAIN
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.debug("Setup Indego Sensor Platform with all sensors")    

    mower_state_sensor_name = GLOB_MOWER_NAME + ' mower state'
    add_devices([IndegoStateSensor(API, mower_state_sensor_name)])

    mower_state_detail_sensor_name = GLOB_MOWER_NAME + ' mower state detail'
    add_devices([IndegoStateSensorDetail(API, mower_state_detail_sensor_name)])

    battery_sensor_name = GLOB_MOWER_NAME + ' battery %'
    add_devices([IndegoBattery(API, battery_sensor_name)])

    lawn_mowed_sensor_name = GLOB_MOWER_NAME + ' lawn mowed'
    add_devices([IndegoLawnMowedSensor(API, lawn_mowed_sensor_name)])

    last_completed_mow_sensor_name = GLOB_MOWER_NAME + ' last completed'
    add_devices([IndegoLastCompletedMowSensor(API, last_completed_mow_sensor_name)])

    next_mow_sensor_name = GLOB_MOWER_NAME + ' next mow'
    add_devices([IndegoNextMowSensor(API, next_mow_sensor_name)])

    mowing_mode_sensor_name = GLOB_MOWER_NAME + ' mowing mode'
    add_devices([IndegoMowingMode(API, mowing_mode_sensor_name)])

    runtime_total_sensor_name = GLOB_MOWER_NAME + ' runtime total'
    add_devices([IndegoRuntimeTotal(API, runtime_total_sensor_name)])

    mower_alert_sensor_name = GLOB_MOWER_NAME + ' mower alert'
    add_devices([IndegoAlertSensor(API, mower_alert_sensor_name)])


    _LOGGER.debug("Finished Sensor Platform setup!")    

class IndegoStateSensor(Entity):
    def __init__(self, IAPI, device_label):
        _LOGGER.debug("Indego State Sensor setup!")
        _LOGGER.debug(f"device Label : {device_label}")
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
        _LOGGER.debug(f"state : {self._IAPI.state.state}")
        _LOGGER.debug(f"state_description : {self._IAPI.state_description}")
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI.state_description
    @property
    def icon(self):
        return 'mdi:robot'
    @property
    def device_state_attributes(self):
        return {
            'Model':  self._IAPI.generic_data.model_description,
            'Serial':  self._IAPI.generic_data.alm_sn,
            'Firmware':  self._IAPI.generic_data.alm_firmware_version
        }

class IndegoStateSensorDetail(Entity):
    def __init__(self, IAPI, device_label):
        _LOGGER.debug("Indego State Sensor Detail setup!")
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
        _LOGGER.debug(f"state : {self._IAPI.state.state}")
        _LOGGER.debug(f"state_description2 : {self._IAPI.state_description}")
        _LOGGER.debug(f"state_detail : {self._IAPI.state_description_detail}")
    @property
    def name(self):
        return self._device_label
    @property
    def state(self):
        return self._IAPI.state_description_detail
    @property
    def icon(self):
        return 'mdi:robot'
    @property
    def device_state_attributes(self):
        return {
            'State #':  self._IAPI.state.state,
            'State description':  self._IAPI.state_description_detail,
            'Model #':  self._IAPI.generic_data.bareToolnumber
        }

class IndegoBattery(Entity):
    def __init__(self, IAPI, device_label):
        _LOGGER.debug("Indego Battery Sensor setup!")
        self._IAPI                  = IAPI
        self._state                 = None
        self._device_label          = device_label
        #self._battery_percent_max   = self._IAPI._battery_percent
        #self._battery_percent_min   = self._IAPI._battery_percent
        _LOGGER.debug(f"percent_adjusted: {self._IAPI.operating_data.battery.percent_adjusted}")
    @property
    def name(self):
        return self._device_label
    @property
    def unit_of_measurement(self):
        return '%'
    @property
    def state(self):
        return self._IAPI.operating_data.battery.percent_adjusted
    @property
    def icon(self):
        tmp_icon = 'mdi:battery-50'
        return tmp_icon
    @property
    def device_state_attributes(self):
        return {
            'Voltage':      str(self._IAPI.operating_data.battery.voltage) + " V",
            'Discharge':    str(self._IAPI.operating_data.battery.discharge) + " Ah",
            'Cycles':       str(self._IAPI.operating_data.battery.cycles),
            'Battery temp': str(self._IAPI.operating_data.battery.battery_temp) + " " + TEMP_CELSIUS,
            'Ambient temp': str(self._IAPI.operating_data.battery.ambient_temp) + " " + TEMP_CELSIUS
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
        return self._IAPI.state.mowed
    @property
    def device_state_attributes(self):
        return {
            'Last session Operation': str(self._IAPI.state.runtime.session.operate) + " min",
            'Last session Cut':       str(self._IAPI.state.runtime.session.cut) + " min",
            'Last session Charge':    str(self._IAPI.state.runtime.session.charge) + " min",
            'Last completed Mow':    str(self._IAPI.last_completed_mow),
            'Next Mow':  str(self._IAPI.next_mow)
        }

class IndegoLastCompletedMowSensor(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def icon(self):
        return 'mdi:cash-100'
    @property
    def state(self):
        return self._IAPI.last_completed_mow

class IndegoNextMowSensor(Entity):
    def __init__(self, IAPI, device_label):
        self._mower        = mower
        self._IAPI         = IAPI
        self._state        = None
        self._device_label = device_label
    @property
    def name(self):
        return self._device_label
    @property
    def icon(self):
        return 'mdi:chevron-right'
    @property
    def state(self):
        return self._IAPI.next_mow
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
        return self._IAPI.generic_data.mowing_mode_description
    @property
    def icon(self):
        tmp_icon = 'mdi:alpha-m-circle-outline'
        return tmp_icon

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
        return self._IAPI.state.runtime.total.operate
    @property
    def unit_of_measurement(self):
        return 'h'
    @property
    def icon(self):
        tmp_icon = 'mdi:information-outline'
        return tmp_icon
    @property
    def device_state_attributes(self):
        return {
            'Total operation time': str(self._IAPI.state.runtime.total.operate) + " h",
            'Total mowing time':    str(self._IAPI.state.runtime.total.cut) + " h",
            'Total charging time':  str(self._IAPI.state.runtime.total.charge) + " h"
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
        return self._IAPI.alerts_count
    @property
    def icon(self):
        tmp_icon = 'mdi:check-circle-outline'
        if self.state:
            if self.state > 0:
                tmp_icon = 'mdi:alert-outline'
            else:
                tmp_icon = 'mdi:check-circle-outline'
        return tmp_icon
#    @property
#    def device_state_attributes(self):
#        if (self._IAPI._alert3_time != None ):
#            return {
#                "ID: " + self._IAPI._alert1_id: str(self._IAPI._alert1_error),
#                self._IAPI._alert1_time: str(self._IAPI._alert1_friendly_description),
#                "ID: " + self._IAPI._alert2_id: str(self._IAPI._alert2_error),
#                self._IAPI._alert2_time: str(self._IAPI._alert2_friendly_description),
#                "ID: " + self._IAPI._alert3_id: str(self._IAPI._alert3_error),
#                self._IAPI._alert3_time: str(self._IAPI._alert3_friendly_description)
#            }
#        else:
#            if (self._IAPI._alert2_time != None ):
#                return {
#                    "ID: " + self._IAPI._alert1_id: str(self._IAPI._alert1_error),
#                    self._IAPI._alert1_time: str(self._IAPI._alert1_friendly_description),
#                    "ID: " + self._IAPI._alert2_id: str(self._IAPI._alert2_error),
#                    self._IAPI._alert2_time: str(self._IAPI._alert2_friendly_description)
#                }
#            else:
#                if (self._IAPI._alert1_time != None ):
#                    return {
#                        "ID: " + self._IAPI._alert1_id: str(self._IAPI._alert1_error),
#                        self._IAPI._alert1_time: str(self._IAPI._alert1_friendly_description),
#                    }
#    
#End of sensor.py