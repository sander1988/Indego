import datetime
import homeassistant.helpers.config_validation as cv
import json
import logging
import requests
import voluptuous as vol
from aiohttp.hdrs import CONTENT_TYPE
from datetime import timedelta
from homeassistant.const import (CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_ID, CONF_REGION, CONTENT_TYPE_JSON)
from homeassistant.helpers import discovery
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.util import Throttle
from requests.auth import HTTPBasicAuth
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.components.switch import (PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)

CONF_HOST = 'api.indego.iot.bosch-si.com'
CONF_PORT = '443'
DEFAULT_NAME = 'Bosch Indego Mower'

_LOGGER.info("Indego init sensor ++++++++++++++++")

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional('name', default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_USERNAME):  cv.string,
    vol.Required(CONF_PASSWORD):  cv.string,
    vol.Required(CONF_ID):  cv.string
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.info("Set up the Indego Platform!")
    
    add_entities([IndegoState('state', config)])
    add_entities([IndegoMowed('state', config)])
    add_entities([IndegoAlerts('state', config)])
    add_entities([IndegoNextPredictiveSession('state', config)])
    add_entities([IndegoMowingMode('state', config)])

class IndegoState(Entity):
    """Representation of the State Sensor."""

    def __init__(self, sensor, config):
        """Initialize the State sensor."""
        self._state = None
        self.mower_name = config.get('name')
        self.mower_username = config.get(CONF_USERNAME)
        self.mower_password = config.get(CONF_PASSWORD)
        self.mower_id = config.get(CONF_ID)

    @property
    def id(self):
        """Return the id of the Automower."""
        return self._id
    
    @property
    def name(self):
        """Return the name of the sensor."""
        tmp_name = self.mower_name + '_mower_state'
        return tmp_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.info("Update Indego state!")

        host = CONF_HOST
        _LOGGER.debug(f"Host = {host}")
        port = CONF_PORT
        _LOGGER.debug(f"Port = {port}")
        name = self.mower_name
        _LOGGER.debug(f"Mower name = {name}")
        username = self.mower_username
        _LOGGER.debug(f"Mower username = {username}")
        password = self.mower_password
        _LOGGER.debug(f"Mower password = {password}")
        serial = self.mower_id
        _LOGGER.debug(f"Mower ID = {serial}")
        url = "https://{}:{}/api/v1/".format(host, port)
        _LOGGER.debug(f"Indego API Host = {url}")

        _LOGGER.debug("Instanciate Idego API")
        indegoAPI_Instance = IndegoAPI(api_url=url, username=username, password=password, serial=serial)
        _LOGGER.debug("setup-Update Idego API")
        test = indegoAPI_Instance.getState()
        self._state = test

class IndegoMowed(Entity):
    """Representation of the lawn mowed percentage"""

    def __init__(self, sensor, config):
        """Initialize the sensor."""
        self._state = None
        self.mower_name = config.get('name')
        self.mower_username = config.get(CONF_USERNAME)
        self.mower_password = config.get(CONF_PASSWORD)
        self.mower_id = config.get(CONF_ID)
    @property
    def name(self):
        """Return the name of the sensor."""
        tmp_name = str(self.mower_name) + '_lawn_mowed' 
        return tmp_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return '%'
    
    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.info("Update Indego Mowed Percentage!")

        host = CONF_HOST
        _LOGGER.debug(f"Host = {host}")
        port = CONF_PORT
        _LOGGER.debug(f"Port = {port}")
        name = self.mower_name
        _LOGGER.debug(f"Mower name = {name}")
        username = self.mower_username
        _LOGGER.debug(f"Mower username = {username}")
        password = self.mower_password
        _LOGGER.debug(f"Mower password = {password}")
        serial = self.mower_id
        _LOGGER.debug(f"Mower ID = {serial}")
        url = "https://{}:{}/api/v1/".format(host, port)
        _LOGGER.debug(f"Indego API Host = {url}")

        _LOGGER.debug("Instanciate Idego API")
        indegoAPI_Instance = IndegoAPI(api_url=url, username=username, password=password, serial=serial)
        _LOGGER.debug("setup-Update Idego API")
        test = indegoAPI_Instance.getMowed()
        self._state = test

class IndegoAlerts(Entity):
    """Representation of the alerts"""

    def __init__(self, sensor, config):
        """Initialize the sensor."""
        self._state = None
        self.mower_name = config.get('name')
        self.mower_username = config.get(CONF_USERNAME)
        self.mower_password = config.get(CONF_PASSWORD)
        self.mower_id = config.get(CONF_ID)
    
    @property
    def name(self):
        """Return the name of the sensor."""
        tmp_name = str(self.mower_name) + '_alerts' 
        return tmp_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    #@property
    #def unit_of_measurement(self):
    #    """Return the unit of measurement."""
    #    return '%'
    
    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.info("Update Indego Alerts!")

        host = CONF_HOST
        _LOGGER.debug(f"Host = {host}")
        port = CONF_PORT
        _LOGGER.debug(f"Port = {port}")
        name = self.mower_name
        _LOGGER.debug(f"Mower name = {name}")
        username = self.mower_username
        _LOGGER.debug(f"Mower username = {username}")
        password = self.mower_password
        _LOGGER.debug(f"Mower password = {password}")
        serial = self.mower_id
        _LOGGER.debug(f"Mower ID = {serial}")
        url = "https://{}:{}/api/v1/".format(host, port)
        _LOGGER.debug(f"Indego API Host = {url}")

        _LOGGER.debug("Instanciate Idego API")
        indegoAPI_Instance = IndegoAPI(api_url=url, username=username, password=password, serial=serial)
        _LOGGER.debug("setup-Update Idego API")
        test_data = indegoAPI_Instance.getAlerts()
        _LOGGER.debug(f"Alert data: {test_data}")
        test = len(test_data)
        _LOGGER.debug(f"Alerts: {test}")
        self._state = test

