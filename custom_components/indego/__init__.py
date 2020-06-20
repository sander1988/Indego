"""Bosch Indego Mower integration."""
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
CONF_SMARTMOWING = 'enable'
CONF_POLLING = 'polling'
DEFAULT_NAME = 'Indego'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)
INDEGO_COMPONENTS = ['sensor', 'binary_sensor']
DEFAULT_URL = 'https://api.indego.iot.bosch-si.com:443/api/v1/'
IndegoAPI_Instance = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_ID): cv.string,
        vol.Optional(CONF_POLLING, default=False): cv.boolean
    }),
}, extra=vol.ALLOW_EXTRA)

SERVICE_SCHEMA_COMMAND = vol.Schema({
    vol.Required(CONF_SEND_COMMAND): cv.string,
})

SERVICE_SCHEMA_SMARTMOWING = vol.Schema({
    vol.Required(CONF_SMARTMOWING): cv.string,
})
_LOGGER.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
_LOGGER.info("Indego init-py")

def setup(hass, config: dict):
    _LOGGER.info("Setup Bosch Indego Mower Integration")    
    global GLOB_MOWER_NAME, GLOB_MOWER_USERNAME, GLOB_MOWER_PASSWORD, GLOB_MOWER_SERIAL, GLOB_MOWER_POLLING
    GLOB_MOWER_NAME = config[DOMAIN].get(CONF_NAME)
    GLOB_MOWER_USERNAME = config[DOMAIN].get(CONF_USERNAME)
    GLOB_MOWER_PASSWORD = config[DOMAIN].get(CONF_PASSWORD)
    GLOB_MOWER_SERIAL = config[DOMAIN].get(CONF_ID)
    GLOB_MOWER_POLLING = config[DOMAIN].get(CONF_POLLING)
    _LOGGER.debug("Call Mower")
    Mower()

    # Should this be here or in Mower() ???
    for component in INDEGO_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    # Update every minute
    _LOGGER.info("Setup 1m update")
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_1m, second=0)

    # Update every 5 minutes
    _LOGGER.info("Setup 5m update")
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_5m, minute=range(0, 60, 5), second=0)

    # Update every 10 minutes
    _LOGGER.info("Setup 10m update")
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_10m, minute=range(0, 60, 10), second=0)

    # Update every hour
    _LOGGER.info("Setup 60m update")
    now = datetime.datetime.now()
    track_utc_time_change(hass, Mower.refresh_60m, minute=1, second=0)

    # Update battery at user interval
    if GLOB_MOWER_POLLING == True:
        _LOGGER.info("Setup battery polling 60m")
        now = datetime.datetime.now()
        track_utc_time_change(hass, Mower.refresh_battery, minute=[0], second=0)
    else:
        _LOGGER.info("No battery polling")
    

    DEFAULT_NAME = None
    SERVICE_NAME = 'command'
    def send_command(call):
        """Handle the service call."""
        name = call.data.get(CONF_SEND_COMMAND, DEFAULT_NAME)
        _LOGGER.info("Indego.send_command service called")
        _LOGGER.debug("Command: %s", name)
        IndegoAPI_Instance.putCommand(name)
    hass.services.register(DOMAIN, SERVICE_NAME, send_command, schema=SERVICE_SCHEMA_COMMAND)
    
    DEFAULT_NAME = None
    SERVICE_NAME = 'smartmowing'
    def send_smartmowing(call):
        """Handle the service call."""
        name = call.data.get(CONF_SMARTMOWING, DEFAULT_NAME)
        _LOGGER.info("Indego.send_smartmowing service called")
        _LOGGER.debug("Command: %s", str(name))
        IndegoAPI_Instance.putMowMode(name)
        #Update SmartMowing sensor
        IndegoAPI_Instance.getGenericData()
        IndegoAPI_Instance.MowingModeDescription()  
    hass.services.register(DOMAIN, SERVICE_NAME, send_smartmowing, schema=SERVICE_SCHEMA_SMARTMOWING)

        

    _LOGGER.info("Setup Bosch Indego Mower Integration END")    
    return True    

