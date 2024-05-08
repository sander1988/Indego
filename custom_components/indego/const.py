"""Constants for Indego integration."""
from typing import Final

DOMAIN: Final = "indego"

OAUTH2_AUTHORIZE: Final = "https://prodindego.b2clogin.com/prodindego.onmicrosoft.com/b2c_1a_signup_signin/oauth2/v2.0/authorize"
OAUTH2_TOKEN: Final = "https://prodindego.b2clogin.com/prodindego.onmicrosoft.com/b2c_1a_signup_signin/oauth2/v2.0/token"
OAUTH2_CLIENT_ID: Final = "65bb8c9d-1070-4fb4-aa95-853618acc876"

STATUS_UPDATE_FAILURE_DELAY_TIME: Final = 60

DATA_UPDATED: Final = f"{DOMAIN}_data_updated"

CONF_MOWER_SERIAL: Final = "mower_serial"
CONF_MOWER_NAME: Final = "mower_name"
CONF_SERVICES_REGISTERED: Final = "services_registered"

CONF_ATTR: Final = "attributes"
CONF_SEND_COMMAND: Final = "command"
CONF_SMARTMOWING: Final = "enable"
CONF_POLLING: Final = "polling"
CONF_DOWNLAD_MAP: Final = "filename"
CONF_DELETE_ALERT: Final = "alert_index"
CONF_READ_ALERT: Final = "alert_index"


DEFAULT_NAME: Final = "Indego"
DEFAULT_NAME_COMMANDS: Final = None
DEFAULT_MAP_NAME: Final = "mapWithoutIndego"

SERVICE_NAME_COMMAND: Final = "command"
SERVICE_NAME_SMARTMOW: Final = "smartmowing"
SERVICE_NAME_DOWNLOAD_MAP: Final = "download_map"
SERVICE_NAME_DELETE_ALERT: Final = "delete_alert"
SERVICE_NAME_READ_ALERT: Final = "read_alert"
SERVICE_NAME_DELETE_ALERT_ALL: Final = "delete_alert_all"
SERVICE_NAME_READ_ALERT_ALL: Final = "read_alert_all"

SENSOR_TYPE: Final = "sensor"
BINARY_SENSOR_TYPE: Final = "binary_sensor"
VACUUM_TYPE: Final = "vacuum"
INDEGO_PLATFORMS: Final = [SENSOR_TYPE, BINARY_SENSOR_TYPE, VACUUM_TYPE]

ENTITY_ONLINE: Final = "online"
ENTITY_UPDATE_AVAILABLE: Final = "update_available"
ENTITY_ALERT: Final = "alert"
ENTITY_MOWER_ALERT: Final = "mower_alert"
ENTITY_ALERT_COUNT: Final = "alert_count"
ENTITY_ALERT_ID: Final = "alert_id"
ENTITY_ALERT_ERROR_CODE: Final = "alert_errorcode"
ENTITY_ALERT_HEADLINE: Final = "alert_headline"
ENTITY_ALERT_DATE: Final = "alert_date"
ENTITY_ALERT_MESSAGE: Final = "alert_message"
ENTITY_ALERT_READ_STATUS: Final = "alert_read_status"
ENTITY_ALERT_FLAG: Final = "alert_flag"
ENTITY_ALERT_PUSH: Final = "alert_push"
ENTITY_ALERT_DESCRIPTION: Final = "alert_description"
ENTITY_MOWER_STATE: Final = "mower_state"
ENTITY_MOWER_STATE_DETAIL: Final = "mower_state_detail"
ENTITY_BATTERY: Final = "battery_percentage"
ENTITY_LAWN_MOWED: Final = "lawn_mowed"
ENTITY_LAST_COMPLETED: Final = "last_completed"
ENTITY_NEXT_MOW: Final = "next_mow"
ENTITY_MOWING_MODE: Final = "mowing_mode"
ENTITY_RUNTIME: Final = "runtime_total"
ENTITY_MOWER_ALERT: Final = "mower_alert"
ENTITY_VACUUM: Final = "vacuum"
ENTITY_HAS_MAP: Final = "setup_has_map"
ENTITY_MAP_UPDATE_AVAILABLE: Final = "state_map_update_available"
ENTITY_XPOS: Final = "state_x_pos"
ENTITY_YPOS: Final = "state_y_pos"
ENTITY_MAPSVGCACHETS: Final = "state_map_svg_cache_ts"
ENTITY_YSVGPOS: Final = "state_svg_y_pos"
ENTITY_XSVGPOS: Final = "state_svg_x_pos"
