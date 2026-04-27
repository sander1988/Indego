"""Bosch Indego Mower integration."""
from typing import Optional
import asyncio
import logging
import time
import math
import os
import aiofiles
from datetime import datetime, timedelta
from aiohttp.client_exceptions import ClientResponseError

import homeassistant.util.dt
import voluptuous as vol
from homeassistant.core import HomeAssistant, CoreState
from homeassistant.exceptions import HomeAssistantError, ConfigEntryAuthFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    STATE_ON,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later
from homeassistant.util.dt import utcnow
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import async_get_config_entry_implementation
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.issue_registry import IssueSeverity
from pyIndego import IndegoAsyncClient

from .api import IndegoOAuth2Session
from .binary_sensor import IndegoBinarySensor
from .vacuum import IndegoVacuum
from .lawn_mower import IndegoLawnMower
from .const import *
from .sensor import IndegoSensor
from .camera import IndegoCamera
from .error_codes import (
    ERROR_CODE_MAP,
    get_error_description,
    get_error_severity,
    parse_composite_error,
    format_error_message,
    ErrorSeverity,
)
from .button import IndegoAlertButton
from .switch import IndegoSwitch
from . import diagnostics, repairs

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA_COMMAND = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Required(CONF_SEND_COMMAND): cv.string
})

SERVICE_SCHEMA_SMARTMOWING = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Required(CONF_SMARTMOWING): cv.string
})

SERVICE_SCHEMA_DELETE_ALERT = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Required(SERVER_DATA_ALERT_INDEX): cv.positive_int
})

SERVICE_SCHEMA_DELETE_ALERT_ALL = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string
})

SERVICE_SCHEMA_READ_ALERT = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Required(SERVER_DATA_ALERT_INDEX): cv.positive_int
})

SERVICE_SCHEMA_READ_ALERT_ALL = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string
})

SERVICE_SCHEMA_DOWNLOAD_MAP = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string
})


def FUNC_ICON_MOWER_ALERT(state):
    if state:
        if int(state) > 0 or state == STATE_ON:
            return "mdi:alert-outline"
    return "mdi:check-circle-outline"


ENTITY_DEFINITIONS = {
    ENTITY_ONLINE: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: "mdi:cloud-check",
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.CONNECTIVITY,
        CONF_ATTR: [],
        CONF_TRANSLATION_KEY: "online",
    },
    ENTITY_UPDATE_AVAILABLE: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: "mdi:download-outline",
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.UPDATE,
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "update_available",
    },
    ENTITY_ALERT: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: FUNC_ICON_MOWER_ALERT,
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_ATTR: [
            "alerts_count",
            "last_alert_message",
            "last_alert_error_code",
            "last_alert_date",
            "last_alert_read",
            "error_0",
            "error_0_code",
            "error_0_description",
            "error_0_timestamp",
            "error_0_message",
            "error_0_read",
        ],
        CONF_TRANSLATION_KEY: "indego_alert",
    },
    ENTITY_MOWER_STATE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:robot-mower-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: ["last_updated"],
        CONF_TRANSLATION_KEY: "mower_state",
    },
    ENTITY_MOWER_STATE_DETAIL: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:robot-mower-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [
            "last_updated",
            "state_number",
            "state_description",
        ],
        CONF_TRANSLATION_KEY: "mower_state_detail",
    },
    ENTITY_BATTERY: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "battery",
        CONF_DEVICE_CLASS: SensorDeviceClass.BATTERY,
        CONF_UNIT_OF_MEASUREMENT: "%",
        CONF_ATTR: [
            "last_updated",
            "voltage_V",
            "discharge_Ah",
            "cycles",
            f"battery_temp_{UnitOfTemperature.CELSIUS}",
            f"ambient_temp_{UnitOfTemperature.CELSIUS}",
        ],
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_TRANSLATION_KEY: "battery_percentage",
    },
    ENTITY_LAWN_MOWED: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:grass",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "%",
        CONF_ATTR: [
            "last_updated",
            "last_completed_mow",
            "next_mow",
            "last_session_operation_min",
            "last_session_cut_min",
            "last_session_charge_min",
        ],
        CONF_TRANSLATION_KEY: "lawn_mowed",
    },
    ENTITY_LAWN_MOWED_SIZE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:grass",
        CONF_DEVICE_CLASS: SensorDeviceClass.AREA,
        CONF_UNIT_OF_MEASUREMENT: "m²",
        CONF_ATTR: [
            "last_updated",
        ],
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_TRANSLATION_KEY: "lawn_mowed_size",
    },
    ENTITY_LAST_COMPLETED: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:calendar-check",
        CONF_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_TRANSLATION_KEY: "last_completed",
    },
    ENTITY_NEXT_MOW: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:calendar-clock",
        CONF_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_TRANSLATION_KEY: "next_mow",
    },
    ENTITY_MOWING_MODE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:alpha-m-circle-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_TRANSLATION_KEY: "mowing_mode",
    },
    ENTITY_RUNTIME: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:information-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "h",
        CONF_ATTR: [
            "total_mowing_time_h",
            "total_charging_time_h",
            "total_operation_time_h",
        ],
        CONF_STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
        CONF_TRANSLATION_KEY: "runtime_total",
    },
    ENTITY_VACUUM: {
        CONF_TYPE: VACUUM_TYPE,
    },
    ENTITY_LAWN_MOWER: {
        CONF_TYPE: LAWN_MOWER_TYPE,
    },
    ENTITY_GARDEN_SIZE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:ruler-square",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "m²",
        CONF_ATTR: [],
        CONF_TRANSLATION_KEY: "garden_size",
    },
    ENTITY_CAMERA: {
        CONF_TYPE: CAMERA_TYPE,
        CONF_TRANSLATION_KEY: "mowing_map",
    },
    ENTITY_MOWER_SVG_X: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:map-marker",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "px",
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "mower_position_x",
    },
    ENTITY_MOWER_SVG_Y: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:map-marker",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "px",
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "mower_position_y",
    },
    ENTITY_MOWER_STUCK: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: "mdi:alert-circle-outline",
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_ATTR: ["stuck_since", "stuck_x", "stuck_y"],
        CONF_TRANSLATION_KEY: "mower_stuck",
    },
    ENTITY_LAST_ERROR_CODE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:alert",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: ["error_code", "error_time"],
        CONF_TRANSLATION_KEY: "last_error_code",
    },
    ENTITY_FIRMWARE_VERSION: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:chip",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "firmware_version",
    },
    ENTITY_MAINTENANCE_HOURS: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:tools",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "h",
        CONF_ATTR: ["maintenance_status"],
        CONF_TRANSLATION_KEY: "maintenance_hours",
    },
    ENTITY_SESSION_COUNT: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:counter",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_TRANSLATION_KEY: "session_count",
    },
    ENTITY_BATTERY_VOLTAGE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:lightning-bolt",
        CONF_DEVICE_CLASS: SensorDeviceClass.VOLTAGE,
        CONF_UNIT_OF_MEASUREMENT: "V",
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "battery_voltage",
    },
    ENTITY_BATTERY_TEMPERATURE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:thermometer",
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "battery_temperature",
    },
    ENTITY_AMBIENT_TEMPERATURE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:thermometer",
        CONF_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_TRANSLATION_KEY: "ambient_temperature",
    },
    ENTITY_BATTERY_CYCLES: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:battery-sync",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "battery_cycles",
    },
    ENTITY_BATTERY_DISCHARGE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:battery-minus",
        CONF_DEVICE_CLASS: SensorDeviceClass.ENERGY,
        CONF_UNIT_OF_MEASUREMENT: "Wh",
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
        CONF_TRANSLATION_KEY: "battery_discharge",
    },
    ENTITY_BATTERY_CHARGING: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: "mdi:battery-charging",
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.BATTERY_CHARGING,
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "battery_charging",
    },
    ENTITY_SERVICE_STATUS: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: "mdi:cloud-check",
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.CONNECTIVITY,
        CONF_ATTR: ["last_service_error"],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "service_status",
    },
    ENTITY_DELETE_ALL_ALERTS_BUTTON: {
        CONF_TYPE: BUTTON_TYPE,
        CONF_ICON: "mdi:alert-remove",
        CONF_SERVICE: SERVICE_NAME_DELETE_ALERT_ALL,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        CONF_TRANSLATION_KEY: "delete_all_alerts",
    },
    ENTITY_DELETE_LAST_ALERT_BUTTON: {
        CONF_TYPE: BUTTON_TYPE,
        CONF_ICON: "mdi:alert-minus",
        CONF_SERVICE: SERVICE_NAME_DELETE_ALERT,
        CONF_SERVICE_DATA: {
            SERVER_DATA_ALERT_INDEX: 0,
        },
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        CONF_TRANSLATION_KEY: "delete_last_alert",
    },
    ENTITY_READ_ALL_ALERTS_BUTTON: {
        CONF_TYPE: BUTTON_TYPE,
        CONF_ICON: "mdi:message-alert",
        CONF_SERVICE: SERVICE_NAME_READ_ALERT_ALL,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        CONF_TRANSLATION_KEY: "read_all_alerts",
    },
    ENTITY_READ_LAST_ALERT_BUTTON: {
        CONF_TYPE: BUTTON_TYPE,
        CONF_ICON: "mdi:message-alert",
        CONF_SERVICE: SERVICE_NAME_READ_ALERT,
        CONF_SERVICE_DATA: {
            SERVER_DATA_ALERT_INDEX: 0,
        },
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        CONF_TRANSLATION_KEY: "read_last_alert",
    },
    ENTITY_SMARTMOWING_SWITCH: {
        CONF_TYPE: SWITCH_TYPE,
        CONF_ICON: "mdi:auto-mode",
        CONF_TRANSLATION_KEY: "indego_smartmowing",
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
    },
}


