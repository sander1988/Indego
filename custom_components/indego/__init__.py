"""The Indego sensor integration."""
import datetime
import homeassistant.helpers.config_validation as cv
import json
import logging
import requests
import threading
import voluptuous as vol
from aiohttp.hdrs import CONTENT_TYPE
from datetime import timedelta
from homeassistant.const import (CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_ID, CONTENT_TYPE_JSON)
from homeassistant.helpers import discovery
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.util import Throttle
from requests.auth import HTTPBasicAuth
from pyIndego import *

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'indego'
DATA_KEY = DOMAIN
CONF_SEND_COMMAND = 'command'
CONF_SMART_MOW = 'enable'
CONF_BATTERY = 'battery'
DEFAULT_NAME = 'Indego'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)
#INDEGO_COMPONENTS = ['sensor', 'binary_sensor']
INDEGO_COMPONENTS = ['sensor']
#UPDATE_INTERVAL = 5  # in minutes
DEFAULT_URL = 'https://api.indego.iot.bosch-si.com:443/api/v1/'
IndegoAPI_Instance = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_ID): cv.string,
        vol.Optional(CONF_BATTERY, default=15): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)

SERVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_SEND_COMMAND): cv.string,
})

SERVICE_SCHEMA2 = vol.Schema({
    vol.Required(CONF_SMART_MOW): cv.string,
})
_LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
_LOGGER.info("Indego init-py")

def setup(hass, config: dict):
    _LOGGER.debug("Setup")    
    global GLOB_MOWER_NAME, GLOB_MOWER_USERNAME, GLOB_MOWER_PASSWORD, GLOB_MOWER_SERIAL, GLOB_MOWER_BATTERY
    GLOB_MOWER_NAME = config[DOMAIN].get(CONF_NAME)
    GLOB_MOWER_USERNAME = config[DOMAIN].get(CONF_USERNAME)
    GLOB_MOWER_PASSWORD = config[DOMAIN].get(CONF_PASSWORD)
    GLOB_MOWER_SERIAL = config[DOMAIN].get(CONF_ID)
    GLOB_MOWER_BATTERY = config[DOMAIN].get(CONF_BATTERY)
    _LOGGER.debug("Idego pyIndego call Mower")
    Mower()

    # Should this be here or in Mower() ???
    for component in INDEGO_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    # Update every minute
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_1m, second=0)

    # Update every 5 minutes
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_5m, minute=range(0, 60, 5), second=0)

    # Update every hour
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_60m, minute=1, second=0)

    # Update battery at user interval
    #now = datetime.datetime.now()
    #track_utc_time_change(hass, Mower.refresh_battery, minute=[1,16,31,46])


    DEFAULT_NAME = None
    SERVICE_NAME = 'mower_command'
    def send_command(call):
        """Handle the service call."""
        name = call.data.get(CONF_SEND_COMMAND, DEFAULT_NAME)
        _LOGGER.debug("Indego.send_command service called")
        _LOGGER.debug("Command: %s", name)
        IndegoAPI_Instance.putCommand(name)
    hass.services.register(DOMAIN, SERVICE_NAME, send_command, schema=SERVICE_SCHEMA)
    
    DEFAULT_NAME = None
    SERVICE_NAME = 'smart_mow'
    def send_smart_mow(call):
        """Handle the service call."""
        name = call.data.get(CONF_SMART_MOW, DEFAULT_NAME)
        _LOGGER.debug("Indego.send_smart_mow service called")
        _LOGGER.debug("Command: %s", str(name))
        IndegoAPI_Instance.putMowMode(name)
    hass.services.register(DOMAIN, SERVICE_NAME, send_smart_mow, schema=SERVICE_SCHEMA2)

    return True    

