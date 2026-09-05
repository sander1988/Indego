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
from homeassistant.exceptions import (
    HomeAssistantError,
    ConfigEntryAuthFailed,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
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
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    PERCENTAGE,
    UnitOfArea,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfTime,
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
from .weather import IndegoWeather
from . import diagnostics, repairs

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA_COMMAND = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(CONF_SEND_COMMAND): cv.string
})

SERVICE_SCHEMA_SMARTMOWING = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(CONF_SMARTMOWING): cv.boolean
})

SERVICE_SCHEMA_DELETE_ALERT = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(SERVER_DATA_ALERT_INDEX): cv.positive_int
})

SERVICE_SCHEMA_DELETE_ALERT_ALL = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id
})

SERVICE_SCHEMA_READ_ALERT = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(SERVER_DATA_ALERT_INDEX): cv.positive_int
})

SERVICE_SCHEMA_READ_ALERT_ALL = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id
})

SERVICE_SCHEMA_DOWNLOAD_MAP = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id
})

SERVICE_SCHEMA_SET_CALENDAR_SLOT = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(CONF_DAYS): vol.All(
        cv.ensure_list,
        [vol.In([
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ])],
    ),
    vol.Required(CONF_SLOT): vol.In([1, 2]),
    vol.Optional(CONF_ENABLED, default=True): cv.boolean,
    vol.Optional(CONF_START): cv.string,
    vol.Optional(CONF_END): cv.string,
})

SERVICE_SCHEMA_SET_PREDICTIVE_MOWING_WINDOW = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(CONF_EARLIEST_START): cv.string,
    vol.Required(CONF_LATEST_END): cv.string,
})

SERVICE_SCHEMA_SET_BUMP_SENSITIVITY = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(CONF_BUMP_SENSITIVITY): vol.In([
        "normal",
        "slippery",
        "uneven",
    ]),
})

SERVICE_SCHEMA_SET_PIN = vol.Schema({
    vol.Optional(CONF_MOWER_SERIAL): cv.string,
    vol.Optional(CONF_MOWER_ENTITY): cv.entity_id,
    vol.Required(CONF_PIN): vol.All(
        cv.string,
        vol.Length(min=4, max=4),
    ),
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
        CONF_ENTITY_CATEGORY: None,
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
        CONF_ENTITY_CATEGORY: None,
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
        CONF_ICON: "mdi:battery",
        CONF_DEVICE_CLASS: SensorDeviceClass.BATTERY,
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
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
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
        CONF_ATTR: [
            "last_updated",
            "last_completed_mow",
            "next_mow",
            "last_session_operation_min",
            "last_session_cut_min",
            "last_session_charge_min",
        ],
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_TRANSLATION_KEY: "lawn_mowed",
    },
    ENTITY_LAWN_MOWED_SIZE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:grass",
        CONF_DEVICE_CLASS: SensorDeviceClass.AREA,
        CONF_UNIT_OF_MEASUREMENT: UnitOfArea.SQUARE_METERS,
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
        CONF_ENTITY_CATEGORY: None,
        CONF_TRANSLATION_KEY: "mowing_mode",
    },
    ENTITY_RUNTIME: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:information-outline",
        CONF_DEVICE_CLASS: SensorDeviceClass.DURATION,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTime.HOURS,
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
        CONF_DEVICE_CLASS: SensorDeviceClass.AREA,
        CONF_UNIT_OF_MEASUREMENT: UnitOfArea.SQUARE_METERS,
        CONF_ATTR: [],
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_ENTITY_CATEGORY: None,
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
        CONF_STATE_CLASS: None,
        CONF_TRANSLATION_KEY: "mower_position_x",
    },
    ENTITY_MOWER_SVG_Y: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:map-marker",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: "px",
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_STATE_CLASS: None,
        CONF_TRANSLATION_KEY: "mower_position_y",
    },
    ENTITY_MOWER_STUCK: {
        CONF_TYPE: BINARY_SENSOR_TYPE,
        CONF_ICON: "mdi:alert-circle-outline",
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
        CONF_ATTR: ["stuck_since", "stuck_x", "stuck_y"],
        CONF_ENTITY_CATEGORY: None,
        CONF_TRANSLATION_KEY: "mower_stuck",
    },
    ENTITY_LAST_ERROR_CODE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:alert",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: ["error_code", "error_time"],
        CONF_ENTITY_CATEGORY: None,
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
        CONF_DEVICE_CLASS: SensorDeviceClass.DURATION,
        CONF_UNIT_OF_MEASUREMENT: UnitOfTime.HOURS,
        CONF_ATTR: ["maintenance_status"],
        CONF_STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "maintenance_hours",
    },
    ENTITY_SESSION_COUNT: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:counter",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "session_count",
    },
    ENTITY_BATTERY_VOLTAGE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:lightning-bolt",
        CONF_DEVICE_CLASS: SensorDeviceClass.VOLTAGE,
        CONF_UNIT_OF_MEASUREMENT: UnitOfElectricPotential.VOLT,
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
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
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
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
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "ambient_temperature",
    },
    ENTITY_BATTERY_CYCLES: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:battery-sync",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "battery_cycles",
    },
    ENTITY_BATTERY_DISCHARGE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:battery-minus",
        CONF_DEVICE_CLASS: SensorDeviceClass.ENERGY,
        CONF_UNIT_OF_MEASUREMENT: UnitOfEnergy.WATT_HOUR,
        CONF_ATTR: [],
        CONF_ENABLED_BY_DEFAULT: False,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
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
    ENTITY_PREDICTIVE_CALENDAR_SLOTS: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:calendar-remove",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [
            "last_updated",
            "smartmowing_enabled",
            "mowing_mode",
            "allowed_mowing_time",
            "earliest_start",
            "latest_end",
            "blocked_time",
            "blocked_before",
            "blocked_after",
        ],
        CONF_TRANSLATION_KEY: "predictive_calendar_slots",
    },
    ENTITY_CALENDAR_SLOTS: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:calendar-clock",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [
            "last_updated",
            "today_slot_1",
            "today_slot_2",
            "monday_slot_1",
            "monday_slot_2",
            "tuesday_slot_1",
            "tuesday_slot_2",
            "wednesday_slot_1",
            "wednesday_slot_2",
            "thursday_slot_1",
            "thursday_slot_2",
            "friday_slot_1",
            "friday_slot_2",
            "saturday_slot_1",
            "saturday_slot_2",
            "sunday_slot_1",
            "sunday_slot_2",
        ],
        CONF_TRANSLATION_KEY: "calendar_slots",
    },
    ENTITY_PREDICTIVE_SCHEDULE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:calendar-search",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [
            "last_updated",
            "next_mow_slot",
            "next_mow_day",
            "next_mow_time",
            "schedule_monday",
            "schedule_tuesday",
            "schedule_wednesday",
            "schedule_thursday",
            "schedule_friday",
            "schedule_saturday",
            "schedule_sunday",
            "exclusion_monday_user",
            "exclusion_monday_weather",
            "exclusion_tuesday_user",
            "exclusion_tuesday_weather",
            "exclusion_wednesday_user",
            "exclusion_wednesday_weather",
            "exclusion_thursday_user",
            "exclusion_thursday_weather",
            "exclusion_friday_user",
            "exclusion_friday_weather",
            "exclusion_saturday_user",
            "exclusion_saturday_weather",
            "exclusion_sunday_user",
            "exclusion_sunday_weather",
        ],
        CONF_ENTITY_CATEGORY: None,
        CONF_TRANSLATION_KEY: "predictive_schedule",
    },
    ENTITY_NETWORK_SIGNAL: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:signal-cellular-outline",
        CONF_DEVICE_CLASS: SensorDeviceClass.SIGNAL_STRENGTH,
        CONF_UNIT_OF_MEASUREMENT: SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        CONF_ATTR: ["last_updated"],
        CONF_TRANSLATION_KEY: "network_signal",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        CONF_ENABLED_BY_DEFAULT: False,
    },
    ENTITY_NETWORK_OPERATOR: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:access-point-network",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: ["last_updated"],
        CONF_TRANSLATION_KEY: "network_operator",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_ENABLED_BY_DEFAULT: False,
    },
    ENTITY_NETWORK_MODE: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:network-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: ["last_updated"],
        CONF_TRANSLATION_KEY: "network_mode",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_ENABLED_BY_DEFAULT: False,
    },
    ENTITY_PREDICTIVE_WEATHER: {
        CONF_TYPE: WEATHER_TYPE,
        CONF_ICON: "mdi:weather-partly-cloudy",
        CONF_TRANSLATION_KEY: "predictive_weather",
    },
    ENTITY_PREDICTIVE_SETUP: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:cog-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [
            "last_updated",
            "mowing_duration",
            "full_cuts",
            "avoid_rain",
            "avoid_temperature",
            "use_grass_growth",
            "rain_factor",
            "temperature_factor",
            "garden_latitude",
            "garden_longitude",
            "garden_timezone",
            "garden_name",
            "garden_country",
        ],
        CONF_TRANSLATION_KEY: "predictive_setup",
        CONF_ENTITY_CATEGORY: None,
    },
    ENTITY_BUMP_SENSITIVITY: {
        CONF_TYPE: SENSOR_TYPE,
        CONF_ICON: "mdi:alert-circle-outline",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ATTR: [
            "last_updated",
        ],
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "bump_sensitivity",
    },
    ENTITY_SECURITY_ENABLED: {
        CONF_TYPE: SWITCH_TYPE,
        CONF_ICON: "mdi:shield-lock",
        CONF_DEVICE_CLASS: None,
        CONF_TRANSLATION_KEY: "security_enabled",
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
    },
    ENTITY_AUTOLOCK: {
        CONF_TYPE: SWITCH_TYPE,
        CONF_ICON: "mdi:lock-clock",
        CONF_DEVICE_CLASS: None,
        CONF_TRANSLATION_KEY: "autolock",
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
    },
    ENTITY_AUTOMATIC_UPDATE: {
        CONF_TYPE: SWITCH_TYPE,
        CONF_ICON: "mdi:update",
        CONF_DEVICE_CLASS: None,
        CONF_TRANSLATION_KEY: "automatic_update",
        CONF_ATTR: [],
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
    },
}