class Mower():
    def __init__(self):
        _LOGGER.info("Mower init start __init__")
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
        _LOGGER.debug(f"GLOB_MOWER_POLLING = {GLOB_MOWER_POLLING}")

        ### Creating API Instance and Login
        IndegoAPI_Instance = IndegoAPI(GLOB_MOWER_USERNAME, GLOB_MOWER_PASSWORD, GLOB_MOWER_SERIAL)

        ### show vars
        #IndegoAPI_Instance.show_vars()
        
        ### Initial update of variables
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
        IndegoAPI_Instance.BareToolNumber()  
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
        #Get last and next mow
        IndegoAPI_Instance.getLastCompletedMow()
        IndegoAPI_Instance.getNextMow()
        #Get updates available
        IndegoAPI_Instance.getUpdates()
        ### show vars
        #IndegoAPI_Instance.show_vars()
        _LOGGER.info("Mower init end __init__")

    def refresh_1m(self):
        _LOGGER.info("  Refresh Indego sensors every 1m")
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
            _LOGGER.debug("  StateValue between (500 and 799) or (257) or (260): time to call getOperatingData!!!")
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
        else:
            _LOGGER.debug("  Mower docked. Do not call getOperatingData!!!")
        return True

    def refresh_5m(self):
        _LOGGER.info("  Refresh Indego sensors every 5m")

        #Get data for MowingMode, modeldata
        IndegoAPI_Instance.getGenericData()
        IndegoAPI_Instance.MowingModeDescription()

        #Get data for alerts
        IndegoAPI_Instance.getAlerts()
        IndegoAPI_Instance.AlertsCount()
        IndegoAPI_Instance.AlertsDescription()

        #Get last and next mow
        IndegoAPI_Instance.getLastCompletedMow()
        IndegoAPI_Instance.getNextMow()

        _LOGGER.debug("  Refresh end")
        return True

    def refresh_10m(self):
        _LOGGER.info("  Refresh Indego online sensor every 10m")

        OnlineValue = IndegoAPI_Instance._online
        if (OnlineValue == False):
            _LOGGER.debug("  Mower offline, control status!")
            IndegoAPI_Instance.getOperatingData()
            OnlineValue = IndegoAPI_Instance._online
            if (OnlineValue == True):
                #IndegoAPI_Instance.getOperatingData()
                _LOGGER.debug("  Mower came online!")
                #Update all OperatingData variables
                IndegoAPI_Instance.Battery()
                IndegoAPI_Instance.BatteryPercent()
                IndegoAPI_Instance.BatteryPercentAdjusted()
                IndegoAPI_Instance.BatteryVoltage()
                IndegoAPI_Instance.BatteryCycles()
                IndegoAPI_Instance.BatteryDischarge()
                IndegoAPI_Instance.BatteryAmbientTemp()
                IndegoAPI_Instance.BatteryTemp()
                # Update the update sensor
                IndegoAPI_Instance.getUpdates()

            else: 
                _LOGGER.debug("  Mower still offline!")
        else:
            _LOGGER.debug("  Mower online, no control!")
        _LOGGER.debug("  Refresh end")
        return True

    def refresh_60m(self):
        _LOGGER.info("Refresh Indego sensors every 60m")
        #Get data for MowingMode, modeldata
        IndegoAPI_Instance.getGenericData()
        IndegoAPI_Instance.MowingModeDescription()
        IndegoAPI_Instance.ModelDescription() 
        IndegoAPI_Instance.ModelVoltage() 
        IndegoAPI_Instance.ModelVoltageMin()
        IndegoAPI_Instance.ModelVoltageMax()  
        _LOGGER.debug("  Refresh end")
        return True

    def refresh_battery(self):
        _LOGGER.info("Refresh Indego battery sensor")
        #Get data for battery
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
        return True