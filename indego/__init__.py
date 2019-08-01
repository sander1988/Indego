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

######
# Working in 0.94, not working in 0.95
# from pyIndego import *
######

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'indego'
DATA_KEY = DOMAIN
CONF_SEND_COMMAND = 'command'
DEFAULT_NAME = 'Indego'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)
INDEGO_COMPONENTS = ['sensor', 'binary_sensor']
UPDATE_INTERVAL = 5  # in minutes
DEFAULT_URL = 'https://api.indego.iot.bosch-si.com:443/api/v1/'
IndegoAPI_Instance = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_ID): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)

SERVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_SEND_COMMAND): cv.string,
})

_LOGGER.info("Idego init-py ++++++++++++++++")

def setup(hass, config: dict):
    """Set up the Indego components."""
    global IndegoAPI_Instance, CONF_MOWER_NAME
    
    _LOGGER.debug(f"API URL = {DEFAULT_URL}")    
    CONF_MOWER_NAME = config[DOMAIN].get(CONF_NAME)
    _LOGGER.debug(f"Name = {CONF_MOWER_NAME}")
    mower_username = config[DOMAIN].get(CONF_USERNAME)
    _LOGGER.debug(f"Username = {mower_username}")
    mower_password = config[DOMAIN].get(CONF_PASSWORD)
    _LOGGER.debug(f"Password = {mower_password}")
    mower_serial = config[DOMAIN].get(CONF_ID)
    _LOGGER.debug(f"ID = {mower_serial}")

    try:
        _LOGGER.debug("Idego pyIndego API")
        IndegoAPI_Instance = IndegoAPI(username=mower_username, password=mower_password, serial=mower_serial)
        
    except (requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError) as conn_err:
        _LOGGER.error("Error setting up Bosch Indego API: %s", conn_err)
        return False
    
    for component in INDEGO_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)
    
    DEFAULT_NAME = None
    SERVICE_NAME = 'mower_command'
    def send_command(call):
        """Handle the service call."""
        name = call.data.get(CONF_SEND_COMMAND, DEFAULT_NAME)
        _LOGGER.debug("Indego.send_command service called")
        _LOGGER.debug("Command: %s", name)
        IndegoAPI_Instance.putCommand(name)
    hass.services.register(DOMAIN, SERVICE_NAME, send_command, schema=SERVICE_SCHEMA)
    return True