def format_indego_date(date: datetime) -> str:
    return date.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def last_updated_now() -> str:
    return homeassistant.util.dt.as_local(utcnow()).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

def _format_calendar_slot(slot) -> str:
    return (
        f"{slot.StHr:02d}:{slot.StMin:02d}-"
        f"{slot.EnHr:02d}:{slot.EnMin:02d}"
    )


def _calendar_slots_by_day(calendar) -> dict:
    result = {}

    day_names = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    for day_name in day_names:
        result[f"{day_name}_slot_1"] = "not_enabled"
        result[f"{day_name}_slot_2"] = "not_enabled"

    if calendar is None or not getattr(calendar, "days", None):
        return result

    for day in calendar.days:
        day_name = getattr(day, "day_name", None)
        if day_name not in day_names:
            continue

        slots = getattr(day, "slots", [])

        for index in range(2):
            attr_name = f"{day_name}_slot_{index + 1}"

            if index >= len(slots):
                result[attr_name] = "not_configured"
                continue

            slot = slots[index]

            if getattr(slot, "En", False):
                result[attr_name] = _format_calendar_slot(slot)
            else:
                result[attr_name] = "not_enabled"

    return result

def _today_calendar_slots(slots_by_day: dict) -> list:
    today_name = _today_calendar_day_name()

    return [
        slot
        for slot in [
            slots_by_day.get(f"{today_name}_slot_1"),
            slots_by_day.get(f"{today_name}_slot_2"),
        ]
        if slot not in (None, "not_enabled", "not_configured")
    ]

def _today_calendar_day_name() -> str:
    return datetime.now().strftime("%A").lower()

DAY_NAME_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _parse_slot_time(value: str) -> tuple[int, int]:
    parts = str(value).split(":")

    if len(parts) not in (2, 3):
        raise ValueError("Time must be in HH:MM or HH:MM:SS format")

    hour = int(parts[0])
    minute = int(parts[1])

    if len(parts) == 3 and int(parts[2]) != 0:
        raise ValueError("Seconds must be 00")

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("Time must be between 00:00 and 23:59")

    return hour, minute


def _calendar_to_payload(calendar, selected_cal: int = 1) -> dict:
    days = []

    for day_index in range(7):
        days.append({
            "day": day_index,
            "slots": [
                {"En": False, "StHr": None, "StMin": None, "EnHr": None, "EnMin": None},
                {"En": False, "StHr": None, "StMin": None, "EnHr": None, "EnMin": None},
            ],
        })

    if calendar is not None and getattr(calendar, "days", None):
        for day in calendar.days:
            day_index = getattr(day, "day", None)
            if day_index is None or day_index < 0 or day_index > 6:
                continue

            slots = getattr(day, "slots", [])
            for slot_index in range(min(len(slots), 2)):
                slot = slots[slot_index]
                days[day_index]["slots"][slot_index] = {
                    "En": bool(getattr(slot, "En", False)),
                    "StHr": getattr(slot, "StHr", None),
                    "StMin": getattr(slot, "StMin", None),
                    "EnHr": getattr(slot, "EnHr", None),
                    "EnMin": getattr(slot, "EnMin", None),
                }

    return {
        "sel_cal": selected_cal,
        "cals": [
            {
                "cal": selected_cal,
                "days": days,
            }
        ],
    }