def format_indego_date(date: datetime) -> str:
    return date.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def last_updated_now() -> str:
    return homeassistant.util.dt.as_local(utcnow()).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.info("Setting up Indego integration: %s (Serial: %s)",
                 entry.data[CONF_MOWER_NAME], entry.data[CONF_MOWER_SERIAL])

    entry_implementation = await async_get_config_entry_implementation(hass, entry)
    oauth_session = IndegoOAuth2Session(hass, entry, entry_implementation)
    indego_hub = hass.data[DOMAIN][entry.entry_id] = IndegoHub(
        entry.data[CONF_MOWER_NAME],
        oauth_session,
        entry.data[CONF_MOWER_SERIAL],
        {
            CONF_EXPOSE_INDEGO_AS_MOWER: entry.options.get(CONF_EXPOSE_INDEGO_AS_MOWER, False),
            CONF_EXPOSE_INDEGO_AS_VACUUM: entry.options.get(CONF_EXPOSE_INDEGO_AS_VACUUM, False),
            CONF_SHOW_ALL_ALERTS: entry.options.get(CONF_SHOW_ALL_ALERTS, False),
        },
        hass,
        entry.options.get(CONF_USER_AGENT)
    )

    await indego_hub.start_periodic_position_update()

    async def load_platforms():
        _LOGGER.debug("Loading Home Assistant platforms: %s", INDEGO_PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, INDEGO_PLATFORMS)

    try:
        await indego_hub.update_generic_data_and_load_platforms(load_platforms)
        _LOGGER.info("Successfully set up Indego integration for: %s", entry.data[CONF_MOWER_NAME])

    except ClientResponseError as exc:
        if 400 <= exc.status < 500:
            _LOGGER.warning("Authentication failed (HTTP %d) - please check your credentials", exc.status)
            # Create repair issue for auth failure
            ir.async_create_issue(
                hass,
                DOMAIN,
                "auth_failure",
                is_fixable=True,
                severity=IssueSeverity.ERROR,
                translation_key="auth_failure",
                data={"entry_id": entry.entry_id},
            )
            raise ConfigEntryAuthFailed from exc

        _LOGGER.error("API connection failed during setup (HTTP %d): %s", exc.status, str(exc))
        return False

    except AttributeError as exc:
        _LOGGER.error("Configuration error - invalid data structure: %s", str(exc))
        return False

    # Register repairs and initialize diagnostics/system health
    try:
        # Diagnostics are automatically discovered by HA - no manual registration needed
        # Register repairs flow
        from .repairs import async_create_fix_flow

        # HA will automatically call async_create_fix_flow when user clicks "Learn more" on a repair issue
    except Exception as err:
        _LOGGER.warning("Error setting up features: %s", err)

    def find_instance_for_mower_service_call(call):
        mower_serial = call.data.get(CONF_MOWER_SERIAL, None)
        if mower_serial is None:
            # Return the first instance when params is missing for backwards compatibility.
            return hass.data[DOMAIN][hass.data[DOMAIN][CONF_SERVICES_REGISTERED]]

        for config_entry_id in hass.data[DOMAIN]:
            if config_entry_id == CONF_SERVICES_REGISTERED:
                continue

            instance = hass.data[DOMAIN][config_entry_id]
            if instance.serial == mower_serial:
                return instance

        raise HomeAssistantError("No mower instance found for serial '%s'" % mower_serial)

    async def async_send_command(call):
        """Handle the mower command service call."""
        instance = find_instance_for_mower_service_call(call)
        command = call.data.get(CONF_SEND_COMMAND, DEFAULT_NAME_COMMANDS)
        _LOGGER.info("Sending command '%s' to mower: %s", command, instance._serial)

        await instance.async_send_command_to_client(command)

    async def async_send_smartmowing(call):
        """Handle the smartmowing service call."""
        instance = find_instance_for_mower_service_call(call)
        enable = call.data.get(CONF_SMARTMOWING, DEFAULT_NAME_COMMANDS)
        _LOGGER.info("Setting smart mowing mode to: %s (Mower: %s)", enable, instance._serial)

        await instance._indego_client.put_mow_mode(enable)
        await instance._update_generic_data()

    async def async_delete_alert(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        index = call.data.get(SERVER_DATA_ALERT_INDEX, DEFAULT_NAME_COMMANDS)
        _LOGGER.info("Deleting alert #%s from mower: %s", index, instance._serial)

        await instance._update_alerts()
        await instance._indego_client.delete_alert(index)
        await instance._update_alerts()

    async def async_delete_alert_all(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        _LOGGER.info("Deleting all alerts from mower: %s", instance._serial)

        await instance._update_alerts()

        # Loop to delete all alerts (API may return only ~10 at a time)
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        while attempt < max_attempts:
            alerts_before = len(instance._indego_client.alerts)
            _LOGGER.debug(
                "Delete attempt %d/%d - Current alert count: %d",
                attempt + 1,
                max_attempts,
                alerts_before,
            )

            if alerts_before == 0:
                _LOGGER.info("All alerts successfully deleted")
                break

            await instance._indego_client.delete_all_alerts()
            await asyncio.sleep(5)  # Wait 5 seconds between deletions
            await instance._update_alerts()

            alerts_after = len(instance._indego_client.alerts)
            _LOGGER.debug(
                "Delete attempt %d/%d - Alert count after: %d",
                attempt + 1,
                max_attempts,
                alerts_after,
            )

            attempt += 1

            # If no progress, stop trying
            if alerts_after >= alerts_before:
                _LOGGER.warning("No progress in alert deletion after %d attempts", attempt)
                break

        if attempt >= max_attempts and len(instance._indego_client.alerts) > 0:
            _LOGGER.error(
                "Failed to delete all alerts after %d attempts (%d alerts remaining)",
                max_attempts,
                len(instance._indego_client.alerts),
            )

    async def async_read_alert(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        index = call.data.get(SERVER_DATA_ALERT_INDEX, DEFAULT_NAME_COMMANDS)
        _LOGGER.info("Marking alert #%s as read on mower: %s", index, instance._serial)

        await instance._update_alerts()
        await instance._indego_client.put_alert_read(index)
        await instance._update_alerts()

    async def async_read_alert_all(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        _LOGGER.info("Marking all alerts as read on mower: %s", instance._serial)

        await instance._update_alerts()
        await instance._indego_client.put_all_alerts_read()
        await instance._update_alerts()

    async def async_download_map(call):
        """Handle the download_map service call."""
        instance = find_instance_for_mower_service_call(call)
        _LOGGER.info("Downloading lawn map for mower: %s", instance._serial)
        await instance.download_and_store_map()

    # In HASS we can have multiple Indego component instances as long as the mower serial is unique.
    # So the mower services should only need to be registered for the first instance.
    if CONF_SERVICES_REGISTERED not in hass.data[DOMAIN]:
        _LOGGER.debug("Registering Indego services for config entry: %s", entry.entry_id)

        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_COMMAND,
            async_send_command,
            schema=SERVICE_SCHEMA_COMMAND
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_SMARTMOW,
            async_send_smartmowing,
            schema=SERVICE_SCHEMA_SMARTMOWING,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_DELETE_ALERT,
            async_delete_alert,
            schema=SERVICE_SCHEMA_DELETE_ALERT
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_READ_ALERT,
            async_read_alert,
            schema=SERVICE_SCHEMA_READ_ALERT
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_DELETE_ALERT_ALL,
            async_delete_alert_all,
            schema=SERVICE_SCHEMA_DELETE_ALERT_ALL
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_READ_ALERT_ALL,
            async_read_alert_all,
            schema=SERVICE_SCHEMA_READ_ALERT_ALL
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_DOWNLOAD_MAP,
            async_download_map,
            schema=SERVICE_SCHEMA_DOWNLOAD_MAP
        )

        hass.data[DOMAIN][CONF_SERVICES_REGISTERED] = entry.entry_id
        _LOGGER.info("Successfully registered all Indego services")

    else:
        _LOGGER.debug("Indego services already registered - skipping for config entry: %s", entry.entry_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, INDEGO_PLATFORMS)
    if not unload_ok:
        return False

    if CONF_SERVICES_REGISTERED in hass.data[DOMAIN] and hass.data[DOMAIN][CONF_SERVICES_REGISTERED] == entry.entry_id:
        del hass.data[DOMAIN][CONF_SERVICES_REGISTERED]

    await hass.data[DOMAIN][entry.entry_id].async_shutdown()
    del hass.data[DOMAIN][entry.entry_id]

    return True


class IndegoHub:
    """Class for the IndegoHub, which controls the sensors and binary sensors."""

    # State-specific stuck detection timeouts (in seconds)
    # Maps mower state codes to how long to wait before marking as stuck
    STUCK_DETECTION_TIMEOUTS = {
        513: 60,    # IN_LAWN_MOWING - Normal mowing
        516: 120,   # IN_LAWN_MAPPING - Learning lawn (slow, covers entire area)
        518: 70,    # IN_LAWN_BORDER_CUT - Border cut (precise, but faster than mapping)
        520: 120,   # IN_LAWN_MAPPING_PAUSED - Learning paused (still slow)
        521: 70,    # IN_LAWN_BORDER_CUTTING - Border cutting (precise, but faster than mapping)
        523: 120,   # IN_LAWN_SPOT_MOWING - Spot mowing (very precise, small area)
        524: 120,   # IN_LAWN_RANDOM_MOWING - Random mowing
        525: 120,   # IN_LAWN_SPOT_MOWING_COMPLETE - Spot mowing complete
    }

    # Grace period after mowing session starts (in seconds)
    MOWING_SESSION_GRACE_PERIOD = 60

    def __init__(self, name: str, session: IndegoOAuth2Session, serial: str, features: dict, hass: HomeAssistant, user_agent: Optional[str] = None):
        """Initialize the IndegoHub.

        Args:
            name (str): the name of the mower for entities
            session (IndegoOAuth2Session): the Bosch SingleKey ID OAuth session
            serial (str): serial of the mower, is used for uniqueness
            hass (HomeAssistant): HomeAssistant instance

        """
        self._mower_name = name
        self._serial = serial
        self._features = features
        self._hass = hass
        self._unsub_refresh_state = None
        self._refresh_state_task = None
        self._refresh_10m_remover = None
        self._refresh_24h_remover = None
        self._shutdown = False
        self._latest_alert = None
        self.entities = {}
        self._update_fail_count = None
        self._lawn_map = None
        self._unsub_map_timer = None
        self._last_position = (None, None)
        self._last_state = None
        self._last_position_change_time = None
        self._mowing_session_start_time = None  # Track when mowing session starts (for grace period)
        self._last_svg_x = None
        self._last_svg_y = None
        self._map_svg = None
        self._map_trail = []
        self._last_error_code = None
        self._last_error_time = None
        self._session_count = 0
        self._last_session_state = None
        self._last_successful_update = None  # Track last successful API response
        self._last_service_error = None  # Track last Bosch service error (5xx)
        self._consecutive_timeouts = 0  # Track consecutive position update timeouts
        self._last_timeout_warning_time = None  # Prevent timeout spam

        async def async_token_refresh() -> str:
            await session.async_ensure_token_valid()
            return session.token["access_token"]

        self._indego_client = IndegoAsyncClient(
            token=session.token["access_token"],
            token_refresh_method=async_token_refresh,
            serial=self._serial,
            session=async_get_clientsession(hass),
            raise_request_exceptions=True
        )
        self._indego_client.set_default_header(HTTP_HEADER_USER_AGENT, user_agent)

    async def async_send_command_to_client(self, command: str):
        """Send a mower command to the Indego client."""
        _LOGGER.debug("Sending command to mower (%s): '%s'", self._serial, command)
        await self._indego_client.put_command(command)

    def _create_entities(self, device_info):
        """Create sub-entities and add them to Hass."""

        _LOGGER.debug("Creating entities for mower: %s", self._mower_name)

        for entity_key, entity in ENTITY_DEFINITIONS.items():
            if entity[CONF_TYPE] == SENSOR_TYPE:
                self.entities[entity_key] = IndegoSensor(
                    entity_id=f"indego_{self._serial}_{entity_key}",
                    name=None,
                    icon=entity[CONF_ICON],
                    device_class=entity[CONF_DEVICE_CLASS],
                    unit_of_measurement=entity[CONF_UNIT_OF_MEASUREMENT],
                    attributes=entity[CONF_ATTR],
                    device_info=device_info,
                    translation_key=entity[CONF_TRANSLATION_KEY] if CONF_TRANSLATION_KEY in entity else None,
                    enabled_by_default=entity[CONF_ENABLED_BY_DEFAULT] if CONF_ENABLED_BY_DEFAULT in entity else True,
                    entity_category=entity[CONF_ENTITY_CATEGORY] if CONF_ENTITY_CATEGORY in entity else None,
                    state_class=entity[CONF_STATE_CLASS] if CONF_STATE_CLASS in entity else None,
                )

            elif entity[CONF_TYPE] == BINARY_SENSOR_TYPE:
                self.entities[entity_key] = IndegoBinarySensor(
                    entity_id=f"indego_{self._serial}_{entity_key}",
                    name=None,
                    icon=entity[CONF_ICON],
                    device_class=entity[CONF_DEVICE_CLASS],
                    attributes=entity[CONF_ATTR],
                    device_info=device_info,
                    translation_key=entity[CONF_TRANSLATION_KEY] if CONF_TRANSLATION_KEY in entity else None,
                    entity_category=entity[CONF_ENTITY_CATEGORY] if CONF_ENTITY_CATEGORY in entity else None,
                )

            elif entity[CONF_TYPE] == LAWN_MOWER_TYPE:
                if self._features[CONF_EXPOSE_INDEGO_AS_MOWER]:
                    self.entities[entity_key] = IndegoLawnMower(
                        f"indego_{self._serial}",
                        self._mower_name,
                        device_info,
                        self
                    )

            elif entity[CONF_TYPE] == VACUUM_TYPE:
                if self._features[CONF_EXPOSE_INDEGO_AS_VACUUM]:
                    self.entities[entity_key] = IndegoVacuum(
                        f"indego_{self._serial}",
                        self._mower_name,
                        device_info,
                        self
                    )

            elif entity[CONF_TYPE] == CAMERA_TYPE:
                self.entities[entity_key] = IndegoCamera(
                    entity_id=f"indego_{self._serial}",
                    name=None,
                    device_info=device_info,
                    indego_hub=self,
                    translation_key=entity[CONF_TRANSLATION_KEY] if CONF_TRANSLATION_KEY in entity else None,
                    entity_category=entity[CONF_ENTITY_CATEGORY] if CONF_ENTITY_CATEGORY in entity else None,
                )

            elif entity[CONF_TYPE] == BUTTON_TYPE:
                self.entities[entity_key] = IndegoAlertButton(
                    entity_id=f"indego_{self._serial}_{entity_key}",
                    name=None,
                    icon=entity[CONF_ICON],
                    service_name=entity[CONF_SERVICE],
                    service_data=entity[CONF_SERVICE_DATA] if CONF_SERVICE_DATA in entity else None,
                    device_info=device_info,
                    indego_hub=self,
                    translation_key=entity[CONF_TRANSLATION_KEY] if CONF_TRANSLATION_KEY in entity else None,
                    entity_category=entity[CONF_ENTITY_CATEGORY] if CONF_ENTITY_CATEGORY in entity else None,
                )

            elif entity[CONF_TYPE] == SWITCH_TYPE:
                self.entities[entity_key] = IndegoSwitch(
                    entity_id=f"indego_{self._serial}_{entity_key}",
                    name=None,
                    icon=entity[CONF_ICON],
                    device_info=device_info,
                    indego_hub=self,
                    translation_key=entity[CONF_TRANSLATION_KEY] if CONF_TRANSLATION_KEY in entity else None,
                    entity_category=entity[CONF_ENTITY_CATEGORY] if CONF_ENTITY_CATEGORY in entity else None,
                )

    async def update_generic_data_and_load_platforms(self, load_platforms):
        """Update the generic mower data, so we can create the HA platforms for the Indego component."""
        _LOGGER.debug("Fetching generic data for device info from Bosch API")
        generic_data = await self._update_generic_data()

        device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            manufacturer="Bosch",
            name=self._mower_name,
            model=generic_data.bareToolnumber if generic_data else None,
            sw_version=generic_data.alm_firmware_version if generic_data else None,
        )

        self._create_entities(device_info)
        await load_platforms()

        if self._hass.state == CoreState.running:
            # HA has already been started (this probably an integration reload).
            # Perform initial update right away...
            self._hass.async_create_task(self._initial_update())

        else:
            # HA is still starting, delay the initial update...
            self._hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self._initial_update
            )

        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_shutdown)

    async def _initial_update(self, _=None):
        """Do the initial update and create all entities."""
        _LOGGER.info("Starting initial state synchronization for: %s", self._serial)

        # Don't set offline during startup - let the first successful API call set the state
        self.set_service_status(True)  # Service is up by default until we detect an error
        await self._create_refresh_state_task()
        await asyncio.gather(*[self.refresh_10m(), self.refresh_24h()])

        try:
            _LOGGER.debug("Fetching initial operating data (battery, garden size, etc.)")
            await self._update_operating_data()

        except Exception as exc:
            _LOGGER.warning("Error during initial operating data update: %s", str(exc))

    async def async_shutdown(self, _=None):
        """Remove all future updates, cancel tasks and close the client."""
        if self._shutdown:
            return

        _LOGGER.info("Shutting down Indego integration for: %s", self._serial)
        self._shutdown = True

        self._cancel_delayed_refresh_state()

        if self._refresh_state_task:
            self._refresh_state_task.cancel()
            await self._refresh_state_task
            self._refresh_state_task = None

        if self._refresh_10m_remover:
            self._refresh_10m_remover()

        if self._refresh_24h_remover:
            self._refresh_24h_remover()

        if self._unsub_map_timer:
            self._unsub_map_timer()
            self._unsub_map_timer = None

        await self._indego_client.close()

    async def refresh_state(self):
        """Update the state, if necessary update operating data and recall itself."""
        _LOGGER.debug("Refreshing mower state")
        self._cancel_delayed_refresh_state()

        # Check if mower should be marked offline due to timeout
        self._check_offline_timeout()

        update_failed = False
        try:
            await self._update_state(longpoll=(self._update_fail_count is None or self._update_fail_count == 0))
            self._update_fail_count = 0

        except ClientResponseError as exc:
            update_failed = True
            # Check for service errors (5xx) - only log if status actually changed
            if 500 <= exc.status < 600:
                new_error = f"HTTP {exc.status}"
                if self._last_service_error != new_error:
                    _LOGGER.warning("Bosch service error detected (HTTP %d)", exc.status)
                    self._last_service_error = new_error
                self.set_service_status(False)
            else:
                _LOGGER.debug("Failed to update mower state (HTTP %d)", exc.status)
            self.set_online_state(False)

        except Exception as exc:
            update_failed = True
            _LOGGER.debug("Failed to update mower state: %s", str(exc))
            self.set_online_state(False)

        # Check for connection failure repair issue
        if self._consecutive_timeouts >= 5 and not self._hass.data[DOMAIN].get("connection_issue_reported"):
            _LOGGER.warning("Connection failure detected - creating repair issue")
            try:
                ir.async_create_issue(
                    self._hass,
                    DOMAIN,
                    "connection_failure",
                    is_fixable=False,
                    severity=IssueSeverity.ERROR,
                    translation_key="connection_failure",
                    data={"entry_id": self._hass.data[DOMAIN].get(CONF_SERVICES_REGISTERED)},
                )
                self._hass.data[DOMAIN]["connection_issue_reported"] = True
            except Exception as err:
                _LOGGER.warning("Error creating connection issue: %s", err)

        # Clear connection issue if connection restored
        if self._consecutive_timeouts == 0 and self._hass.data[DOMAIN].get("connection_issue_reported"):
            _LOGGER.info("Connection restored - clearing repair issue")
            try:
                issue_registry = ir.async_get(self._hass)
                issue_registry.async_delete(DOMAIN, "connection_failure")
                self._hass.data[DOMAIN]["connection_issue_reported"] = False
            except Exception as err:
                _LOGGER.warning("Error deleting connection issue: %s", err)

        if self._shutdown:
            return

        if update_failed:
            if self._update_fail_count is None:
                self._update_fail_count = 1
            delay = STATUS_UPDATE_FAILURE_DELAY_TIME[self._update_fail_count]
            _LOGGER.debug("Next state update scheduled in %d seconds due to previous failure", delay)
            when = datetime.now() + timedelta(seconds=delay)
            self._update_fail_count = min(self._update_fail_count + 1, len(STATUS_UPDATE_FAILURE_DELAY_TIME) - 1)
            self._unsub_refresh_state = async_track_point_in_time(self._hass, self._create_refresh_state_task, when)
            return

        if self._indego_client.state:
            state = self._indego_client.state.state
            if (500 <= state <= 799) or (state in (257, 260)):
                try:
                    _LOGGER.debug("Mower is actively mowing - fetching detailed operating data")
                    await self._update_operating_data()

                except Exception as exc:
                    _LOGGER.warning("Failed to update operating data: %s", str(exc))

            if self._indego_client.state.error != self._latest_alert:
                self._latest_alert = self._indego_client.state.error
                try:
                    _LOGGER.debug("New alert detected - updating alert list")
                    await self._update_alerts()

                except Exception as exc:
                    _LOGGER.warning("Failed to refresh alerts: %s", str(exc))

        await self._create_refresh_state_task()

    async def _create_refresh_state_task(self, event=None):
        """Create a task to refresh the mower state."""
        self._refresh_state_task = self._hass.async_create_task(self.refresh_state())

    def _cancel_delayed_refresh_state(self):
        """Cancel a delayed refresh state callback (if any exists)."""
        if self._unsub_refresh_state is None:
            return

        self._unsub_refresh_state()
        self._unsub_refresh_state = None

    async def refresh_10m(self, _=None):
        """Refresh Indego sensors every 10m."""
        _LOGGER.debug("Performing 10-minute refresh - fetching generic data, alerts, last completed/next mow")

        results = await asyncio.gather(
            *[
                self._update_generic_data(),
                self._update_alerts(),
                self._update_last_completed_mow(),
                self._update_next_mow(),
            ],
            return_exceptions=True,
        )

        next_refresh = 600
        index = 0
        for res in results:
            if res and isinstance(res, BaseException):
                try:
                    raise res
                except Exception as exc:
                    _LOGGER.warning("Update %d failed during 10-minute refresh: %s", index, str(exc))
            index += 1

        self._refresh_10m_remover = async_call_later(
            self._hass, next_refresh, self.refresh_10m
        )

    async def refresh_24h(self, _=None):
        """Refresh Indego sensors every 24h."""
        _LOGGER.debug("Performing 24-hour refresh - checking for firmware updates and availability")

        try:
            await self._update_updates_available()
            await self._update_firmware_version()

        except Exception as exc:
            _LOGGER.warning("Error during 24-hour refresh: %s", str(exc))

        self._refresh_24h_remover = async_call_later(self._hass, 86400, self.refresh_24h)

    def map_path(self):
        return f"/config/www/indego_map_{self._serial}.svg"

    async def download_and_store_map(self):
        try:
            _LOGGER.debug("Downloading lawn map from Bosch API for mower: %s", self._serial)
            svg_bytes = await self._indego_client.get(f"alms/{self._serial}/map")
            if svg_bytes:
                async with aiofiles.open(self.map_path(), "wb") as f:
                    await f.write(svg_bytes)
                _LOGGER.info("Lawn map successfully saved to: %s", self.map_path())
        except Exception as e:
            _LOGGER.error("Failed to download map from Bosch API for %s: %s", self._serial, e)

    async def start_periodic_position_update(self):
        self._unsub_map_timer = async_track_time_interval(
            self._hass, self._check_position_and_state, timedelta(seconds=60)
        )

    async def _check_position_and_state(self, now):
        try:
            _LOGGER.debug("Fetching latest mower position and state")
            await self._indego_client.update_state(force=True)
        except asyncio.TimeoutError:
            # Track consecutive timeouts to implement backoff
            self._consecutive_timeouts += 1

            # Only log on first timeout or after a minute of silence
            should_log = (
                self._consecutive_timeouts == 1 or
                (self._last_timeout_warning_time and
                 (time.time() - self._last_timeout_warning_time) > 60)
            )

            if should_log:
                _LOGGER.debug("Timeout while fetching position - mower may be offline or API is slow (attempt: %d)",
                            self._consecutive_timeouts)
                self._last_timeout_warning_time = time.time()
            return
        except Exception as e:
            self._consecutive_timeouts = 0  # Reset on other errors
            _LOGGER.debug("Error fetching position (current state: %s): %s", self._last_state, str(e))
            return

        # Successful update - reset timeout counter
        self._consecutive_timeouts = 0
        self._last_timeout_warning_time = None

        try:
            state = self._indego_client.state
            if not state:
                _LOGGER.warning("Received empty state object from API")
                return

            mower_state = self._indego_client.state_description
            xpos = getattr(state, "svg_xPos", None)
            ypos = getattr(state, "svg_yPos", None)
            self._last_state = mower_state

            _LOGGER.debug("Position: x=%s, y=%s | State: %s", xpos, ypos, mower_state)

            if mower_state and mower_state.lower() == "docked":
                _LOGGER.debug("Mower is docked - skipping position update")
                return

            if xpos is not None and ypos is not None:
                if (xpos, ypos) != self._last_position:
                    _LOGGER.info("Mower position changed: (%s, %s)", xpos, ypos)
                    self._last_position = (xpos, ypos)
                    for entity in self.entities.values():
                        if hasattr(entity, "refresh_map"):
                            await entity.refresh_map(mower_state)
        except Exception as e:
            _LOGGER.error("Unexpected error processing position update: %s", str(e))
    
    async def _update_operating_data(self):
        try:
            await self._indego_client.update_operating_data()
            _LOGGER.debug("Successfully fetched operating data from Bosch API")
        except Exception as exc:
            _LOGGER.warning("Failed to fetch operating data from Bosch API: %s", str(exc))
            return

        try:
            if not self._indego_client.operating_data:
                _LOGGER.debug("Operating data is empty - mower may not support this feature")
                return

            # Update battery
            try:
                if hasattr(self._indego_client.operating_data, 'battery') and self._indego_client.operating_data.battery:
                    battery_percent = self._indego_client.operating_data.battery.percent_adjusted
                    self.entities[ENTITY_BATTERY].state = battery_percent
                    _LOGGER.debug("Battery: %d%% | Voltage: %s V", battery_percent, getattr(self._indego_client.operating_data.battery, 'voltage', 'N/A'))

                    # Get battery values
                    voltage = getattr(self._indego_client.operating_data.battery, 'voltage', None)
                    discharge = getattr(self._indego_client.operating_data.battery, 'discharge', None)
                    cycles = getattr(self._indego_client.operating_data.battery, 'cycles', None)
                    battery_temp = getattr(self._indego_client.operating_data.battery, 'battery_temp', None)
                    ambient_temp = getattr(self._indego_client.operating_data.battery, 'ambient_temp', None)

                    # Update main battery sensor attributes (keep for backward compatibility)
                    self.entities[ENTITY_BATTERY].add_attributes(
                        {
                            "last_updated": last_updated_now(),
                            "voltage_V": voltage if voltage is not None else 'N/A',
                            "discharge_Ah": discharge if discharge is not None else 'N/A',
                            "cycles": cycles if cycles is not None else 'N/A',
                            f"battery_temp_{UnitOfTemperature.CELSIUS}": battery_temp if battery_temp is not None else 'N/A',
                            f"ambient_temp_{UnitOfTemperature.CELSIUS}": ambient_temp if ambient_temp is not None else 'N/A',
                        }
                    )

                    # Update individual battery sensors
                    if ENTITY_BATTERY_VOLTAGE in self.entities:
                        self.entities[ENTITY_BATTERY_VOLTAGE].state = voltage if voltage is not None else STATE_UNKNOWN

                    if ENTITY_BATTERY_DISCHARGE in self.entities:
                        if discharge is not None and voltage is not None:
                            # Convert Ah to Wh (Watt-hours) and make absolute
                            discharge_wh = abs(discharge) * voltage
                            self.entities[ENTITY_BATTERY_DISCHARGE].state = round(discharge_wh, 2)
                        else:
                            self.entities[ENTITY_BATTERY_DISCHARGE].state = STATE_UNKNOWN

                    if ENTITY_BATTERY_CYCLES in self.entities:
                        self.entities[ENTITY_BATTERY_CYCLES].state = cycles if cycles is not None else STATE_UNKNOWN

                    if ENTITY_BATTERY_TEMPERATURE in self.entities:
                        self.entities[ENTITY_BATTERY_TEMPERATURE].state = battery_temp if battery_temp is not None else STATE_UNKNOWN

                    if ENTITY_AMBIENT_TEMPERATURE in self.entities:
                        self.entities[ENTITY_AMBIENT_TEMPERATURE].state = ambient_temp if ambient_temp is not None else STATE_UNKNOWN
                else:
                    _LOGGER.debug("Battery data not available")
                    self.entities[ENTITY_BATTERY].state = STATE_UNKNOWN
            except AttributeError as exc:
                _LOGGER.error("Error accessing battery data: %s", str(exc))
                self.entities[ENTITY_BATTERY].state = STATE_UNKNOWN

            # Update garden size
            try:
                garden_size = None

                if self._indego_client.operating_data:
                    # Access garden object directly
                    garden = self._indego_client.operating_data.garden

                    if garden and garden.size:
                        garden_size = garden.size
                        _LOGGER.info("Garden size: %d m²", garden_size)
                    elif garden:
                        _LOGGER.debug("Garden object exists but size is not set")
                    else:
                        _LOGGER.debug("Garden data not available from API")
                else:
                    _LOGGER.debug("Operating data is None")

                if garden_size is not None and garden_size > 0:
                    self.entities[ENTITY_GARDEN_SIZE].state = garden_size
                else:
                    self.entities[ENTITY_GARDEN_SIZE].state = STATE_UNKNOWN

            except Exception as exc:
                _LOGGER.error("Error accessing garden size: %s", str(exc))
                self.entities[ENTITY_GARDEN_SIZE].state = STATE_UNKNOWN

        except Exception as exc:
            _LOGGER.error("Unexpected error while updating operating data: %s", str(exc))

    def set_online_state(self, online: bool):
        current_is_online = self.entities[ENTITY_ONLINE].state
        if current_is_online != online:
            if online:
                _LOGGER.info("Mower is now ONLINE")
            else:
                _LOGGER.warning("Mower is now OFFLINE")

        self.entities[ENTITY_ONLINE].state = online
        self.entities[ENTITY_MOWER_STATE].set_cloud_connection_state(online)
        self.entities[ENTITY_MOWER_STATE_DETAIL].set_cloud_connection_state(online)

        if ENTITY_VACUUM in self.entities:
            self.entities[ENTITY_VACUUM].set_cloud_connection_state(online)

        if ENTITY_LAWN_MOWER in self.entities:
            self.entities[ENTITY_LAWN_MOWER].set_cloud_connection_state(online)

    def set_service_status(self, service_up: bool):
        """Set the Bosch service status."""
        if ENTITY_SERVICE_STATUS not in self.entities:
            return

        current_status = self.entities[ENTITY_SERVICE_STATUS].state
        if current_status != service_up:
            if service_up:
                _LOGGER.info("Bosch service is now UP")
                self._last_service_error = None
            else:
                _LOGGER.info("Bosch service is now DOWN")

        self.entities[ENTITY_SERVICE_STATUS].state = service_up
        if self._last_service_error:
            self.entities[ENTITY_SERVICE_STATUS].add_attributes({
                "last_service_error": self._last_service_error
            })

    async def _update_state(self, longpoll: bool = True):
        try:
            _LOGGER.debug("Fetching mower state from Bosch API (longpoll: %s)", longpoll)
            await self._indego_client.update_state(longpoll=longpoll, longpoll_timeout=230)
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout while fetching mower state - mower may be offline or API is slow")
            self.set_online_state(False)
            return
        except ClientResponseError as exc:
            # Enhanced error handling with specific error code information
            error_code = str(exc.status)
            error_desc = get_error_description(f"{error_code}_timeout")
            error_severity = get_error_severity(f"{error_code}_timeout")

            log_msg = f"Failed to fetch mower state from Bosch API: {error_desc} (HTTP {exc.status})"
            if error_severity == ErrorSeverity.ERROR:
                _LOGGER.error(log_msg)
            elif error_severity == ErrorSeverity.WARNING:
                _LOGGER.warning(log_msg)
            else:
                _LOGGER.debug(log_msg)

            self.set_online_state(False)
            return
        except Exception as exc:
            _LOGGER.error("Failed to fetch mower state from Bosch API: %s", str(exc))
            self.set_online_state(False)
            return

        if self._shutdown:
            return

        if not self._indego_client.state:
            _LOGGER.warning("Received empty state from API - cannot process")
            self.set_online_state(False)
            return

        try:
            # Record successful API response
            self._last_successful_update = time.time()
            # Mark service as UP on successful response
            self.set_service_status(True)

            # Check for offline error codes (WiFi lost, API error, No connection to server)
            state_code = getattr(self._indego_client.state, 'state', None)
            if state_code in (802, 803, 804):
                _LOGGER.warning("Mower reported offline state (error code: %s)", state_code)
                self.set_online_state(False)
            else:
                # Update online state from API
                online = self._indego_client.online
                self.set_online_state(online)

            # Refresh Camera map if Position is available
            new_x = self._indego_client.state.svg_xPos
            new_y = self._indego_client.state.svg_yPos
            mower_state = self._indego_client.state_description

            if new_x is not None and new_y is not None:
                for entity in self.entities.values():
                    if hasattr(entity, "refresh_map"):
                        await entity.refresh_map(mower_state)

            # Update mower state (with safe getattr)
            try:
                state_desc = self._indego_client.state_description
                self.entities[ENTITY_MOWER_STATE].state = state_desc if state_desc else STATE_UNKNOWN
                _LOGGER.debug("Mower state: %s", state_desc)
            except Exception as exc:
                _LOGGER.error("Failed to update mower state sensor: %s", str(exc))
                self.entities[ENTITY_MOWER_STATE].state = STATE_UNKNOWN

            # Update mower state detail
            try:
                state_detail = self._indego_client.state_description_detail
                state_number = getattr(self._indego_client.state, 'state', 'unknown')
                self.entities[ENTITY_MOWER_STATE_DETAIL].state = state_detail if state_detail else STATE_UNKNOWN
                _LOGGER.debug("Mower detailed state: %s (code: %d)", state_detail, state_number if isinstance(state_number, int) else 0)
            except Exception as exc:
                _LOGGER.error("Failed to update mower state detail sensor: %s", str(exc))
                self.entities[ENTITY_MOWER_STATE_DETAIL].state = STATE_UNKNOWN

            # Update lawn mowed
            try:
                mowed = getattr(self._indego_client.state, 'mowed', None)
                self.entities[ENTITY_LAWN_MOWED].state = mowed if mowed is not None else STATE_UNKNOWN
                _LOGGER.debug("Lawn mowed: %d%%", mowed if mowed is not None else 0)

                # Calculate lawn mowed size in m²
                if ENTITY_LAWN_MOWED_SIZE in self.entities:
                    garden_size = None
                    if self._indego_client.operating_data:
                        garden = self._indego_client.operating_data.garden
                        if garden and garden.size:
                            garden_size = garden.size

                    if mowed is not None and garden_size is not None and garden_size > 0:
                        mowed_size = (garden_size * mowed) / 100
                        self.entities[ENTITY_LAWN_MOWED_SIZE].state = round(mowed_size, 2)
                        _LOGGER.debug("Lawn mowed area: %.2f m² (%.1f%%)", mowed_size, mowed)
                    else:
                        self.entities[ENTITY_LAWN_MOWED_SIZE].state = STATE_UNKNOWN
            except Exception as exc:
                _LOGGER.error("Failed to update lawn mowed data: %s", str(exc))
                self.entities[ENTITY_LAWN_MOWED].state = STATE_UNKNOWN
                if ENTITY_LAWN_MOWED_SIZE in self.entities:
                    self.entities[ENTITY_LAWN_MOWED_SIZE].state = STATE_UNKNOWN

            # Update runtime
            try:
                runtime = getattr(self._indego_client.state, 'runtime', None)
                if runtime and hasattr(runtime, 'total'):
                    cut_time = getattr(runtime.total, 'cut', None)

                    # Ensure runtime never decreases (TOTAL_INCREASING constraint)
                    current_state = self.entities[ENTITY_RUNTIME].state
                    if cut_time is not None:
                        # Convert current state to number if possible
                        try:
                            current_value = float(current_state) if current_state and current_state != STATE_UNKNOWN else 0
                        except (ValueError, TypeError):
                            current_value = 0

                        # Only update if new value is >= current value or current is unknown
                        if cut_time >= current_value:
                            self.entities[ENTITY_RUNTIME].state = cut_time
                            _LOGGER.debug("Total mowing time: %s hours", cut_time)
                        else:
                            _LOGGER.debug("Ignoring runtime decrease from %s to %s hours (API inconsistency)",
                                          current_value, cut_time)
                    else:
                        self.entities[ENTITY_RUNTIME].state = STATE_UNKNOWN
                else:
                    self.entities[ENTITY_RUNTIME].state = STATE_UNKNOWN
            except Exception as exc:
                _LOGGER.error("Failed to update runtime data: %s", str(exc))
                self.entities[ENTITY_RUNTIME].state = STATE_UNKNOWN

            # Update battery charging state
            try:
                self.entities[ENTITY_BATTERY].charging = (
                    self._indego_client.state_description_detail == "Charging"
                )
                # Also update battery charging binary sensor if it exists
                if ENTITY_BATTERY_CHARGING in self.entities:
                    self.entities[ENTITY_BATTERY_CHARGING].state = (
                        self._indego_client.state_description_detail == "Charging"
                    )
            except Exception as exc:
                _LOGGER.error("Failed to update battery charging state: %s", str(exc))
                self.entities[ENTITY_BATTERY].charging = False
                if ENTITY_BATTERY_CHARGING in self.entities:
                    self.entities[ENTITY_BATTERY_CHARGING].state = False

            # Update state attributes
            self.entities[ENTITY_MOWER_STATE].add_attributes(
                {"last_updated": last_updated_now()}
            )

            self.entities[ENTITY_MOWER_STATE_DETAIL].add_attributes(
                {
                    "last_updated": last_updated_now(),
                    "state_number": getattr(self._indego_client.state, 'state', 'unknown'),
                    "state_description": self._indego_client.state_description_detail,
                }
            )

            # Update lawn mowed attributes
            try:
                mow_attrs = {
                    "last_updated": last_updated_now(),
                }
                if hasattr(self._indego_client.state, 'runtime') and hasattr(self._indego_client.state.runtime, 'session'):
                    mow_attrs["last_session_operation_min"] = getattr(self._indego_client.state.runtime.session, 'operate', 'N/A')
                    mow_attrs["last_session_cut_min"] = getattr(self._indego_client.state.runtime.session, 'cut', 'N/A')
                    mow_attrs["last_session_charge_min"] = getattr(self._indego_client.state.runtime.session, 'charge', 'N/A')
                self.entities[ENTITY_LAWN_MOWED].add_attributes(mow_attrs)

                # Update lawn mowed size attributes
                if ENTITY_LAWN_MOWED_SIZE in self.entities:
                    self.entities[ENTITY_LAWN_MOWED_SIZE].add_attributes({
                        "last_updated": last_updated_now(),
                    })
            except Exception as exc:
                _LOGGER.error("Failed to update lawn mowed attributes: %s", str(exc))

            # Update runtime attributes
            try:
                runtime_attrs = {"last_updated": last_updated_now()}
                if hasattr(self._indego_client.state, 'runtime') and hasattr(self._indego_client.state.runtime, 'total'):
                    runtime_attrs["total_operation_time_h"] = getattr(self._indego_client.state.runtime.total, 'operate', 'N/A')
                    runtime_attrs["total_mowing_time_h"] = getattr(self._indego_client.state.runtime.total, 'cut', 'N/A')
                    runtime_attrs["total_charging_time_h"] = getattr(self._indego_client.state.runtime.total, 'charge', 'N/A')
                self.entities[ENTITY_RUNTIME].add_attributes(runtime_attrs)
            except Exception as exc:
                _LOGGER.error("Failed to update runtime attributes: %s", str(exc))

            # Update vacuum state
            if ENTITY_VACUUM in self.entities:
                try:
                    self.entities[ENTITY_VACUUM].indego_state = getattr(self._indego_client.state, 'state', None)
                except Exception as exc:
                    _LOGGER.error("Failed to update vacuum state: %s", str(exc))

            # Update lawn mower state
            if ENTITY_LAWN_MOWER in self.entities:
                try:
                    self.entities[ENTITY_LAWN_MOWER].indego_state = getattr(self._indego_client.state, 'state', None)
                    self.entities[ENTITY_LAWN_MOWER].indego_state_detail = self._indego_client.state_description_detail
                except Exception as exc:
                    _LOGGER.error("Failed to update lawn mower state: %s", str(exc))

            # Position tracking and stuck detection
            try:
                svg_x = getattr(self._indego_client.state, 'svg_xPos', None)
                svg_y = getattr(self._indego_client.state, 'svg_yPos', None)

                if svg_x is not None and svg_y is not None:
                    if ENTITY_MOWER_SVG_X in self.entities:
                        self.entities[ENTITY_MOWER_SVG_X].state = svg_x
                    if ENTITY_MOWER_SVG_Y in self.entities:
                        self.entities[ENTITY_MOWER_SVG_Y].state = svg_y

                    current_state_code = self._indego_client.state.state
                    is_mowing = 500 <= current_state_code <= 799
                    now = datetime.now()

                    # Track mowing session start
                    if is_mowing and self._mowing_session_start_time is None:
                        self._mowing_session_start_time = now
                        _LOGGER.debug("Mowing session started - activating stuck detection after grace period")
                    elif not is_mowing and self._mowing_session_start_time is not None:
                        self._mowing_session_start_time = None

                    # Detect position movement (5px threshold)
                    moved = self._last_svg_x is None or math.sqrt(
                        (svg_x - self._last_svg_x) ** 2 + (svg_y - self._last_svg_y) ** 2
                    ) > 5

                    if moved:
                        self._last_svg_x = svg_x
                        self._last_svg_y = svg_y
                        self._last_position_change_time = now

                    # Determine stuck status with adaptive timeout
                    stuck = False
                    if is_mowing and self._last_position_change_time is not None:
                        # Get timeout for current state (default 60s if state not in map)
                        timeout_seconds = self.STUCK_DETECTION_TIMEOUTS.get(current_state_code, 60)

                        # Check if grace period is active (first 60s of session)
                        grace_period_active = False
                        if self._mowing_session_start_time is not None:
                            session_duration = (now - self._mowing_session_start_time).total_seconds()
                            grace_period_active = session_duration < self.MOWING_SESSION_GRACE_PERIOD

                        # Only check for stuck after grace period ends
                        if not grace_period_active:
                            stuck = (now - self._last_position_change_time).total_seconds() > timeout_seconds

                    if ENTITY_MOWER_STUCK in self.entities:
                        self.entities[ENTITY_MOWER_STUCK].state = stuck
                        if stuck:
                            timeout_seconds = self.STUCK_DETECTION_TIMEOUTS.get(current_state_code, 60)
                            state_detail = self._indego_client.state_description_detail or "unknown"
                            _LOGGER.warning(
                                "Mower appears to be stuck - no movement detected for > %d seconds "
                                "(state: %d, detail: %s)",
                                timeout_seconds,
                                current_state_code,
                                state_detail,
                            )
                            self.entities[ENTITY_MOWER_STUCK].add_attributes({
                                "stuck_since": self._last_position_change_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "stuck_x": svg_x,
                                "stuck_y": svg_y,
                            })

                    if is_mowing:
                        self._map_trail.append((svg_x, svg_y))

                    self._hass.async_create_task(self._update_map_svg(svg_x, svg_y))
            except Exception as exc:
                _LOGGER.error("Failed to process position tracking: %s", str(exc))

            # Maintenance Hours Tracking
            try:
                self._update_maintenance_hours()
            except Exception as exc:
                _LOGGER.error("Failed to update maintenance hours: %s", str(exc))

            # Session Counting and Estimated Duration
            try:
                self._update_session_tracking()
            except Exception as exc:
                _LOGGER.error("Failed to update session tracking: %s", str(exc))

            # Error Code Tracking
            try:
                self._update_error_tracking()
            except Exception as exc:
                _LOGGER.error("Failed to update error tracking: %s", str(exc))

        except Exception as exc:
            _LOGGER.error("Unexpected error in _update_state: %s", str(exc))

    async def _update_generic_data(self):
        try:
            await self._indego_client.update_generic_data()
            _LOGGER.debug("Generic data fetched from Bosch API")
        except Exception as exc:
            _LOGGER.warning("Failed to fetch generic data from API: %s", str(exc))
            return None

        try:
            if self._indego_client.generic_data:
                if ENTITY_MOWING_MODE in self.entities:
                    mowing_mode = getattr(
                        self._indego_client.generic_data,
                        'mowing_mode_description',
                        STATE_UNKNOWN
                    )
                    self.entities[ENTITY_MOWING_MODE].state = mowing_mode
                    _LOGGER.debug("Mowing mode: %s", mowing_mode)
            else:
                _LOGGER.debug("Generic data is empty from API")
                if ENTITY_MOWING_MODE in self.entities:
                    self.entities[ENTITY_MOWING_MODE].state = STATE_UNKNOWN
        except Exception as exc:
            _LOGGER.error("Error processing generic data: %s", str(exc))
            if ENTITY_MOWING_MODE in self.entities:
                self.entities[ENTITY_MOWING_MODE].state = STATE_UNKNOWN

        return self._indego_client.generic_data

    async def _update_alerts(self):
        await self._indego_client.update_alerts()

        # Show "Problem" only if there are unread alerts
        unread_count = sum(
            1 for alert in self._indego_client.alerts
            if str(alert.read_status).strip().lower() == "unread"
        )
        self.entities[ENTITY_ALERT].state = unread_count > 0

        if self._indego_client.alerts:
            # Build complete alert attributes with enhanced error descriptions
            alert_attributes = {
                "alerts_count": self._indego_client.alerts_count,
                "last_alert_error_code": self._indego_client.alerts[0].error_code,
                "last_alert_message": self._indego_client.alerts[0].message,
                "last_alert_date": format_indego_date(self._indego_client.alerts[0].date),
                "last_alert_read": self._indego_client.alerts[0].read_status,
            }

            # Always store all alerts as individual attributes for easy extraction in automations
            for index, alert in enumerate(self._indego_client.alerts):
                error_code = str(alert.error_code)
                # Use new comprehensive error description
                error_desc = get_error_description(error_code)
                error_severity = get_error_severity(error_code)
                alert_time = format_indego_date(alert.date)

                # Format: "ERROR_CODE: Error Description - 2024-01-01 12:34:56 [SEVERITY]"
                alert_attributes[f"error_{index}"] = f"{error_code}: {error_desc} - {alert_time} [{error_severity.name}]"

                # Also store individual components for advanced use cases
                alert_attributes[f"error_{index}_code"] = error_code
                alert_attributes[f"error_{index}_description"] = error_desc
                alert_attributes[f"error_{index}_severity"] = error_severity.name
                alert_attributes[f"error_{index}_timestamp"] = alert_time
                alert_attributes[f"error_{index}_message"] = alert.message
                alert_attributes[f"error_{index}_read"] = alert.read_status

            self.entities[ENTITY_ALERT].add_attributes(alert_attributes, False)

            # Clear any other alerts that no longer exist
            alert_index = len(self._indego_client.alerts)
            while self.entities[ENTITY_ALERT].clear_attribute(f"error_{alert_index}", False):
                alert_index += 1

            # Also clear individual components if alerts were removed
            error_index = len(self._indego_client.alerts)
            while self.entities[ENTITY_ALERT].clear_attribute(f"error_{error_index}_code", False):
                error_index += 1
            while self.entities[ENTITY_ALERT].clear_attribute(f"error_{error_index}_severity", False):
                error_index += 1

            self.entities[ENTITY_ALERT].async_schedule_update_ha_state()

        else:
            self.entities[ENTITY_ALERT].set_attributes(
                {
                    "alerts_count": self._indego_client.alerts_count
                }
            )

            # Clear all error attributes when no alerts
            error_index = 0
            while self.entities[ENTITY_ALERT].clear_attribute(f"error_{error_index}", False):
                error_index += 1

            error_index = 0
            while self.entities[ENTITY_ALERT].clear_attribute(f"error_{error_index}_code", False):
                error_index += 1

    async def _update_updates_available(self):
        await self._indego_client.update_updates_available()

        self.entities[ENTITY_UPDATE_AVAILABLE].state = self._indego_client.update_available

    async def _update_last_completed_mow(self):
        await self._indego_client.update_last_completed_mow()

        if self._indego_client.last_completed_mow:
            self.entities[
                ENTITY_LAST_COMPLETED
            ].state = self._indego_client.last_completed_mow.isoformat()

            self.entities[ENTITY_LAWN_MOWED].add_attributes(
                {
                    "last_completed_mow": format_indego_date(self._indego_client.last_completed_mow)
                }
            )

    async def _update_next_mow(self):
        await self._indego_client.update_next_mow()

        if self._indego_client.next_mow:
            self.entities[ENTITY_NEXT_MOW].state = self._indego_client.next_mow.isoformat()

            next_mow = format_indego_date(self._indego_client.next_mow)

            self.entities[ENTITY_NEXT_MOW].add_attributes(
                {"next_mow": next_mow}
            )

            self.entities[ENTITY_LAWN_MOWED].add_attributes(
                {"next_mow": next_mow}
            )

    async def _update_map_svg(self, current_x: int, current_y: int):
        """Fetch SVG map and save to www."""
        try:
            if self._map_svg is None:
                _LOGGER.debug("Fetching lawn map SVG from Bosch API")
                svg_bytes = await self._indego_client.get(f"alms/{self._serial}/map")
                if svg_bytes:
                    self._map_svg = svg_bytes.decode("utf-8") if isinstance(svg_bytes, bytes) else svg_bytes

            if not self._map_svg:
                return

            www_path = self._hass.config.path("www")
            os.makedirs(www_path, exist_ok=True)
            map_path = os.path.join(www_path, f"indego_map_{self._serial}.svg")

            async with aiofiles.open(map_path, "w") as f:
                await f.write(self._map_svg)

        except Exception as exc:
            _LOGGER.debug("Could not update lawn map: %s", str(exc))

    def _update_session_tracking(self):
        """Track session count and calculate estimated duration."""
        try:
            current_state = getattr(self._indego_client.state, 'state', None)
            if current_state is None:
                _LOGGER.debug("State not available for session tracking")
                return

            is_mowing = 500 <= current_state <= 799

            # Count transitions to mowing state
            if is_mowing and self._last_session_state != current_state:
                if not (500 <= (self._last_session_state or 0) <= 799):
                    self._session_count += 1
                    _LOGGER.info("New mowing session started - Total sessions: %d", self._session_count)

            self._last_session_state = current_state

            if ENTITY_SESSION_COUNT in self.entities:
                self.entities[ENTITY_SESSION_COUNT].state = self._session_count
        except Exception as exc:
            _LOGGER.error("Error updating session tracking: %s", str(exc))

    def _update_error_tracking(self):
        """Track error codes and descriptions from last alert."""
        if ENTITY_LAST_ERROR_CODE not in self.entities:
            return

        try:
            if self._indego_client.alerts and len(self._indego_client.alerts) > 0:
                latest_alert = self._indego_client.alerts[0]
                error_code = str(latest_alert.error_code)

                # Use new comprehensive error description
                error_description = get_error_description(error_code)
                error_severity = get_error_severity(error_code)

                self._last_error_code = error_code
                self._last_error_time = latest_alert.date

                self.entities[ENTITY_LAST_ERROR_CODE].state = error_description
                self.entities[ENTITY_LAST_ERROR_CODE].add_attributes({
                    "error_code": error_code,
                    "error_time": format_indego_date(latest_alert.date),
                    "error_severity": error_severity.name,
                })

                # Log with appropriate level based on severity
                if error_severity == ErrorSeverity.CRITICAL:
                    _LOGGER.critical("CRITICAL mower error: %s (Code: %s)", error_description, error_code)
                elif error_severity == ErrorSeverity.ERROR:
                    _LOGGER.error("Mower error: %s (Code: %s)", error_description, error_code)
                elif error_severity == ErrorSeverity.WARNING:
                    _LOGGER.warning("Mower warning: %s (Code: %s)", error_description, error_code)
                else:
                    _LOGGER.info("Mower info: %s (Code: %s)", error_description, error_code)
            else:
                self.entities[ENTITY_LAST_ERROR_CODE].state = "No errors"
                self.entities[ENTITY_LAST_ERROR_CODE].add_attributes({
                    "error_code": "0",
                    "error_time": "N/A",
                    "error_severity": ErrorSeverity.INFO.name,
                })
        except Exception as exc:
            _LOGGER.error("Failed to process error tracking: %s", str(exc))
            self.entities[ENTITY_LAST_ERROR_CODE].state = STATE_UNKNOWN

    def _check_offline_timeout(self):
        """Check if mower should be marked offline due to timeout (no successful API response)."""
        if self._last_successful_update is None:
            # No successful update yet, don't set offline by timeout
            return

        current_time = time.time()
        time_since_success = current_time - self._last_successful_update

        if time_since_success > ONLINE_TIMEOUT_SECONDS:
            _LOGGER.warning("Mower offline - no successful API response for %d seconds (timeout threshold: %d seconds)",
                           int(time_since_success), ONLINE_TIMEOUT_SECONDS)
            self.set_online_state(False)

    async def _update_firmware_version(self):
        """Update firmware version sensor."""
        if ENTITY_FIRMWARE_VERSION not in self.entities:
            return

        try:
            # Firmware version is available in generic_data, not directly on client
            if self._indego_client.generic_data:
                firmware_version = getattr(self._indego_client.generic_data, "alm_firmware_version", None)
                if firmware_version:
                    self.entities[ENTITY_FIRMWARE_VERSION].state = str(firmware_version)
                    _LOGGER.debug("Firmware version: %s", firmware_version)
                else:
                    _LOGGER.debug("Firmware version not available from API")
                    self.entities[ENTITY_FIRMWARE_VERSION].state = STATE_UNKNOWN
            else:
                _LOGGER.debug("Generic data not available for firmware check")
                self.entities[ENTITY_FIRMWARE_VERSION].state = STATE_UNKNOWN
        except Exception as e:
            _LOGGER.error("Error fetching firmware version: %s", str(e))
            self.entities[ENTITY_FIRMWARE_VERSION].state = STATE_UNKNOWN

    def _update_maintenance_hours(self):
        """Track maintenance hours based on cumulative operation time."""
        if ENTITY_MAINTENANCE_HOURS not in self.entities:
            return

        try:
            runtime = getattr(self._indego_client.state, 'runtime', None)
            if not runtime:
                _LOGGER.debug("Runtime data not available for maintenance calculation")
                return

            total_hours = getattr(runtime.total if hasattr(runtime, 'total') else runtime, 'operate', None)
            if total_hours is None:
                _LOGGER.debug("Total operation hours not available")
                self.entities[ENTITY_MAINTENANCE_HOURS].state = STATE_UNKNOWN
                return

            # Maintenance recommendations (based on Indego specs)
            if total_hours < 50:
                maintenance_status = "good"
            elif total_hours < 150:
                maintenance_status = "service_due_soon"
            else:
                maintenance_status = "service_required"

            self.entities[ENTITY_MAINTENANCE_HOURS].state = int(total_hours)
            self.entities[ENTITY_MAINTENANCE_HOURS].add_attributes({
                "maintenance_status": maintenance_status,
            })
            _LOGGER.debug("Maintenance status: %d hours - %s", int(total_hours), maintenance_status)
        except Exception as exc:
            _LOGGER.error("Error calculating maintenance status: %s", str(exc))
            self.entities[ENTITY_MAINTENANCE_HOURS].state = STATE_UNKNOWN

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def client(self) -> IndegoAsyncClient:
        return self._indego_client
