"""Bosch Indego Mower integration."""
import asyncio
import datetime
import json
import logging
from datetime import timedelta
import voluptuous as vol
from pyIndego import IndegoAsyncClient

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    DEVICE_CLASS_PROBLEM,
)
from homeassistant.const import (
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    CONF_DEVICE_CLASS,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TIMESTAMP,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    TEMP_CELSIUS,
    STATE_UNKNOWN,
)
from homeassistant.helpers import discovery
from homeassistant.helpers.event import async_call_later

from .binary_sensor import IndegoBinarySensor
from .const import (
    BINARY_SENSOR_TYPE,
    CONF_POLLING,
    CONF_SEND_COMMAND,
    CONF_SMARTMOWING,
    DATA_KEY,
    DEFAULT_NAME,
    DEFAULT_NAME_COMMANDS,
    DOMAIN,
    ENTITY_ALERT,
    ENTITY_BATTERY,
    ENTITY_LAST_COMPLETED,
    ENTITY_LAWN_MOWED,
    ENTITY_MOWER_ALERT,
    ENTITY_MOWER_STATE,
    ENTITY_MOWER_STATE_DETAIL,
    ENTITY_MOWING_MODE,
    ENTITY_NEXT_MOW,
    ENTITY_ONLINE,
    ENTITY_RUNTIME,
    ENTITY_UPDATE_AVAILABLE,
    INDEGO_COMPONENTS,
    MIN_TIME_BETWEEN_UPDATES,
    SENSOR_TYPE,
    SERVICE_NAME_COMMAND,
    SERVICE_NAME_SMARTMOW,
)
from .sensor import IndegoSensor

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_ID): cv.string,
                vol.Optional(CONF_POLLING, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SCHEMA_COMMAND = vol.Schema({vol.Required(CONF_SEND_COMMAND): cv.string})

SERVICE_SCHEMA_SMARTMOWING = vol.Schema({vol.Required(CONF_SMARTMOWING): cv.string})


def FUNC_ICON_BATTERY(state):
    if state:
        state = int(state)
        if state == 0:
            return "mdi:battery-outline"
        elif state == 100:
            return "mdi:battery"
        return f"mdi:battery-{state - (state%10)}"
    return "mdi:battery-50"


def FUNC_ICON_MOWER_ALERT(state):
    if state:
        if state == STATE_UNKNOWN:
            return "mdi:check-circle-outline"
        if int(state) > 0:
            return "mdi:alert-outline"
    return "mdi:check-circle-outline"


entity_definitions = {
    ENTITY_ONLINE: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_NAME: "online",
        CONF_ICON: "mdi:cloud-check",
        CONF_DEVICE_CLASS: DEVICE_CLASS_CONNECTIVITY,
    },
    ENTITY_UPDATE_AVAILABLE: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_NAME: "update available",
        CONF_ICON: "mdi:chip",
        CONF_DEVICE_CLASS: None,
    },
    ENTITY_ALERT: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_NAME: "alert",
        CONF_ICON: "mdi:alert-octagram-outline",
        CONF_DEVICE_CLASS: DEVICE_CLASS_PROBLEM,
    },
    ENTITY_MOWER_STATE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "mower state",
        CONF_ICON: "mdi:robot",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ENTITY_MOWER_STATE_DETAIL: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "mower state detail",
        CONF_ICON: "mdi:robot",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ENTITY_BATTERY: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "battery %",
        CONF_ICON: FUNC_ICON_BATTERY,
        CONF_DEVICE_CLASS: DEVICE_CLASS_BATTERY,
        CONF_UNIT_OF_MEASUREMENT: "%",
    },
    ENTITY_LAWN_MOWED: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "lawn mowed",
        CONF_ICON: "mdi:percent",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ENTITY_LAST_COMPLETED: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "last completed",
        CONF_ICON: "mdi:cash-100",
        CONF_DEVICE_CLASS: DEVICE_CLASS_TIMESTAMP,
        CONF_UNIT_OF_MEASUREMENT: "ISO8601",
    },
    ENTITY_NEXT_MOW: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "next mow",
        CONF_ICON: "mdi:chevron-right",
        CONF_DEVICE_CLASS: DEVICE_CLASS_TIMESTAMP,
        CONF_UNIT_OF_MEASUREMENT: "ISO8601",
    },
    ENTITY_MOWING_MODE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "mowing mode",
        CONF_ICON: "mdi:alpha-m-circle-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
    ENTITY_RUNTIME: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "runtime total",
        CONF_ICON: "mdi:information-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "h",
    },
    ENTITY_MOWER_ALERT: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_NAME: "mower alert",
        CONF_ICON: FUNC_ICON_MOWER_ALERT,
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
    },
}