class Mower():
    _LOGGER.debug("Mower ")
    def __init__(self):
        _LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        _LOGGER.debug("Init Mower start __init__")
        global IndegoAPI_Instance
        _LOGGER.debug(f"API URL = {DEFAULT_URL}")    
        _LOGGER.debug(f"GLOB_MOWER_NAME = {GLOB_MOWER_NAME}")
        #Mask username
        #jresult = GLOB_MOWER_USERNAME
        position = GLOB_MOWER_USERNAME.find('@')
        masked_username = ''
        i = 0
        for x in GLOB_MOWER_USERNAME:
            i = i + 1
            if i <= position:
                masked_username = masked_username + '*'
            else:
                masked_username = masked_username + x
        #_LOGGER.debug(f"GLOB_MOWER_USERNAME = {GLOB_MOWER_USERNAME}")
        _LOGGER.debug(f"GLOB_MOWER_USERNAME = {masked_username}")    
        masked_password = ''
        i = 0
        for x in GLOB_MOWER_PASSWORD:
            masked_password = masked_password + '*'
        #_LOGGER.debug(f"GLOB_MOWER_PASSWORD = {GLOB_MOWER_PASSWORD}")
        _LOGGER.debug(f"GLOB_MOWER_PASSWORD = {masked_password}")
        _LOGGER.debug(f"GLOB_MOWER_SERIAL = {GLOB_MOWER_SERIAL}")
        _LOGGER.debug(f"GLOB_MOWER_BATTERY = {GLOB_MOWER_BATTERY}")

        ### Creating API Instance and Login
        IndegoAPI_Instance = IndegoAPI(GLOB_MOWER_USERNAME, GLOB_MOWER_PASSWORD, GLOB_MOWER_SERIAL)

        ### show vars
        #IndegoAPI_Instance.show_vars()
        
        ### Initial update of variables
        #IndegoAPI_Instance.initial_update()
        #Get data for State, 
        IndegoAPI_Instance.getState()
        IndegoAPI_Instance.MowerStateDescription()
        IndegoAPI_Instance.MowerStateDescriptionDetailed()
        IndegoAPI_Instance.Runtime()
        IndegoAPI_Instance.RuntimeTotal()
        IndegoAPI_Instance.RuntimeSession()
        
        #Get data for MowingMode, modeldata
        IndegoAPI_Instance.getGenericData()
        IndegoAPI_Instance.MowingModeDescription()
        IndegoAPI_Instance.ModelDescription() 
        IndegoAPI_Instance.ModelVoltage() 
        IndegoAPI_Instance.ModelVoltageMin()
        IndegoAPI_Instance.ModelVoltageMax()  

        #Get data for battery, mowingmode
        IndegoAPI_Instance.getOperatingData()
        IndegoAPI_Instance.Battery()
        IndegoAPI_Instance.BatteryPercent()
        IndegoAPI_Instance.BatteryPercentAdjusted()
        IndegoAPI_Instance.BatteryVoltage()
        IndegoAPI_Instance.BatteryCycles()
        IndegoAPI_Instance.BatteryDischarge()
        IndegoAPI_Instance.BatteryAmbientTemp()
        IndegoAPI_Instance.BatteryTemp()

        #Get data for alerts
        IndegoAPI_Instance.getAlerts()
        IndegoAPI_Instance.AlertsCount()
        IndegoAPI_Instance.AlertsDescription()

        #Get last cutting
        IndegoAPI_Instance.getLastCutting()
        IndegoAPI_Instance.getNextCutting()

        ### show vars
        IndegoAPI_Instance.show_vars()

        _LOGGER.debug("Init Mower end __init__")
        _LOGGER.debug("--------------------------------------------------------")

    def refresh_1m(self):
        _LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        _LOGGER.debug("  Refresh Indego sensors every 1m")
        #Get data for State, 
        IndegoAPI_Instance.getState()
        IndegoAPI_Instance.MowerStateDescription()
        IndegoAPI_Instance.MowerStateDescriptionDetailed()
        IndegoAPI_Instance.Runtime()
        IndegoAPI_Instance.RuntimeTotal()
        IndegoAPI_Instance.RuntimeSession()
        


        StateValue = IndegoAPI_Instance._mower_state
        _LOGGER.debug("  Mower StateValue: " + str(StateValue))
        if ((StateValue >= 500) and (StateValue <= 799)) or (StateValue ==257):
            _LOGGER.debug("  StateValue between (500 and 799) or (257): time to call getOperatingData!!!")
            #Get data for battery, mowingmode
            IndegoAPI_Instance.getOperatingData()
            IndegoAPI_Instance.Battery()
            IndegoAPI_Instance.BatteryPercent()
            IndegoAPI_Instance.BatteryPercentAdjusted()
            IndegoAPI_Instance.BatteryVoltage()
            IndegoAPI_Instance.BatteryCycles()
            IndegoAPI_Instance.BatteryDischarge()
            IndegoAPI_Instance.BatteryAmbientTemp()
            IndegoAPI_Instance.BatteryTemp()
        #else:
        #    _LOGGER.debug("  Mower docked. Do not call getOperatingData!!!")

        _LOGGER.debug("--------------------------------------------------------")
        return True

    def refresh_5m(self):
        _LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        _LOGGER.debug("  Refresh Indego sensors every 5m")

        #Get data for MowingMode, modeldata
        IndegoAPI_Instance.getGenericData()
        IndegoAPI_Instance.MowingModeDescription()

        #Get data for alerts
        IndegoAPI_Instance.getAlerts()
        IndegoAPI_Instance.AlertsCount()
        IndegoAPI_Instance.AlertsDescription()

        #Get last cutting
        IndegoAPI_Instance.getLastCutting()
        IndegoAPI_Instance.getNextCutting()

        _LOGGER.debug("  Refresh end")
        _LOGGER.debug("--------------------------------------------------------")
        return True

    def refresh_60m(self):
        _LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        _LOGGER.debug("  Refresh Indego sensors every 60m")
        
        #Get data for MowingMode, modeldata
        IndegoAPI_Instance.getGenericData()
        IndegoAPI_Instance.MowingModeDescription()
        IndegoAPI_Instance.ModelDescription() 
        IndegoAPI_Instance.ModelVoltage() 
        IndegoAPI_Instance.ModelVoltageMin()
        IndegoAPI_Instance.ModelVoltageMax()  
        
         #Get data for battery, mowingmode
        IndegoAPI_Instance.getOperatingData()
        IndegoAPI_Instance.Battery()
        IndegoAPI_Instance.BatteryPercent()
        IndegoAPI_Instance.BatteryPercentAdjusted()
        IndegoAPI_Instance.BatteryVoltage()
        IndegoAPI_Instance.BatteryCycles()
        IndegoAPI_Instance.BatteryDischarge()
        IndegoAPI_Instance.BatteryAmbientTemp()
        IndegoAPI_Instance.BatteryTemp()

        _LOGGER.debug("  Refresh end")
        _LOGGER.debug("--------------------------------------------------------")
        return True

    def refresh_battery(self):
        _LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        _LOGGER.debug("  Refresh Indego battery sensor")
        
        #Get data for battery, mowingmode
        IndegoAPI_Instance.getOperatingData()
        IndegoAPI_Instance.Battery()
        IndegoAPI_Instance.BatteryPercent()
        IndegoAPI_Instance.BatteryPercentAdjusted()
        IndegoAPI_Instance.BatteryVoltage()
        IndegoAPI_Instance.BatteryCycles()
        IndegoAPI_Instance.BatteryDischarge()
        IndegoAPI_Instance.BatteryAmbientTemp()
        IndegoAPI_Instance.BatteryTemp()

        _LOGGER.debug("  Refresh end")
        _LOGGER.debug("--------------------------------------------------------")
        return True