class IndegoNextPredictiveSession(Entity):
    """Representation of the next predicitve session"""

    def __init__(self, sensor, config):
        """Initialize the sensor."""
        self._state = None
        self.mower_name = config.get('name')
        self.mower_username = config.get(CONF_USERNAME)
        self.mower_password = config.get(CONF_PASSWORD)
        self.mower_id = config.get(CONF_ID)
    @property
    def name(self):
        """Return the name of the sensor."""
        tmp_name = str(self.mower_name) + '_next_predictive_session' 
        return tmp_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.info("Update Indego Next Session!")

        host = CONF_HOST
        _LOGGER.debug(f"Host = {host}")
        port = CONF_PORT
        _LOGGER.debug(f"Port = {port}")
        name = self.mower_name
        _LOGGER.debug(f"Mower name = {name}")
        username = self.mower_username
        _LOGGER.debug(f"Mower username = {username}")
        password = self.mower_password
        _LOGGER.debug(f"Mower password = {password}")
        serial = self.mower_id
        _LOGGER.debug(f"Mower ID = {serial}")
        url = "https://{}:{}/api/v1/".format(host, port)
        _LOGGER.debug(f"Indego API Host = {url}")

        _LOGGER.debug("Instanciate Idego API")
        indegoAPI_Instance = IndegoAPI(api_url=url, username=username, password=password, serial=serial)
        _LOGGER.debug("setup-Update Idego API")
        test = indegoAPI_Instance.getNextPredicitiveCutting()
        _LOGGER.debug(f"Next session: {test}")
        #test = len(test_data)
        #_LOGGER.debug(f"Alerts: {test}")
        self._state = test

class IndegoMowingMode(Entity):
    """Representation of the mowing mode"""

    def __init__(self, sensor, config):
        """Initialize the sensor."""
        self._state = None
        self.mower_name = config.get('name')
        self.mower_username = config.get(CONF_USERNAME)
        self.mower_password = config.get(CONF_PASSWORD)
        self.mower_id = config.get(CONF_ID)
    @property
    def name(self):
        """Return the name of the sensor."""
        tmp_name = str(self.mower_name) + '_mowing_mode' 
        return tmp_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        _LOGGER.info("Update Indego Mowing Mode!")

        host = CONF_HOST
        _LOGGER.debug(f"Host = {host}")
        port = CONF_PORT
        _LOGGER.debug(f"Port = {port}")
        name = self.mower_name
        _LOGGER.debug(f"Mower name = {name}")
        username = self.mower_username
        _LOGGER.debug(f"Mower username = {username}")
        password = self.mower_password
        _LOGGER.debug(f"Mower password = {password}")
        serial = self.mower_id
        _LOGGER.debug(f"Mower ID = {serial}")
        url = "https://{}:{}/api/v1/".format(host, port)
        _LOGGER.debug(f"Indego API Host = {url}")

        _LOGGER.debug("Instanciate Idego API")
        indegoAPI_Instance = IndegoAPI(api_url=url, username=username, password=password, serial=serial)
        _LOGGER.debug("setup-Update Idego API")
        test = indegoAPI_Instance.getMowingMode()
        _LOGGER.debug(f"Mower Mode: {test}")
        #test = len(test_data)
        #_LOGGER.debug(f"Alerts: {test}")
        self._state = test


class IndegoAPI():
    """Simple wrapper for Indego's API."""

    def __init__(self, api_url=None, username=None, password=None, serial=None):
        """Initialize Indego API and set headers needed later."""
        _LOGGER.debug("IndegoAPI")
        self.api_url = api_url
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

        #self.update()

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
            self._state = 'Waking up mover'
        else:
            self._state = value
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
        #value = str(Runtime_temp)
        value = Runtime_temp
        return value

    def getNextPredicitiveCutting(self):
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
        _LOGGER.debug("getUserAdjustment")
        complete_url = 'alms/' + self.serial + '/predictive/useradjustment'
        Runtime_temp = self.get(complete_url)
        value = Runtime_temp
        return value

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
        value = Runtime_temp
        return value

    def putCommand(self, command):
        _LOGGER.debug("postCommand: " + command)
        if command == "mow" or command == "pause" or command == "returnToDock":
            complete_url = "alms/" + self.serial + "/state"
            #accepted commands = mow, pause, returnToDock
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