async def async_setup(hass, config: dict):
    """Set up the integration."""
    conf = config[DOMAIN]
    mower_serial = conf[CONF_ID]
    component = hass.data[DOMAIN] = IndegoHub(
        conf[CONF_NAME],
        conf[CONF_USERNAME],
        conf[CONF_PASSWORD],
        mower_serial,
        conf[CONF_POLLING],
        hass,
    )

    await component.indego.login()
    await component.async_schedule_updates()
    for comp in INDEGO_COMPONENTS:
        hass.async_create_task(
            discovery.async_load_platform(hass, comp, DOMAIN, {}, config)
        )

    async def async_send_command(call):
        """Handle the service call."""
        name = call.data.get(CONF_SEND_COMMAND, DEFAULT_NAME_COMMANDS)
        _LOGGER.debug("Indego.send_command service called, with command: %s", name)
        await hass.data[DOMAIN].indego.put_command(name)
        await hass.data[DOMAIN]._update_state()

    async def async_send_smartmowing(call):
        """Handle the service call."""
        name = call.data.get(CONF_SMARTMOWING, DEFAULT_NAME_COMMANDS)
        _LOGGER.debug("Indego.send_smartmowing service called, set to %s", name)
        await hass.data[DOMAIN].indego.put_mow_mode(name)
        await hass.data[DOMAIN]._update_generic_data()

    hass.services.async_register(
        DOMAIN, SERVICE_NAME_COMMAND, async_send_command, schema=SERVICE_SCHEMA_COMMAND
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_NAME_SMARTMOW,
        async_send_smartmowing,
        schema=SERVICE_SCHEMA_SMARTMOWING,
    )
    return True


