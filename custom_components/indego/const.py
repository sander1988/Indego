"""Constants for Indego integration."""
from typing import Final

DOMAIN: Final = "indego"

OAUTH2_AUTHORIZE: Final = "https://prodindego.b2clogin.com/prodindego.onmicrosoft.com/b2c_1a_signup_signin/oauth2/v2.0/authorize"
OAUTH2_TOKEN: Final = "https://prodindego.b2clogin.com/prodindego.onmicrosoft.com/b2c_1a_signup_signin/oauth2/v2.0/token"
OAUTH2_CLIENT_ID: Final = "65bb8c9d-1070-4fb4-aa95-853618acc876"

STATUS_UPDATE_FAILURE_DELAY_TIME: Final = [0, 10, 30, 60]
ONLINE_TIMEOUT_SECONDS: Final = 300  # 5 minutes - mark mower as offline if no successful API response

DATA_UPDATED: Final = f"{DOMAIN}_data_updated"

CONF_MOWER_SERIAL: Final = "mower_serial"
CONF_MOWER_NAME: Final = "mower_name"
CONF_MOWER_ENTITY: Final = "mower_entity"
CONF_EXPOSE_INDEGO_AS_MOWER: Final = "expose_mower"
CONF_EXPOSE_INDEGO_AS_VACUUM: Final = "expose_vacuum"
CONF_SHOW_ALL_ALERTS: Final = "show_all_alerts"
CONF_USER_AGENT: Final = "user_agent"
CONF_SERVICES_REGISTERED: Final = "services_registered"

CONF_TRANSLATION_KEY: Final = "translation_key"
CONF_ATTR: Final = "attributes"
CONF_STATE_CLASS: Final = "state_class"
CONF_SEND_COMMAND: Final = "command"
CONF_SMARTMOWING: Final = "enable"
CONF_POLLING: Final = "polling"
CONF_ENABLED_BY_DEFAULT: Final = "enabled_by_default"
CONF_ENTITY_CATEGORY: Final = "entity_category"

CONF_DAYS: Final = "days"
CONF_SLOT: Final = "slot"
CONF_ENABLED: Final = "enabled"
CONF_START: Final = "start"
CONF_END: Final = "end"
CONF_EARLIEST_START: Final = "earliest_start"
CONF_LATEST_END: Final = "latest_end"

CONF_SERVICE: Final = "service"
CONF_SERVICE_DATA: Final = "service_data"

DEFAULT_NAME: Final = "Indego"
DEFAULT_NAME_COMMANDS: Final = None

SERVICE_NAME_COMMAND: Final = "command"
SERVICE_NAME_SMARTMOW: Final = "smartmowing"
SERVICE_NAME_DELETE_ALERT: Final = "delete_alert"
SERVICE_NAME_READ_ALERT: Final = "read_alert"
SERVICE_NAME_DELETE_ALERT_ALL: Final = "delete_alert_all"
SERVICE_NAME_READ_ALERT_ALL: Final = "read_alert_all"
SERVICE_NAME_DOWNLOAD_MAP: Final = "download_map"
SERVER_DATA_ALERT_INDEX: Final = "alert_index"

CAMERA_TYPE: Final = "camera"
SENSOR_TYPE: Final = "sensor"
BINARY_SENSOR_TYPE: Final = "binary_sensor"
VACUUM_TYPE: Final = "vacuum"
LAWN_MOWER_TYPE: Final = "lawn_mower"
BUTTON_TYPE: Final = "button"
SWITCH_TYPE: Final = "switch"
WEATHER_TYPE: Final = "weather"
INDEGO_PLATFORMS: Final = [SENSOR_TYPE, BINARY_SENSOR_TYPE, VACUUM_TYPE, LAWN_MOWER_TYPE, CAMERA_TYPE, BUTTON_TYPE, SWITCH_TYPE, WEATHER_TYPE]
ENTITY_ONLINE: Final = "online"
ENTITY_UPDATE_AVAILABLE: Final = "update_available"
ENTITY_ALERT: Final = "alert"
ENTITY_MOWER_STATE: Final = "mower_state"
ENTITY_MOWER_STATE_DETAIL: Final = "mower_state_detail"
ENTITY_BATTERY: Final = "battery_percentage"
ENTITY_LAWN_MOWED: Final = "lawn_mowed"
ENTITY_LAWN_MOWED_SIZE: Final = "lawn_mowed_size"
ENTITY_LAST_COMPLETED: Final = "last_completed"
ENTITY_NEXT_MOW: Final = "next_mow"
ENTITY_MOWING_MODE: Final = "mowing_mode"
ENTITY_RUNTIME: Final = "runtime_total"
ENTITY_VACUUM: Final = "vacuum"
ENTITY_LAWN_MOWER: Final = "lawn_mower"
ENTITY_GARDEN_SIZE: Final = "garden_size"
ENTITY_CAMERA: Final = "camera"
ENTITY_MOWER_SVG_X: Final = "mower_svg_x"
ENTITY_MOWER_SVG_Y: Final = "mower_svg_y"
ENTITY_MOWER_STUCK: Final = "mower_stuck"
ENTITY_LAST_ERROR_CODE: Final = "last_error_code"
ENTITY_FIRMWARE_VERSION: Final = "firmware_version"
ENTITY_MAINTENANCE_HOURS: Final = "maintenance_hours"
ENTITY_SESSION_COUNT: Final = "session_count"
ENTITY_BATTERY_VOLTAGE: Final = "battery_voltage"
ENTITY_BATTERY_TEMPERATURE: Final = "battery_temperature"
ENTITY_AMBIENT_TEMPERATURE: Final = "ambient_temperature"
ENTITY_BATTERY_CYCLES: Final = "battery_cycles"
ENTITY_BATTERY_DISCHARGE: Final = "battery_discharge"
ENTITY_BATTERY_CHARGING: Final = "battery_charging"
ENTITY_SERVICE_STATUS: Final = "service_status"
ENTITY_DELETE_ALL_ALERTS_BUTTON: Final = "delete_all_alerts"
ENTITY_DELETE_LAST_ALERT_BUTTON: Final = "delete_last_alert"
ENTITY_READ_ALL_ALERTS_BUTTON: Final = "read_all_alerts"
ENTITY_READ_LAST_ALERT_BUTTON: Final = "read_last_alert"
ENTITY_SMARTMOWING_SWITCH: Final = "smartmowing_switch"
ENTITY_AUTOMATIC_UPDATE: Final = "automatic_update"
ENTITY_PREDICTIVE_WEATHER: Final = "predictive_weather"