def _predictive_calendar_payload(earliest_start: str, latest_end: str) -> dict:
    start_hour, start_minute = _parse_slot_time(earliest_start)
    end_hour, end_minute = _parse_slot_time(latest_end)

    days = []

    for day_index in range(7):
        days.append({
            "day": day_index,
            "slots": [
                {
                    "En": True,
                    "StHr": 0,
                    "StMin": 0,
                    "EnHr": start_hour,
                    "EnMin": start_minute,
                },
                {
                    "En": True,
                    "StHr": end_hour,
                    "StMin": end_minute,
                    "EnHr": 23,
                    "EnMin": 59,
                },
            ],
        })

    return {
        "sel_cal": 1,
        "cals": [
            {
                "cal": 1,
                "days": days,
            }
        ],
    }

def _predictive_calendar_window(calendar, hass) -> dict:
    result = {
        "earliest_start": "not_enabled",
        "latest_end": "not_enabled",
        "blocked_before": "not_enabled",
        "blocked_after": "not_enabled",
        "allowed_mowing_time": "not_enabled",
        "blocked_time": "not_enabled",
    }

    if calendar is None or not getattr(calendar, "days", None):
        return result

    first_day = calendar.days[0]
    slots = getattr(first_day, "slots", [])

    if len(slots) > 0 and getattr(slots[0], "En", False):
        result["blocked_before"] = _format_calendar_slot(slots[0])
        result["earliest_start"] = f"{slots[0].EnHr:02d}:{slots[0].EnMin:02d}"

    if len(slots) > 1 and getattr(slots[1], "En", False):
        result["blocked_after"] = _format_calendar_slot(slots[1])
        result["latest_end"] = f"{slots[1].StHr:02d}:{slots[1].StMin:02d}"

    if (
        result["earliest_start"] != "not_enabled"
        and result["latest_end"] != "not_enabled"
    ):
        result["allowed_mowing_time"] = (
            f"{_localized_text(hass, 'allowed_mowing_time')} "
            f"{result['earliest_start']}-{result['latest_end']}"
        )
        result["blocked_time"] = (
            f"{result['latest_end']}-{result['earliest_start']}"
        )

    return result

def _set_payload_slot(payload: dict, day_name: str, slot_number: int, enabled: bool, start: str | None, end: str | None) -> dict:
    day_index = DAY_NAME_TO_INDEX[day_name]
    slot_index = slot_number - 1

    slot = payload["cals"][0]["days"][day_index]["slots"][slot_index]

    if not enabled:
        slot.update({
            "En": False,
            "StHr": None,
            "StMin": None,
            "EnHr": None,
            "EnMin": None,
        })
        return payload

    if not start or not end:
        raise ValueError("start and end are required when enabled is true")

    start_hour, start_minute = _parse_slot_time(start)
    end_hour, end_minute = _parse_slot_time(end)

    slot.update({
        "En": True,
        "StHr": start_hour,
        "StMin": start_minute,
        "EnHr": end_hour,
        "EnMin": end_minute,
    })

    return payload

def _schedule_slot_to_text(slot) -> str:
    return (
        f"{slot.StHr:02d}:{slot.StMin:02d}-"
        f"{slot.EnHr:02d}:{slot.EnMin:02d}"
    )


def _predictive_schedule_attributes(schedule, hass) -> dict:
    day_names = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    attrs = {
        "next_mow_slot": "none",
        "next_mow_day": "none",
        "next_mow_time": "none",
    }

    for day_name in day_names:
        attrs[f"schedule_{day_name}"] = "not_scheduled"
        attrs[f"exclusion_{day_name}_user"] = "none"
        attrs[f"exclusion_{day_name}_weather"] = "none"

    if schedule is None:
        return attrs

    schedule_days = getattr(schedule, "schedule_days", None) or []
    exclusion_days = getattr(schedule, "exclusion_days", None) or []

    for day in schedule_days:
        day_name = getattr(day, "day_name", None)
        if day_name not in day_names:
            continue

        slots = getattr(day, "slots", []) or []
        slot_texts = [
            _schedule_slot_to_text(slot)
            for slot in slots
            if getattr(slot, "En", True)
        ]

        if slot_texts:
            attrs[f"schedule_{day_name}"] = ", ".join(slot_texts)

            if attrs["next_mow_slot"] == "none":
                attrs["next_mow_slot"] = (
                    f"{_localized_text(hass, day_name)} {slot_texts[0]}"
                )
                attrs["next_mow_day"] = day_name
                attrs["next_mow_time"] = slot_texts[0]

    for day in exclusion_days:
        day_name = getattr(day, "day_name", None)
        if day_name not in day_names:
            continue

        user_slots = []
        weather_slots = []

        for slot in getattr(day, "slots", []) or []:
            text = _schedule_slot_to_text(slot)
            attr = getattr(slot, "Attr", None)

            if attr == "C":
                user_slots.append(text)
            else:
                weather_slots.append(text)

        if user_slots:
            attrs[f"exclusion_{day_name}_user"] = ", ".join(user_slots)

        if weather_slots:
            attrs[f"exclusion_{day_name}_weather"] = ", ".join(weather_slots)

    return attrs

def _is_smartmowing_active(generic_data, forced_mowing_mode=None) -> bool:
    mowing_mode = forced_mowing_mode or getattr(
        generic_data,
        "mowing_mode_description",
        None,
    )
    return str(mowing_mode).lower() == "smartmowing"

def _is_calendar_selection_required(generic_data) -> bool:
    mowing_mode = getattr(
        generic_data,
        "mowing_mode_description",
        None,
    )
    alm_mode = getattr(
        generic_data,
        "alm_mode",
        None,
    )

    return (
        str(mowing_mode).lower() == "manual"
        or str(alm_mode).lower() == "manual"
    )