class IndegoHub:
    """Class for the IndegoHub, which controls the sensors and binary sensors."""

    def __init__(self, name, username, password, serial, polling, hass):
        """Initialize the IndegoHub.

        Args:
            name (str): the name of the mower for entities
            username (str): username for indego service
            password (str): password for  indego service
            serial (str): serial of the mower, is used for uniqueness
            polling (bool): whether to keep polling the mower
            hass (HomeAssistant): HomeAssistant instance

        """
        self.mower_name = name
        self.username = username
        self.password = password
        self._serial = serial
        self._polling = polling
        self.hass = hass

        self.indego = IndegoAsyncClient(self.username, self.password, self._serial)
        self.refresh_state_remover = None
        self.refresh_5m_remover = None
        self.refresh_10m_remover = None
        # self.refresh_60m_remover = None
        # self.polling_remover = None

        self.entities = self.create_entities()

    def create_entities(self):
        entities = {}
        for entity_key, entity in entity_definitions.items():
            if entity[CONF_TYPE] == SENSOR_TYPE:
                entities[entity_key] = IndegoSensor(
                    self._serial,
                    f"{self._serial}_{entity_key}",
                    f"{self.mower_name} {entity[CONF_NAME]}",
                    entity[CONF_ICON],
                    entity[CONF_DEVICE_CLASS],
                    entity[CONF_UNIT_OF_MEASUREMENT],
                )
            elif entity[CONF_TYPE] == BINARY_SENSOR_TYPE:
                entities[entity_key] = IndegoBinarySensor(
                    self._serial,
                    f"{self._serial}_{entity_key}",
                    f"{self.mower_name} {entity[CONF_NAME]}",
                    entity[CONF_ICON],
                    entity[CONF_DEVICE_CLASS],
                )
        return entities

    async def async_schedule_updates(self):
        """Schedule future updates."""
        # self.refresh_state_remover = async_call_later(self.hass, 30, self.refresh_state)
        # self.refresh_5m_remover = async_call_later(self.hass, 300, self.refresh_5m)
        # self.refresh_10m_remover = async_call_later(self.hass, 600, self.refresh_10m)
        # self.refresh_60m_remover = async_call_later(self.hass, 3600, self.refresh_60m)
        # if self._polling:
        #     self.polling_remover = async_call_later(
        #         self.hass, 3600, self.refresh_battery
        #     )

        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, self._initial_update
        )
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_shutdown)

    async def _initial_update(self, _):
        """Initial update of values, which will also trigger further updates at the right times."""
        await self.refresh_state(_)
        await self.refresh_5m(_)
        await self.refresh_10m(_)

        # await asyncio.gather(
        #     *[
        #         self._update_generic_data(),
        #         self._update_state(),
        #         self._update_operating_data(),
        #         self._update_last_completed_mow(),
        #         self._update_next_mow(),
        #         self._update_alerts(),
        #         self._update_updates_available(),
        #     ]
        # )

    async def async_shutdown(self, _):
        """Remove all future updates and close the client."""
        if self.refresh_state_remover:
            self.refresh_state_remover()
        if self.refresh_5m_remover:
            self.refresh_5m_remover()
        if self.refresh_10m_remover:
            self.refresh_10m_remover()
        # self.refresh_60m_remover()
        # if self._polling:
        #     self.polling_remover()
        await self.indego.close()

    async def refresh_state(self, _):
        """Refresh Indego sensors every 30 seconds when mowing, 5 minutes otherwise."""
        await self._update_state()
        state = self.indego.state.state
        next_refresh = 300
        if (500 <= state <= 799) or (state in (257, 266)):
            await self._update_operating_data()
            next_refresh = 30

        self.refresh_state_remover = async_call_later(
            self.hass, next_refresh, self.refresh_state
        )

    async def refresh_5m(self, _):
        """Refresh Indego sensors every 5m."""
        await asyncio.gather(
            *[
                self._update_generic_data(),
                self._update_alerts(),
                self._update_last_completed_mow(),
                self._update_next_mow(),
            ]
        )
        self.refresh_5m_remover = async_call_later(self.hass, 300, self.refresh_5m)

    async def refresh_10m(self, _):
        """Refresh Indego sensors every 10m."""
        online = self.indego._online
        if not online:
            await asyncio.gather(
                *[self._update_operating_data(), self._update_updates_available()]
            )
        self.refresh_10m_remover = async_call_later(self.hass, 600, self.refresh_10m)

    # TODO: Look at the logic for these refreshes, this one is called less often then the 5m one and does the same.
    # async def refresh_60m(self, _):
    #     """Refresh Indego sensors every 60m."""
    #     await self._update_generic_data()
    #     self.refresh_60m_remover = async_call_later(self.hass, 3600, self.refresh_60m)

    # TODO: Look at the logic for these refreshes, this one is called less often then the 10m one and does the same.
    # async def refresh_battery(self, _):
    #     """Refresh self.indego battery sensor."""
    #     await self._update_operating_data()
    #     if self._polling:
    #         self.polling_remover = async_call_later(
    #             self.hass, 3600, self.refresh_battery
    #         )

    async def _update_operating_data(self):
        await self.indego.update_operating_data()
        # dependent state updates
        self.entities[ENTITY_ONLINE].state = self.indego._online
        self.entities[
            ENTITY_BATTERY
        ].state = self.indego.operating_data.battery.percent_adjusted

        # dependent attribute updates
        self.entities[ENTITY_BATTERY].add_attribute(
            {
                "Voltage": f"{self.indego.operating_data.battery.voltage} V",
                "Discharge": f"{self.indego.operating_data.battery.discharge} Ah",
                "Cycles": f"{self.indego.operating_data.battery.cycles}",
                "Battery temp": f"{self.indego.operating_data.battery.battery_temp} {TEMP_CELSIUS}",
                "Ambient temp": f"{self.indego.operating_data.battery.ambient_temp} {TEMP_CELSIUS}",
            }
        )

    async def _update_state(self):
        await self.indego.update_state()
        # dependent state updates
        self.entities[ENTITY_MOWER_STATE].state = self.indego.state_description
        self.entities[
            ENTITY_MOWER_STATE_DETAIL
        ].state = self.indego.state_description_detail
        self.entities[ENTITY_LAWN_MOWED].state = self.indego.state.mowed
        self.entities[ENTITY_RUNTIME].state = self.indego.state.runtime.total.operate

        # dependent attribute updates
        self.entities[ENTITY_MOWER_STATE_DETAIL].add_attribute(
            {
                "State #": self.indego.state.state,
                "State description": self.indego.state_description_detail,
            }
        )
        self.entities[ENTITY_LAWN_MOWED].add_attribute(
            {
                "Last session Operation": f"{self.indego.state.runtime.session.operate} min",
                "Last session Cut": f"{self.indego.state.runtime.session.cut} min",
                "Last session Charge": f"{self.indego.state.runtime.session.charge} min",
            }
        )
        self.entities[ENTITY_RUNTIME].add_attribute(
            {
                "Total operation time": f"{self.indego.state.runtime.total.operate} h",
                "Total mowing time": f"{self.indego.state.runtime.total.cut} h",
                "Total charging time": f"{self.indego.state.runtime.total.charge} h",
            }
        )

    async def _update_generic_data(self):
        await self.indego.update_generic_data()
        # dependent state updates
        self.entities[
            ENTITY_MOWING_MODE
        ].state = self.indego.generic_data.mowing_mode_description

        # dependent attribute updates
        self.entities[ENTITY_MOWER_STATE].add_attribute(
            {
                "Model": self.indego.generic_data.model_description,
                "Serial": self.indego.generic_data.alm_sn,
                "Firmware": self.indego.generic_data.alm_firmware_version,
            }
        )
        self.entities[ENTITY_MOWER_STATE_DETAIL].add_attribute(
            {"Model #": self.indego.generic_data.bareToolnumber}
        )

    async def _update_alerts(self):
        await self.indego.update_alerts()
        # dependent state updates
        # TODO: fix in pyIndego: put self.alerts_count in init and then replace len(...) with self.indego.alerts_count
        self.entities[ENTITY_MOWER_ALERT].state = len(self.indego.alerts)
        self.entities[ENTITY_ALERT].state = len(self.indego.alerts) > 0

    async def _update_updates_available(self):
        await self.indego.update_updates_available()
        # dependent state updates
        self.entities[ENTITY_UPDATE_AVAILABLE].state = self.indego.update_available

    async def _update_last_completed_mow(self):
        await self.indego.update_last_completed_mow()
        self.entities[ENTITY_LAST_COMPLETED].state = self.indego.last_completed_mow
        self.entities[ENTITY_LAWN_MOWED].add_attribute(
            {"Last completed Mow": str(self.indego.last_completed_mow)}
        )

    async def _update_next_mow(self):
        await self.indego.update_next_mow()
        self.entities[ENTITY_NEXT_MOW].state = self.indego.next_mow
        self.entities[ENTITY_LAWN_MOWED].add_attribute(
            {"Next Mow": str(self.indego.next_mow)}
        )