# Smart Mowing Sensors (Phase 1)
ENTITY_WEATHER: Final = "weather"
ENTITY_WEATHER_TEMPERATURE: Final = "weather_temperature"
ENTITY_WEATHER_HUMIDITY: Final = "weather_humidity"
ENTITY_WEATHER_FORECAST: Final = "weather_forecast"
ENTITY_WEATHER_WIND: Final = "weather_wind"
ENTITY_LAST_CUTTING: Final = "last_cutting"
ENTITY_GARDEN_LOCATION: Final = "garden_location"
ENTITY_SMARTMOW_ENABLED: Final = "smartmow_enabled"
ENTITY_SMARTMOW_SETUP: Final = "smartmow_setup"
ENTITY_SMARTMOW_SCHEDULE: Final = "smartmow_schedule"
ENTITY_PREDICTIVE_SETUP: Final = "predictive_setup"

# Smart Mowing Services (Phase 2)
SERVICE_NAME_SET_LOCATION: Final = "set_smart_mowing_location"
SERVICE_NAME_CONFIGURE_SETUP: Final = "configure_smart_mowing"
SERVICE_NAME_RESET_SMART_MOWING: Final = "reset_smart_mowing"

# Calendar
ENTITY_PREDICTIVE_CALENDAR_SLOTS: Final = "predictive_calendar_slots"
ENTITY_PREDICTIVE_SCHEDULE: Final = "predictive_schedule"
ENTITY_CALENDAR_SLOTS: Final = "calendar_slots"

# Calendar services
SERVICE_NAME_SET_CALENDAR_SLOT: Final = "set_calendar_slot"
SERVICE_NAME_SET_PREDICTIVE_MOWING_WINDOW: Final = "set_predictive_mowing_window"

# Network
ENTITY_NETWORK_SIGNAL: Final = "network_signal"
ENTITY_NETWORK_OPERATOR: Final = "network_operator"
ENTITY_NETWORK_MODE: Final = "network_mode"
ENTITY_NETWORK_SIGNAL: Final = "network_signal"
ENTITY_NETWORK_OPERATOR: Final = "network_operator"
ENTITY_NETWORK_MODE: Final = "network_mode"

# Bump Sensitivity
ENTITY_BUMP_SENSITIVITY: Final = "bump_sensitivity"
SERVICE_NAME_SET_BUMP_SENSITIVITY: Final = "set_bump_sensitivity"
CONF_BUMP_SENSITIVITY: Final = "bump_sensitivity"
CONF_BUMP_SENSITIVITY_NORMAL: Final = "normal"
CONF_BUMP_SENSITIVITY_SLIPPERY: Final = "slippery"
CONF_BUMP_SENSITIVITY_UNEVEN: Final = "uneven"

# Security
ENTITY_SECURITY_ENABLED: Final = "security_enabled"
ENTITY_AUTOLOCK: Final = "autolock"
SERVICE_NAME_SET_PIN: Final = "set_pin"
CONF_PIN: Final = "pin"

DELETE_ALERTS_BATCH_DELAY_SECONDS: Final = 10
DELETE_ALERTS_BATCH_MAX_ROUNDS: Final = 20
READ_ALERTS_BATCH_DELAY_SECONDS: Final = 10
READ_ALERTS_BATCH_MAX_ROUNDS: Final = 20

HTTP_HEADER_USER_AGENT: Final = "User-Agent"
HTTP_HEADER_USER_AGENT_DEFAULT: Final = "HA/Indego"
HTTP_HEADER_USER_AGENT_DEFAULTS: Final = [
    "HomeAssistant/Indego",
    "HA/Indego"
]