LOCALIZED_TEXTS = {
    "de": {
        "allowed_mowing_time": "Erlaubte Mähzeit",
        "monday": "Montag",
        "tuesday": "Dienstag",
        "wednesday": "Mittwoch",
        "thursday": "Donnerstag",
        "friday": "Freitag",
        "saturday": "Samstag",
        "sunday": "Sonntag",
    },
    "en": {
        "allowed_mowing_time": "Allowed mowing time",
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
        "sunday": "Sunday",
    },
    "da": {
        "allowed_mowing_time": "Tilladt klippetid",
        "monday": "Mandag",
        "tuesday": "Tirsdag",
        "wednesday": "Onsdag",
        "thursday": "Torsdag",
        "friday": "Fredag",
        "saturday": "Lørdag",
        "sunday": "Søndag",
    },
    "es": {
        "allowed_mowing_time": "Tiempo de corte permitido",
        "monday": "Lunes",
        "tuesday": "Martes",
        "wednesday": "Miércoles",
        "thursday": "Jueves",
        "friday": "Viernes",
        "saturday": "Sábado",
        "sunday": "Domingo",
    },
    "fr": {
        "allowed_mowing_time": "Heure de tonte autorisée",
        "monday": "Lundi",
        "tuesday": "Mardi",
        "wednesday": "Mercredi",
        "thursday": "Jeudi",
        "friday": "Vendredi",
        "saturday": "Samedi",
        "sunday": "Dimanche",
    },
    "it": {
        "allowed_mowing_time": "Orario di taglio consentito",
        "monday": "Lunedì",
        "tuesday": "Martedì",
        "wednesday": "Mercoledì",
        "thursday": "Giovedì",
        "friday": "Venerdì",
        "saturday": "Sabato",
        "sunday": "Domenica",
    },
    "nl": {
        "allowed_mowing_time": "Toegestane maaitijd",
        "monday": "Maandag",
        "tuesday": "Dinsdag",
        "wednesday": "Woensdag",
        "thursday": "Donderdag",
        "friday": "Vrijdag",
        "saturday": "Zaterdag",
        "sunday": "Zondag",
    },
    "no": {
        "allowed_mowing_time": "Tillatt klippetid",
        "monday": "Mandag",
        "tuesday": "Tirsdag",
        "wednesday": "Onsdag",
        "thursday": "Torsdag",
        "friday": "Fredag",
        "saturday": "Lørdag",
        "sunday": "Søndag",
    },
    "pl": {
        "allowed_mowing_time": "Dozwolony czas koszenia",
        "monday": "Poniedziałek",
        "tuesday": "Wtorek",
        "wednesday": "Środa",
        "thursday": "Czwartek",
        "friday": "Piątek",
        "saturday": "Sobota",
        "sunday": "Niedziela",
    },
    "sk": {
        "allowed_mowing_time": "Povolený čas kosenia",
        "monday": "Pondelok",
        "tuesday": "Utorok",
        "wednesday": "Streda",
        "thursday": "Štvrtok",
        "friday": "Piatok",
        "saturday": "Sobota",
        "sunday": "Nedeľa",
    },
    "sv": {
        "allowed_mowing_time": "Tillåten klipptid",
        "monday": "Måndag",
        "tuesday": "Tisdag",
        "wednesday": "Onsdag",
        "thursday": "Torsdag",
        "friday": "Fredag",
        "saturday": "Lördag",
        "sunday": "Söndag",
    },
}

NETWORK_OPERATORS = {
    (262, 1): "Telekom",
    (262, 2): "Vodafone",
    (262, 3): "O2",
    (262, 7): "O2",
}

def _language_code(hass) -> str:
    language = getattr(hass.config, "language", None) or "en"
    return language.split("-")[0].lower()


def _localized_text(hass, key: str) -> str:
    language = _language_code(hass)
    return LOCALIZED_TEXTS.get(
        language,
        LOCALIZED_TEXTS["en"],
    ).get(key, key)

def _network_operator_name(value):
    """Return readable network operator name."""
    if value is None:
        return None

    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)

    mcc = value // 100
    mnc = value % 100

    return NETWORK_OPERATORS.get(
        (mcc, mnc),
        f"{mcc}-{mnc}",
    )
def _config_to_payload(config) -> dict:
    """Convert pyIndego config object to API payload."""
    if isinstance(config, dict):
        return dict(config)

    if hasattr(config, "model_dump"):
        return config.model_dump(exclude_none=True)

    if hasattr(config, "dict"):
        return config.dict(exclude_none=True)

    if hasattr(config, "__dict__"):
        return {
            key: value
            for key, value in vars(config).items()
            if not key.startswith("_")
        }

    raise ValueError(f"Unsupported config type: {type(config)}")

def _get_config_value(config, *keys):
    """Get config value from dict or object using multiple possible field names."""
    if config is None:
        return None

    if isinstance(config, dict):
        for key in keys:
            if key in config:
                return config[key]
        return None

    for key in keys:
        if hasattr(config, key):
            return getattr(config, key)

    return None

def _bump_sensitivity_state(value) -> str:
    mapping = {
        0: "normal",
        1: "slippery",
        2: "uneven",
    }

    try:
        return mapping.get(int(value), str(value))
    except (TypeError, ValueError):
        return STATE_UNKNOWN

