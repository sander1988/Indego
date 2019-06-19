"""
Support for monitoring Bosch Indego lawn mower.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.indego/
"""
DOMAIN = 'indego'
from datetime import timedelta
import logging

from aiohttp.hdrs import CONTENT_TYPE
import requests
from requests.auth import HTTPBasicAuth
import json
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PORT, CONF_PASSWORD, CONF_USERNAME,
    CONF_ID, CONTENT_TYPE_JSON, CONF_MONITORED_VARIABLES)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOST = 'api.indego.iot.bosch-si.com'
DEFAULT_NAME = 'Indego'
DEFAULT_PORT = 443

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)

SENSOR_TYPES = {
    'state': ['state', 'State', ''],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    vol.Optional(CONF_MONITORED_VARIABLES, default=['state']):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_ID): cv.string,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Indego sensors."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    serial = config.get(CONF_ID)
    monitored_types = config.get(CONF_MONITORED_VARIABLES)
    url = "https://{}:{}/api/v1/".format(host, port)

    try:
        indegoapi = IndegoAPI(
            api_url=url, username=username, password=password, serial=serial)
        indegoapi.update()
    except (requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError) as conn_err:
        _LOGGER.error("Error setting up Bosch Indego API: %s", conn_err)
        return False

    devices = []
    for ng_type in monitored_types:
        new_sensor = IndegoSensor(
            api=indegoapi, sensor_type=SENSOR_TYPES.get(ng_type),
            client_name=name)
        devices.append(new_sensor)

    add_devices(devices, True)


class IndegoSensor(Entity):
    """Representation of an Indego sensor."""

    def __init__(self, api, sensor_type, client_name):
        """Initialize a new Indego sensor."""
        self._name = '{} {}'.format(client_name, sensor_type[1])
        self.type = sensor_type[0]
        self.api = api
        self._state = None
        self._unit_of_measurement = sensor_type[2]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    def update(self):
        """Update state of sensor."""
        try:
            self.api.update()
        except requests.exceptions.ConnectionError:
            # Error calling the API, already logged in api.update()
            return

        if self.api.status is None:
            _LOGGER.debug("Update of %s requested, but no status is available",
                          self._name)
            return

        value = self.api.status.get(self.type)
        if value is None:
            _LOGGER.warning("Unable to locate value for %s", self.type)
            return

        if "state" in self.type and value > -1:
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
        else:
            self._state = value


class IndegoAPI(object):
    """Simple wrapper for Indego's API."""

    def __init__(self, api_url, username=None, password=None, serial=None):
        """Initialize Indego API and set headers needed later."""
        self.api_url = api_url
        self.serial = serial
        self.status = None
        self.username = username
        self.password = password
        self.headers = {CONTENT_TYPE: CONTENT_TYPE_JSON}

        self.body = {'device': '', 'os_type': 'Android', 'os_version': '4.0', 'dvc_manuf': 'unknown', 'dvc_type': 'unknown'}
        self.jsonBody = json.dumps(self.body)
        
        _LOGGER.debug("API: %s", '{}{}'.format(api_url, 'authenticate'))
        self.login = requests.post(
            '{}{}'.format(api_url, 'authenticate'), data=self.jsonBody, headers=self.headers, auth=HTTPBasicAuth(username, password), timeout=30)
        _LOGGER.debug("Response: %s", self.login.content)
        _LOGGER.debug("JSON Response: %s", self.login.json())
        self.update()

    def post(self, method, params=None):
        """Send a POST request and return the response as a dict."""

        try:
            logindata = json.loads(self.login.content)
            contextId = logindata['contextId']
            _LOGGER.debug("ContextID: %s ", contextId)

            headers = {CONTENT_TYPE: CONTENT_TYPE_JSON, 'x-im-context-id': contextId}
            response = requests.get(
                '{}{}'.format(self.api_url, 'alms/' + self.serial + '/state'), headers=headers, timeout=30)
            _LOGGER.debug("HTTP Status Code: %s", response.status_code)
            if response.status_code != 200:
                _LOGGER.debug("need to call login again")
                self.authenticate()
                return
            else:
                _LOGGER.debug("JSON Response: %s", response.json())
                response.raise_for_status()            
                return response.json()

        except requests.exceptions.ConnectionError as conn_exc:
            _LOGGER.error("Failed to update Indego status. Error: %s",
                          conn_exc)
            raise

    def authenticate(self):
        
        try:
            _LOGGER.debug("authenticate called")
            _LOGGER.debug("API: %s", '{}{}'.format(self.api_url, 'authenticate'))
            self.login = requests.post(
                '{}{}'.format(self.api_url, 'authenticate'), data=self.jsonBody, headers=self.headers, auth=HTTPBasicAuth(self.username, self.password), timeout=30)
            _LOGGER.debug("Response: %s", self.login.content)
            _LOGGER.debug("JSON Response: %s", self.login.json())
            self.update()

        except requests.exceptions.ConnectionError as conn_exc:
            _LOGGER.error("Failed to update Indego status. Error: %s",
                          conn_exc)
            raise

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update cached response."""
        try:
            self.status = self.post('state')
        except requests.exceptions.ConnectionError:
            # Failed to update status - exception already logged in self.post
            raise