class IndegoAPI():
    """Wrapper for Indego's API."""

    def __init__(self, username=None, password=None, serial=None):
        """Initialize Indego API and set headers needed later."""
        _LOGGER.debug("__init__")
        self.api_url = DEFAULT_URL
        self.serial = serial
        self.status = None
        self.username = username
        self.password = password
        self.headers = {CONTENT_TYPE: CONTENT_TYPE_JSON}
        self.body = {'device': '', 'os_type': 'Android', 'os_version': '4.0', 'dvc_manuf': 'unknown', 'dvc_type': 'unknown'}
        self.jsonBody = json.dumps(self.body)

        _LOGGER.debug("API: %s", '{}{}'.format(self.api_url, 'authenticate'))
        self.login = requests.post(
            '{}{}'.format(self.api_url, 'authenticate'), data=self.jsonBody, headers=self.headers,
            auth=HTTPBasicAuth(username, password), timeout=30, verify=False)
        _LOGGER.debug("Response: " + str(self.login.content))
        _LOGGER.debug("JSON Response: " + str(self.login.json()))
        
        logindata = json.loads(self.login.content)
        self.contextid = logindata['contextId']
        _LOGGER.debug("self.contextid: " + self.contextid)
        _LOGGER.debug("self.serial: " + self.serial)

    def get(self, method):
        """Send a GET request and return the response as a dict."""
        _LOGGER.debug("GET start")
        try:
            logindata = json.loads(self.login.content)
            contextId = logindata['contextId']
            _LOGGER.debug("ContextID: " + contextId)
            headers = {CONTENT_TYPE: CONTENT_TYPE_JSON, 'x-im-context-id': contextId}
            url = self.api_url + method
            _LOGGER.debug("URL GET: " + url)
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            _LOGGER.debug("HTTP Status code: " + str(response.status_code))
            if response.status_code != 200:
                _LOGGER.debug("need to call login again")
                self.authenticate()
                return
            else:
                _LOGGER.debug("Json:" + str(response.json()))
                response.raise_for_status()
                _LOGGER.debug("GET end")
                return response.json()
        except requests.exceptions.ConnectionError as conn_exc:
            _LOGGER.debug("Failed to update Indego status. Error: " + conn_exc)
            raise

    def put(self, url, method):
        """Send a PUT request and return the response as a dict."""
        _LOGGER.debug("PUT start")
        try:
            logindata = json.loads(self.login.content)
            contextId = logindata['contextId']
            headers = {CONTENT_TYPE: CONTENT_TYPE_JSON, 'x-im-context-id': contextId}
            url = self.api_url + url
            data = '{"state":"' + method + '"}'
            _LOGGER.debug("URL HERE: " + url)
            _LOGGER.debug("headers: " + str(headers))
            _LOGGER.debug("data: " + str(data))
            response = requests.put(url, headers=headers, data=data, timeout=30, verify=False)
            _LOGGER.debug("HTTP Status code: " + str(response.status_code))
            if response.status_code != 200:
                _LOGGER.debug("need to call login again")
                self.authenticate()
                return
            else:
                _LOGGER.debug("Status code: " + str(response))
                #response.raise_for_status()
                _LOGGER.debug("GET end")
                #return response.json()
                return response.status_code                   #Not returning codes!!!


        except requests.exceptions.ConnectionError as conn_exc:
            _LOGGER.debug("Failed to update Indego status. Error: " + conn_exc)
            raise

    def authenticate(self):
        _LOGGER.debug("Authenticate start")
        try:
            _LOGGER.debug("authenticate called")
            _LOGGER.debug("API: " + self.api_url +  'authenticate')
            self.login = requests.post(
                '{}{}'.format(self.api_url, 'authenticate'), data=self.jsonBody, headers=self.headers,
                auth=HTTPBasicAuth(self.username, self.password), timeout=30, verify=False)
            _LOGGER.debug("Response: " + str(self.login.content))
            _LOGGER.debug("JSON Response: " + str(self.login.json()))
            self.update()

        except requests.exceptions.ConnectionError as conn_exc:
            _LOGGER.debug("Failed to update Indego status. Error: " + conn_exc)
            raise
        _LOGGER.debug("Authenticate end")

    def update(self):
        """Update cached response."""
        _LOGGER.debug("Update start")
        complete_url = 'alms/' + self.serial + '/state'
        try:
            self.status = self.get(complete_url)
        except requests.exceptions.ConnectionError:
            _LOGGER.debug("Failed to update status - exception already logged in self.post")
            raise
        _LOGGER.debug("state: " + str(self.status))
        _LOGGER.debug("Update end")
        return(self.status)

    def getState(self):
        """ Get Position History """
        _LOGGER.debug("getState")
        complete_url = 'alms/' + self.serial + '/state'
        _LOGGER.debug("Complete URL: " + complete_url)
        temp = self.get(complete_url)
        value = temp['state']

        if value == 0:
            self._state = 'Reading status'
        elif value == 257:
            self._state = 'Charging'
        elif value == 258:
            self._state = 'Docked'
        elif value == 259:
            self._state = 'Docked - Software update'
        elif value == 260:
            self._state = 'Docked'
        elif value == 261:
            self._state = 'Docked'
        elif value == 262:
            self._state = 'Docked - Loading map'
        elif value == 263:
            self._state = 'Docked - Saving map'
        elif value == 513:
            self._state = 'Mowing'
        elif value == 514:
            self._state = 'Relocalising'
        elif value == 515:
            self._state = 'Loading map'
        elif value == 516:
            self._state = 'Learning lawn'
        elif value == 517:
            self._state = 'Paused'
        elif value == 518:
            self._state = 'Border cut'
        elif value == 519:
            self._state = 'Idle in lawn'
        elif value == 769:
            self._state = 'Returning to Dock'
        elif value == 770:
            self._state = 'Returning to Dock'
        elif value == 771:
            self._state = 'Returning to Dock - Battery low'
        elif value == 772:
            self._state = 'Returning to dock - Calendar timeslot ended'
        elif value == 773:
            self._state = 'Returning to dock - Battery temp range'
        elif value == 774:
            self._state = 'Returning to dock - requested by user/app'
        elif value == 775:
            self._state = 'Returning to dock - Lawn complete'
        elif value == 776:
            self._state = 'Returning to dock - Relocalising'
        elif value == 1025:
            self._state = 'Diagnostic mode'
        elif value == 1026:
            self._state = 'End of live'
        elif value == 1281:
            self._state = 'Software update'
        elif value == 1537:
            self._state = 'Stuck on lawn, help needed'
        elif value == 64513:
            self._state = 'Sleeping'
        else:
            self._state = value
            _LOGGER.debug(f"Value = {value}")
        return self._state

    def getMowed(self):
        _LOGGER.debug("getMoved")
        complete_url = 'alms/' + self.serial + '/state'
        temp = self.get(complete_url)
        value = temp['mowed']
        return value

    def getPosition(self):
        _LOGGER.debug("getPosition")
        complete_url = 'alms/' + self.serial + '/state'
        Position_temp = self.get(complete_url)
        value = Position_temp['xPos'], Position_temp['yPos']
        return value

    def getRuntimeTotal(self):
        _LOGGER.debug("getRuntimeTotal")
        complete_url = 'alms/' + self.serial + '/state'
        Runtime_temp = self.get(complete_url)
        value_temp = Runtime_temp['runtime']
        value = value_temp['total']
        return value

    def getRuntimeSession(self):
        _LOGGER.debug("getRuntimeSession")
        complete_url = 'alms/' + self.serial + '/state'
        Runtime_temp = self.get(complete_url)
        value_temp = Runtime_temp['runtime']
        value = value_temp['session']
        return value

    def getAlerts(self):
        _LOGGER.debug("getAlerts")
        complete_url = 'alerts'
        Runtime_temp = self.get(complete_url)
        _LOGGER.debug("Runtime_temp: " + str(Runtime_temp))
        tmp_count = len(Runtime_temp)
        _LOGGER.debug(f"Alerts: {tmp_count}")    
        return tmp_count
    
    def getAlertsDescription(self):
        _LOGGER.debug("getAlerts")
        complete_url = 'alerts'
        Runtime_temp = self.get(complete_url)
        _LOGGER.debug("Runtime_temp: " + str(Runtime_temp))
        value = str(Runtime_temp)
        return value

    def getNextPredicitiveCutting(self):
        # Not working
        _LOGGER.debug("getNetPRedicitveCutting")
        complete_url = 'alms/' + self.serial + '/predictive/nextcutting?last=YYYY-MM-DDTHH:MM:SS%2BHH:MM'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

    def getName(self):
        _LOGGER.debug("getName")
        complete_url = 'alms/' + self.serial
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['alm_name']
        return value

    def getServiceCounter(self):
        _LOGGER.debug("getServiceCounter")
        complete_url = 'alms/' + self.serial
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['service_counter']
        return value

    def getNeedsService(self):
        _LOGGER.debug("getNeedsService")
        complete_url = 'alms/' + self.serial
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['needs_service']
        return value

    def getMowingMode(self):
        _LOGGER.debug("getMowingMode")
        complete_url = 'alms/' + self.serial
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['alm_mode']
        return value

    def getModel(self):
        _LOGGER.debug("getModel")
        complete_url = 'alms/' + self.serial
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['bareToolnumber']

        if value == '3600HA2300':
            self._state = 'Indego 1000 Connect'
        elif value == '3600HA2301':
            self._state = 'Indego 1200 Connect'
        elif value == '3600HA2302':
            self._state = 'Indego 1100 Connect'
        elif value == '3600HA2303':
            self._state = 'Indego 13C'
        elif value == '3600HA2304':
            self._state = 'Indego 10C'
        else:
            self._state = 'Undefined ' + value
        return self._state

    def getSerial(self):
        _LOGGER.debug("getSerial")
        return self.serial

    def getFirmware(self):
        _LOGGER.debug("getFirmware")
        complete_url = 'alms/' + self.serial
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['alm_firmware_version']
        return value

    def getLocation(self):
        _LOGGER.debug("getLocation")
        complete_url = 'alms/' + self.serial + '/predictive/location'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

    def getPredicitiveCalendar(self):
        _LOGGER.debug("getPredicitveCalendar")
        complete_url = 'alms/' + self.serial + '/predictive/calendar'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

    def getUserAdjustment(self):
        # No idea what this does?
        _LOGGER.debug("getUserAdjustment")
        complete_url = 'alms/' + self.serial + '/predictive/useradjustment'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value['user_adjustment']

    def getCalendar(self):
        _LOGGER.debug("getCalendar")
        complete_url = 'alms/' + self.serial + '/calendar'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

    def getSecurity(self):
        _LOGGER.debug("getSecurity")
        complete_url = 'alms/' + self.serial + '/security'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

    def getAutomaticUpdate(self):
        _LOGGER.debug("getAutomaticUpdate")
        complete_url = 'alms/' + self.serial + '/automaticUpdate'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

    def getUpdateAvailable(self):
        #
        # Need to better this class with better error handling for timeout
        # Takes time as the mower has to wake up for this control to be perfomed
        #
        _LOGGER.debug("getUpdateAvailable")
        complete_url = 'alms/' + self.serial + '/updates'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp['available']
        #if value == 'True':
        #    value_binary = 0
        #else:
        #    value_binary = 1
        #return value_binary
        return value

    def putCommand(self, command):
        _LOGGER.debug("postCommand: " + command)
        if command == "mow" or command == "pause" or command == "returnToDock":
            complete_url = "alms/" + self.serial + "/state"
            temp = self.put(complete_url, command)
            
            return temp
        else:
            _LOGGER.debug("postCommand " + command + " not valid!")
            return "Wrong Command!"

    def getMap(self):
        print("getMap (Not implemented yet")
        #complete_url = 'alms/' + self.serial + '/map'
        #Runtime_temp = self.get(complete_url)
        #value = Runtime_temp
        value = "error"
        return value