def _bump_sensitivity_value(value) -> int:
    mapping = {
        "normal": 0,
        "slippery": 1,
        "uneven": 2,
    }

    return mapping[str(value).lower()]

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

    async def load_platforms():
        _LOGGER.debug("Loading Home Assistant platforms: %s", INDEGO_PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, INDEGO_PLATFORMS)

    try:
        await indego_hub.update_generic_data_and_load_platforms(load_platforms)

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
        mower_entity = call.data.get(CONF_MOWER_ENTITY, None)
        mower_serial = call.data.get(CONF_MOWER_SERIAL, None)
        
        if mower_entity is not None:
            for config_entry_id in hass.data[DOMAIN]:
                if config_entry_id == CONF_SERVICES_REGISTERED:
                    continue

                instance = hass.data[DOMAIN][config_entry_id]
                expected_entity_id = f"lawn_mower.indego_{instance.serial}"

                if mower_entity == expected_entity_id:
                    return instance

            raise HomeAssistantError(
                "No mower instance found for entity '%s'" % mower_entity
            )

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
        enable_bool = enable is True

        _LOGGER.info("Setting smart mowing mode to: %s (Mower: %s)", enable_bool, instance._serial)


        await instance._indego_client.put_mow_mode(enable_bool)

        instance._forced_mowing_mode = "SmartMowing" if enable_bool else "Calendar"

        if ENTITY_SMARTMOWING_SWITCH in instance.entities:
            instance.entities[ENTITY_SMARTMOWING_SWITCH].is_on = enable_bool

        if ENTITY_MOWING_MODE in instance.entities:
            instance.entities[ENTITY_MOWING_MODE].state = (
                "SmartMowing" if enable_bool else "Calendar"
            )

        await asyncio.sleep(3)

        await instance._update_predictive_calendar()
        await instance._update_predictive_schedule()
        await instance._update_calendar()
        await instance._update_generic_data()

    async def async_delete_alert(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        index = call.data.get(SERVER_DATA_ALERT_INDEX, DEFAULT_NAME_COMMANDS)
        _LOGGER.info("Deleting alert #%s from mower: %s", index, instance._serial)

        await instance._update_alerts()
        await instance._indego_client.delete_alert(index)
        await instance._update_alerts(force_alert_state=True)

    async def async_delete_alert_all(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        _LOGGER.info("Deleting all alerts from mower: %s", instance._serial)

        max_rounds = 30

        for round_num in range(1, max_rounds + 1):
            await instance._update_alerts()

            loaded_alerts = len(instance._indego_client.alerts or [])
            total_alerts = getattr(instance._indego_client, "alerts_count", loaded_alerts)

            _LOGGER.info(
                "Delete-all round %d/%d for mower %s: loaded=%d total=%s",
                round_num,
                max_rounds,
                instance._serial,
                loaded_alerts,
                total_alerts,
            )

            if loaded_alerts == 0 and total_alerts == 0:
                _LOGGER.info("All alerts deleted for mower: %s", instance._serial)
                break

            if loaded_alerts == 0:
                _LOGGER.warning(
                    "Alert count is %s but no alerts are loaded for mower %s; stopping delete loop",
                    total_alerts,
                    instance._serial,
                )
                break

            await instance._indego_client.delete_all_alerts()
            await asyncio.sleep(5)

        await instance._update_alerts(force_alert_state=True)

    async def async_read_alert(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        index = call.data.get(SERVER_DATA_ALERT_INDEX, DEFAULT_NAME_COMMANDS)
        _LOGGER.info("Marking alert #%s as read on mower: %s", index, instance._serial)

        await instance._update_alerts()
        await instance._indego_client.put_alert_read(index)
        await instance._update_alerts(force_alert_state=True)

    async def async_read_alert_all(call):
        """Handle the service call."""
        instance = find_instance_for_mower_service_call(call)
        _LOGGER.info("Marking all alerts as read on mower: %s", instance._serial)

        await instance._update_alerts()
        await instance._indego_client.put_all_alerts_read()
        await instance._update_alerts(force_alert_state=True)

    async def async_download_map(call):
        """Handle the download_map service call."""
        instance = find_instance_for_mower_service_call(call)
        _LOGGER.info("Downloading lawn map for mower: %s", instance._serial)
        await instance.download_and_store_map()

    async def async_set_calendar_slot(call):
        """Handle set_calendar_slot service call."""
        instance = find_instance_for_mower_service_call(call)

        days = call.data[CONF_DAYS]
        slot = call.data[CONF_SLOT]
        enabled = call.data[CONF_ENABLED]
        start = call.data.get(CONF_START)
        end = call.data.get(CONF_END)

        await instance.async_set_calendar_slot(
            days=days,
            slot=slot,
            enabled=enabled,
            start=start,
            end=end,
        )

    async def async_set_predictive_mowing_window(call):
        """Handle set_predictive_mowing_window service call."""
        instance = find_instance_for_mower_service_call(call)

        await instance.async_set_predictive_mowing_window(
            earliest_start=call.data[CONF_EARLIEST_START],
            latest_end=call.data[CONF_LATEST_END],
        )

    async def async_set_bump_sensitivity(call):
        """Handle set_bump_sensitivity service call."""
        instance = find_instance_for_mower_service_call(call)

        await instance.async_set_bump_sensitivity(
            _bump_sensitivity_value(call.data[CONF_BUMP_SENSITIVITY])
        )

    async def async_set_pin(call):
        """Handle set_pin service call."""
        instance = find_instance_for_mower_service_call(call)

        pin = str(call.data[CONF_PIN])

        if not pin.isdigit() or len(pin) != 4:
            raise HomeAssistantError(
                "PIN must consist of exactly 4 digits"
            )

        await instance.async_set_pin(pin)

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
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_SET_CALENDAR_SLOT,
            async_set_calendar_slot,
            schema=SERVICE_SCHEMA_SET_CALENDAR_SLOT,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_SET_PREDICTIVE_MOWING_WINDOW,
            async_set_predictive_mowing_window,
            schema=SERVICE_SCHEMA_SET_PREDICTIVE_MOWING_WINDOW,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_SET_BUMP_SENSITIVITY,
            async_set_bump_sensitivity,
            schema=SERVICE_SCHEMA_SET_BUMP_SENSITIVITY,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_NAME_SET_PIN,
            async_set_pin,
            schema=SERVICE_SCHEMA_SET_PIN,
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
        513: 60,
        518: 70,
        521: 70,
        523: 120,
        524: 120,
        768: 120,
        769: 120,
        770: 120,
        771: 120,
        772: 120,
        773: 120,
        774: 120,
        775: 120,
        776: 120,
    }

    STUCK_IGNORED_STATES = {
        266,  # Leaving Dock
        514,  # Relocalising
        515,  # Loading map
        516,  # Learning lawn / calibrating-like
        517,  # Paused (intentional stand-still)
        519,  # Idle in lawn (intentional stand-still)
        520,  # Mapping paused
        525,  # Spot mowing complete
        526,  # Random mowing complete (Pendant zu 525, fehlte bisher)
    }

    # Grace period after mowing session starts (in seconds)
    MOWING_SESSION_GRACE_PERIOD = 90

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
        self._empty_alert_refresh_count = 0
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
        self._forced_mowing_mode = None # force mowing mode and calendar sensors to update

        async def async_token_refresh() -> str:
            """Ensure OAuth token is valid."""
        
            try:
                await session.async_ensure_token_valid()
        
            except OAuth2TokenRequestReauthError as exc:
                raise ConfigEntryAuthFailed(
                    "Bosch OAuth refresh token is no longer valid"
                ) from exc
        
            except OAuth2TokenRequestTransientError:
                raise
        
            return session.token["access_token"]

        self._indego_client = IndegoAsyncClient(
            token=session.token["access_token"],
            token_refresh_method=async_token_refresh,
            serial=self._serial,
            session=async_get_clientsession(hass),
            raise_request_exceptions=True
        )
        self._indego_client.set_default_header(HTTP_HEADER_USER_AGENT, user_agent)

    def entity_enabled(self, key: str | list[str]) -> bool:
        keys = [key] if isinstance(key, str) else key

        return any(
            k in self.entities and self.entities[k].enabled
            for k in keys
        )

    async def async_set_calendar_slot(
        self,
        days: list[str],
        slot: int,
        enabled: bool,
        start: str | None = None,
        end: str | None = None,
    ):
        """Set one manual calendar slot."""
        _LOGGER.info(
            "Setting calendar slot: days=%s slot=%s enabled=%s start=%s end=%s mower=%s",
            days,
            slot,
            enabled,
            start,
            end,
            self._serial,
        )

        if enabled:
            if not start or not end:
                raise HomeAssistantError(
                    "start and end are required when enabled is true"
                )

            try:
                _parse_slot_time(start)
                _parse_slot_time(end)
            except ValueError as err:
                _LOGGER.error("Invalid time format for slot: %s", err)
                raise HomeAssistantError(f"Invalid time format: {err}") from err

        await self._indego_client.update_calendar()
        calendar = getattr(self._indego_client, "calendar", None)

        payload = _calendar_to_payload(calendar, selected_cal=2)

        for day in days:
            payload = _set_payload_slot(payload, day, slot, enabled, start, end)

        await self._indego_client.put(
            f"alms/{self._serial}/calendar",
            payload,
        )

        await self._update_calendar()
        await self._update_next_mow()

    async def async_select_manual_calendar(self):
        """Try to select the manual calendar after SmartMowing was disabled."""
        await self._indego_client.update_calendar()
        calendar = getattr(self._indego_client, "calendar", None)

        payload = _calendar_to_payload(calendar, selected_cal=2)

        result = await self._indego_client.put(
            f"alms/{self._serial}/calendar",
            payload,
        )

    async def async_set_predictive_mowing_window(
        self,
        earliest_start: str,
        latest_end: str,
    ):
        """Set SmartMowing allowed mowing window."""
        _LOGGER.info(
            "Setting predictive mowing window: earliest_start=%s latest_end=%s mower=%s",
            earliest_start,
            latest_end,
            self._serial,
        )

        payload = _predictive_calendar_payload(earliest_start, latest_end)

        result = await self._indego_client.put_predictive_cal(payload)

        _LOGGER.debug("Set predictive mowing window result: %r", result)

        await self._update_predictive_calendar()

    async def _update_predictive_schedule(self):
        """Update SmartMowing predictive schedule."""

        if not self.entity_enabled(ENTITY_PREDICTIVE_SCHEDULE):
            _LOGGER.debug("Predictive schedule entity disabled, NOT updating predictive schedule from Bosch API")
            return None

        _LOGGER.debug("Fetching predictive schedule from Bosch API")

        try:
            await self._indego_client.update_predictive_schedule()
        except Exception as exc:
            _LOGGER.warning("Failed to fetch predictive schedule data: %s", exc)

            if ENTITY_PREDICTIVE_SCHEDULE in self.entities:
                sensor = self.entities[ENTITY_PREDICTIVE_SCHEDULE]
                sensor.state = "not_scheduled"
                sensor.set_attributes(
                    {
                        "last_updated": last_updated_now(),
                        **_predictive_schedule_attributes(None, self._hass),
                    }
                )

            return None

        schedule = getattr(self._indego_client, "predictive_schedule", None)
        attrs = _predictive_schedule_attributes(schedule, self._hass)
        sensor = self.entities[ENTITY_PREDICTIVE_SCHEDULE]

        if not _is_smartmowing_active(
            self._indego_client.generic_data,
            self._forced_mowing_mode,
        ):
            sensor.state = "manual_calendar_active"
        else:
            sensor.state = attrs["next_mow_slot"]

        sensor.set_attributes(
            {
                "last_updated": last_updated_now(),
                **attrs,
            }
        )

    async def _update_network(self):
        """Update mower network data."""

        if not self.entity_enabled([
            ENTITY_NETWORK_SIGNAL,
            ENTITY_NETWORK_OPERATOR,
            ENTITY_NETWORK_MODE
        ]):
            _LOGGER.debug("No network entities enabled, NOT updating network data from Bosch API")
            return None

        _LOGGER.debug("Fetching network data from Bosch API")

        try:
            network = await self._indego_client.get(
                f"alms/{self._serial}/network"
            )
        except Exception as exc:
            _LOGGER.warning("Failed to fetch network data: %s", exc)
            return None

        if ENTITY_NETWORK_SIGNAL in self.entities:
            self.entities[ENTITY_NETWORK_SIGNAL].state = network.get("rssi")
            self.entities[ENTITY_NETWORK_SIGNAL].set_attributes(
                {
                    "last_updated": last_updated_now(),
                    "steered_rssi": network.get("steeredRssi"),
                }
            )

        if ENTITY_NETWORK_OPERATOR in self.entities:
            operator_name = NETWORK_OPERATORS.get(
                (network.get("mcc"), network.get("mnc")),
                f"{network.get('mcc')}-{network.get('mnc')}",
            )
            self.entities[ENTITY_NETWORK_OPERATOR].state = operator_name

            self.entities[ENTITY_NETWORK_OPERATOR].set_attributes(
                {
                    "last_updated": last_updated_now(),
                    "mcc": network.get("mcc"),
                    "mnc": network.get("mnc"),
                    "available_networks": [
                        _network_operator_name(item)
                        for item in network.get("networks", [])
                    ],
                    "available_network_codes": network.get("networks"),
                    "network_count": network.get("networkCount"),
                }
            )

        if ENTITY_NETWORK_MODE in self.entities:
            self.entities[ENTITY_NETWORK_MODE].state = network.get("currMode")
            self.entities[ENTITY_NETWORK_MODE].set_attributes(
                {
                    "last_updated": last_updated_now(),
                    "configured_mode": network.get("configMode"),
                    "rat": network.get("rat"),
                }
            )

        return network

    async def _update_config(self):
        """Update mower config data."""

        if not self.entity_enabled(ENTITY_BUMP_SENSITIVITY):
            _LOGGER.debug("No config entities enabled, NOT updating config data from Bosch API")
            return None

        _LOGGER.debug("Fetching config data from Bosch API")

        try:
            config = await self._indego_client.get(
                f"alms/{self._serial}/config"
            )
        except Exception as exc:
            _LOGGER.warning("Failed to fetch config data from API: %s", exc)
            return None

        value = _get_config_value(
            config,
            "bump_sensitivity",
            "bumpSensitivity",
            "bump_sens",
            "bumpSens",
        )

        self.entities[ENTITY_BUMP_SENSITIVITY].state = (
            _bump_sensitivity_state(value)
            if value is not None
            else STATE_UNKNOWN
        )

        self.entities[ENTITY_BUMP_SENSITIVITY].set_attributes(
            {
                "last_updated": last_updated_now(),
            }
        )

        self.entities[ENTITY_BUMP_SENSITIVITY].async_schedule_update_ha_state()

        return config

    async def async_set_bump_sensitivity(self, bump_sensitivity: int):
        """Set mower bump sensitivity."""
        _LOGGER.info(
            "Setting bump sensitivity to %s for mower %s",
            bump_sensitivity,
            self._serial,
        )

        try:
            config = await self._indego_client.get(
                f"alms/{self._serial}/config"
            )
        except Exception as exc:
            raise HomeAssistantError(
                f"Could not fetch mower config: {exc}"
            ) from exc

        payload = {
            "bump_sensitivity": bump_sensitivity,
        }

        result = await self._indego_client.put(
            f"alms/{self._serial}/config",
            payload,
        )

        if ENTITY_BUMP_SENSITIVITY in self.entities:
            self.entities[ENTITY_BUMP_SENSITIVITY].state = (
                _bump_sensitivity_state(bump_sensitivity)
            )
            self.entities[ENTITY_BUMP_SENSITIVITY].set_attributes(
                {
                    "last_updated": last_updated_now(),
                }
            )

        _LOGGER.debug("Set bump sensitivity result: %r", result)

        await self._update_config()

    async def async_set_pin(self, pin: str):
        """Set mower PIN."""
        pin = str(pin)

        if not pin.isdigit() or len(pin) != 4:
            raise HomeAssistantError(
                "PIN must consist of exactly 4 digits"
            )

        if str(getattr(self._indego_client, "state_description", "")).lower() != "docked":
            raise HomeAssistantError(
                "PIN can only be changed while the mower is docked"
            )

        payload = {
            "new_pin": pin,
        }

        result = await self._indego_client.put(
            f"alms/{self._serial}/security",
            payload,
        )

        _LOGGER.debug("Set PIN result: %r", result)

        await self._update_security()

    async def _update_security(self):
        """Update mower security data."""

        if not self.entity_enabled([
            ENTITY_SECURITY_ENABLED,
            ENTITY_AUTOLOCK,
        ]):
            _LOGGER.debug("No security entities enabled, NOT updating security data from Bosch API")
            return None

        _LOGGER.debug("Fetching security data from Bosch API")

        try:
            security = await self._indego_client.get(
                f"alms/{self._serial}/security"
            )
        except Exception as exc:
            _LOGGER.warning("Failed to fetch security data from API: %s", exc)
            return None

        if ENTITY_SECURITY_ENABLED in self.entities:
            self.entities[ENTITY_SECURITY_ENABLED].is_on = bool(security.get("enabled"))

        if ENTITY_AUTOLOCK in self.entities:
            self.entities[ENTITY_AUTOLOCK].is_on = bool(security.get("autolock"))

        return security

    async def async_set_security_enabled(self, enabled: bool):
        payload = {
            "enabled": enabled,
        }

        result = await self._indego_client.put(
            f"alms/{self._serial}/security",
            payload,
        )

        _LOGGER.debug("Set security enabled result: %r", result)

        await self._update_security()

    async def async_set_autolock(self, enabled: bool):
        if str(self._indego_client.state_description).lower() != "docked":
            raise HomeAssistantError(
                "AutoLock can only be changed while the mower is docked"
            )

        payload = {
            "autolock": enabled,
        }

        result = await self._indego_client.put(
            f"alms/{self._serial}/security",
            payload,
        )

        _LOGGER.debug("Set AutoLock result: %r", result)

        await self._update_security()

    async def _update_automatic_update(self):
        if not self.entity_enabled(ENTITY_AUTOMATIC_UPDATE):
            _LOGGER.debug("No automatic update entities enabled, NOT updating automatic update data from Bosch API")
            return None

        _LOGGER.debug("Fetching automatic update data from Bosch API")

        try:
            automatic_update = await self._indego_client.get(
                f"alms/{self._serial}/automaticUpdate"
            )
        except Exception as exc:
            _LOGGER.warning("Failed to fetch automatic update data: %s", exc)
            return None
    
        self.entities[ENTITY_AUTOMATIC_UPDATE].is_on = bool(
            automatic_update.get("allow_automatic_update")
        )

        return automatic_update

    async def async_set_automatic_update(self, enabled: bool):
        """Set automatic firmware update."""
        payload = {
            "allow_automatic_update": enabled,
        }

        result = await self._indego_client.put(
            f"alms/{self._serial}/automaticUpdate",
            payload,
        )

        _LOGGER.debug("Set automatic update result: %r", result)

        if ENTITY_AUTOMATIC_UPDATE in self.entities:
            self.entities[ENTITY_AUTOMATIC_UPDATE].is_on = enabled

        await self._update_automatic_update()

    async def _update_predictive_setup(self):
        """Update SmartMowing setup data."""

        if not self.entity_enabled(ENTITY_PREDICTIVE_SETUP):
            _LOGGER.debug("Predictive setup entity disabled, NOT updating predictive setup from Bosch API")
            return None

        try:
            setup = await self._indego_client.get(
                f"alms/{self._serial}/predictive/setup"
            )
        except Exception as exc:
            _LOGGER.warning("Failed to fetch predictive setup data: %s", exc)
            return None

        garden_location = setup.get("garden_location", {}) or {}

        self.entities[ENTITY_PREDICTIVE_SETUP].state = "configured"
        self.entities[ENTITY_PREDICTIVE_SETUP].set_attributes(
            {
                "last_updated": last_updated_now(),
                "mowing_duration": setup.get("mowing_duration"),
                "full_cuts": setup.get("full_cuts"),
                "avoid_rain": setup.get("avoid_rain"),
                "avoid_temperature": setup.get("avoid_temperature"),
                "use_grass_growth": setup.get("use_grass_growth"),
                "rain_factor": setup.get("rain_factor"),
                "temperature_factor": setup.get("temperature_factor"),
                "garden_latitude": garden_location.get("latitude"),
                "garden_longitude": garden_location.get("longitude"),
                "garden_timezone": garden_location.get("timezone"),
                "garden_name": garden_location.get("name"),
                "garden_country": garden_location.get("country"),
            }
        )

        return setup

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
                        None,
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

            elif entity[CONF_TYPE] == WEATHER_TYPE:
                self.entities[entity_key] = IndegoWeather(
                    entity_id=f"indego_{self._serial}_{entity_key}",
                    name=None,
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

        await self.start_periodic_position_update()

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

        # Restore session count from persisted entity state
        if ENTITY_SESSION_COUNT in self.entities:
            entity = self.entities[ENTITY_SESSION_COUNT]
            restored_state = entity.state
            if restored_state is not None:
                try:
                    self._session_count = int(float(restored_state))
                    _LOGGER.debug("Restored session count: %d", self._session_count)
                except (ValueError, TypeError):
                    pass

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
                self._update_predictive_calendar(),
                self._update_predictive_schedule(),
                self._update_calendar(),
                self._update_network(),
                self._update_config(),
                self._update_security(),
                self._update_automatic_update(),
                self._update_predictive_weather(),
                self._update_predictive_setup()
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

    async def _update_predictive_calendar(self):
        """Update predictive calendar data / SmartMowing allowed mowing window."""

        if not self.entity_enabled(ENTITY_PREDICTIVE_CALENDAR_SLOTS):
            _LOGGER.debug("Predictive calendar entity disabled, NOT updating predictive calendar from Bosch API")
            return

        _LOGGER.debug("Fetching predictive calendar from Bosch API")

        try:
            await self._indego_client.update_predictive_calendar()
        except Exception as exc:
            _LOGGER.warning("Failed to fetch predictive calendar data: %s", exc)
            return

        calendar = getattr(self._indego_client, "predictive_calendar", None)

        mowing_mode = getattr(
            self._indego_client.generic_data,
            "mowing_mode_description",
            None,
        )

        smartmowing_enabled = _is_smartmowing_active(
            self._indego_client.generic_data,
            self._forced_mowing_mode,
        )

        window = _predictive_calendar_window(calendar, self._hass)

        sensor = self.entities[ENTITY_PREDICTIVE_CALENDAR_SLOTS]

        if not _is_smartmowing_active(
            self._indego_client.generic_data,
            self._forced_mowing_mode,
        ):
            sensor.state = "manual_calendar_active"
        elif window["allowed_mowing_time"] != "not_enabled":
            sensor.state = window["allowed_mowing_time"]
        else:
            sensor.state = "off"

        sensor.set_attributes(
            {
                "last_updated": last_updated_now(),
                "smartmowing_enabled": smartmowing_enabled,
                "mowing_mode": self._forced_mowing_mode or mowing_mode,
                **window,
            }
        )

    async def _update_predictive_weather(self):
        if not self.entity_enabled(ENTITY_PREDICTIVE_WEATHER):
            _LOGGER.debug("Predictive weather entity disabled, NOT updating predictive weather from Bosch API")
            return None

        _LOGGER.debug("Fetching predictive weather from Bosch API")

        try:
            weather = await self._indego_client.get(
                f"alms/{self._serial}/predictive/weather"
            )
        except Exception as exc:
            _LOGGER.warning("Failed to fetch predictive weather data: %s", exc)
            return None
    
        self._predictive_weather = weather
        self.entities[ENTITY_PREDICTIVE_WEATHER].weather_data = weather
        return weather

    async def _update_calendar(self):
        """Update calendar data / planned mowing slots."""

        if not self.entity_enabled(ENTITY_CALENDAR_SLOTS):
            _LOGGER.debug("Calendar entity disabled, NOT updating calendar from Bosch API")
            return None

        _LOGGER.debug("Fetching calendar from Bosch API")

        try:
            await self._indego_client.update_calendar()
        except Exception as exc:
            _LOGGER.warning("Failed to fetch calendar data: %s", exc)
            return None

        calendar = getattr(self._indego_client, "calendar", None)

        slots_by_day = _calendar_slots_by_day(calendar)
        today_name = _today_calendar_day_name()
        today_slots = _today_calendar_slots(slots_by_day)

        sensor = self.entities[ENTITY_CALENDAR_SLOTS]

        if _is_smartmowing_active(
            self._indego_client.generic_data,
            self._forced_mowing_mode,
        ):
            sensor.state = "smartmowing_active"

        elif today_slots:
            sensor.state = ", ".join(today_slots)

        elif _is_calendar_selection_required(self._indego_client.generic_data):
            sensor.state = "calendar_selection_required"

        else:
            sensor.state = "off"

        sensor.set_attributes(
            {
                "last_updated": last_updated_now(),
                "today_slot_1": slots_by_day.get(f"{today_name}_slot_1"),
                "today_slot_2": slots_by_day.get(f"{today_name}_slot_2"),
                **slots_by_day,
            }
        )

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


            # Update battery charging state - use separate binary sensor only
            try:
                is_charging = (self._indego_client.state_description_detail == "Charging")
                # Update battery charging binary sensor
                if ENTITY_BATTERY_CHARGING in self.entities:
                    self.entities[ENTITY_BATTERY_CHARGING].state = is_charging
                # Note: ENTITY_BATTERY does NOT have a 'charging' attribute; only use binary sensor
            except Exception as exc:
                _LOGGER.error("Failed to update battery charging state: %s", str(exc))
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
                    stuck_detection_allowed = current_state_code not in self.STUCK_IGNORED_STATES
                    is_mowing = stuck_detection_allowed and (
                        500 <= current_state_code <= 799
                        or current_state_code in {768, 769, 770, 771, 772, 773, 774, 775, 776}
                    )
                    now = datetime.now()

                    if not stuck_detection_allowed:
                        _LOGGER.debug(
                            "Stuck detection: state=%s detail=%s allowed=%s",
                            current_state_code,
                            self._indego_client.state_description_detail,
                            stuck_detection_allowed,
                        )

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
                mowing_mode = getattr(
                    self._indego_client.generic_data,
                    "mowing_mode_description",
                    STATE_UNKNOWN,

                )

                effective_mowing_mode = self._forced_mowing_mode or mowing_mode

                if ENTITY_MOWING_MODE in self.entities:
                    self.entities[ENTITY_MOWING_MODE].state = effective_mowing_mode
                    _LOGGER.debug("Mowing mode: %s", mowing_mode)

                if ENTITY_SMARTMOWING_SWITCH in self.entities:
                    self.entities[ENTITY_SMARTMOWING_SWITCH].is_on = (
                        str(effective_mowing_mode).lower() == "smartmowing"
                    )

            else:
                _LOGGER.debug("Generic data is empty from API")

                if ENTITY_MOWING_MODE in self.entities:
                    self.entities[ENTITY_MOWING_MODE].state = STATE_UNKNOWN

                if ENTITY_SMARTMOWING_SWITCH in self.entities:
                    self.entities[ENTITY_SMARTMOWING_SWITCH].is_on = False

        except Exception as exc:
            _LOGGER.error("Error processing generic data: %s", str(exc))

            if ENTITY_MOWING_MODE in self.entities:
                self.entities[ENTITY_MOWING_MODE].state = STATE_UNKNOWN

            if ENTITY_SMARTMOWING_SWITCH in self.entities:
                self.entities[ENTITY_SMARTMOWING_SWITCH].is_on = False

        try:
            if ENTITY_PREDICTIVE_CALENDAR_SLOTS in self.entities:
                await self._update_predictive_calendar()
        except Exception as exc:
            _LOGGER.debug(
                "Could not refresh predictive calendar after generic data update: %s",
                exc,
            )


        return self._indego_client.generic_data

    async def _update_alerts(self, force_alert_state: bool = False):

        await self._indego_client.update_alerts()

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

        self._update_alert_state(force=force_alert_state)

    def _update_alert_state(self, force: bool = False):
        """Update alert state based on unread alerts."""
        if ENTITY_ALERT not in self.entities:
            return
    
        alerts = self._indego_client.alerts or []
    
        has_unread_alerts = any(
            str(alert.read_status).strip().lower() == "unread"
            for alert in alerts
        )
    
        if has_unread_alerts:
            # At least one unread alert exists.
            self._empty_alert_refresh_count = 0
            self.entities[ENTITY_ALERT].state = True
            return
    
        if alerts:
            # Alerts exist, but all of them have been read.
            self._empty_alert_refresh_count = 0
            self.entities[ENTITY_ALERT].state = False
            return
    
        if force:
            # An explicit read/delete operation was performed.
            # Accept the empty alert list immediately.
            self._empty_alert_refresh_count = 0
            self.entities[ENTITY_ALERT].state = False
            return
    
        # Bosch may occasionally return an empty alert list during
        # periodic refreshes. Require two consecutive empty responses
        # before clearing the problem state.
        self._empty_alert_refresh_count += 1
    
        if self._empty_alert_refresh_count >= 2:
            self.entities[ENTITY_ALERT].state = False

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

                # Log mower error message
                _LOGGER.info(
                    "Mower %s: %s (Code: %s)",
                    error_severity.name.lower(),
                    error_description,
                    error_code,
                )
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
