"""
Comprehensive error code mappings for Bosch Indego mowers.

This module provides complete error handling for:
1. Mower State Codes (firmware states)
2. Device/Hardware Error Codes (mower-reported errors) – with severity
3. API Error Codes (operation errors from endpoints)
4. HTTP Error Patterns (composite codes from API responses)

Based on Bosch Indego Connect v4.1.2 Reverse Engineering and Service Manuals.
"""

from enum import Enum
from typing import Optional, Tuple, Dict, Any

# =============================================================================
# MOWER STATE CODES (Firmware States)
# =============================================================================

MOWER_STATE_CODES = {
    # Dock/Charging States (200-299)
    "257": {"name": "IN_DOCK_CHARGING", "display": "Charging", "state": "docked"},
    "258": {"name": "IN_DOCK_DOCKED", "display": "Docked", "state": "docked"},
    "259": {"name": "IN_DOCK_SOFTWARE_UPDATE", "display": "Software update", "state": "docked"},
    "260": {"name": "IN_DOCK_CHARGING2", "display": "Charging", "state": "docked"},
    "261": {"name": "IN_DOCK_DOCKED2", "display": "Docked", "state": "docked"},
    "262": {"name": "IN_DOCK_LOADING_MAP", "display": "Docked – loading map", "state": "docked"},
    "263": {"name": "IN_DOCK_SAVING_MAP", "display": "Docked – saving map", "state": "docked"},
    "266": {"name": "IN_DOCK_LEAVING_DOCK", "display": "Leaving dock", "state": "leaving"},
    "270": {"name": "IN_DOCK_FIRMWARE_DOWNLOAD", "display": "Firmware download", "state": "docked"},
    "271": {"name": "IN_DOCK_FIRMWARE_INSTALL", "display": "Installing firmware", "state": "docked"},

    # Lawn States (512-599)
    "512": {"name": "IN_LAWN_LEAVING_DOCK", "display": "Leaving dock", "state": "leaving"},
    "513": {"name": "IN_LAWN_MOWING", "display": "Mowing", "state": "mowing"},
    "514": {"name": "IN_LAWN_RELOCALISING", "display": "Relocalising", "state": "mowing"},
    "515": {"name": "IN_LAWN_LOADING_MAP", "display": "Loading map", "state": "mowing"},
    "516": {"name": "IN_LAWN_MAPPING", "display": "Learning lawn", "state": "mapping"},
    "517": {"name": "IN_LAWN_PAUSED", "display": "Paused", "state": "paused"},
    "518": {"name": "IN_LAWN_BORDER_CUT", "display": "Border cut", "state": "mowing"},
    "519": {"name": "IN_LAWN_IDLE", "display": "Idle in lawn", "state": "idle"},
    "520": {"name": "IN_LAWN_MAPPING_PAUSED", "display": "Learning lawn (paused)", "state": "mapping_paused"},
    "521": {"name": "IN_LAWN_BORDER_CUTTING", "display": "Border cutting", "state": "mowing"},
    "522": {"name": "IN_LAWN_UNUSED", "display": "Border cutting", "state": "mowing"},  # legacy, kept as is
    "523": {"name": "IN_LAWN_SPOT_MOWING", "display": "Spot mowing", "state": "spot_mowing"},
    "524": {"name": "IN_LAWN_RANDOM_MOWING", "display": "Random mowing", "state": "random_mowing"},
    "525": {"name": "IN_LAWN_SPOT_MOWING_COMPLETE", "display": "Spot mowing complete", "state": "mowing"},
    "526": {"name": "IN_LAWN_RANDOM_MOWING_COMPLETE", "display": "Random mowing complete", "state": "mowing"},
    "528": {"name": "IN_LAWN_SPOT_MOWING_PAUSED", "display": "Spot mowing (paused)", "state": "paused"},
    "529": {"name": "IN_LAWN_RANDOM_MOWING_PAUSED", "display": "Random mowing (paused)", "state": "paused"},
    "530": {"name": "IN_LAWN_ZONE_MOWING", "display": "Zone mowing", "state": "zone_mowing"},
    "531": {"name": "IN_LAWN_ZONE_MOWING_PAUSED", "display": "Zone mowing (paused)", "state": "paused"},

    # Returning to Dock (768-799)
    "768": {"name": "RET_DOCK", "display": "Returning to dock", "state": "returning"},
    "769": {"name": "RET_DOCK_HMI", "display": "Returning to dock", "state": "returning"},
    "770": {"name": "RET_DOCK_BS", "display": "Returning to dock", "state": "returning"},
    "771": {"name": "RET_DOCK_BATTERY_LOW", "display": "Returning to dock – battery low", "state": "returning"},
    "772": {"name": "RET_DOCK_CALENDAR", "display": "Returning to dock – calendar", "state": "returning"},
    "773": {"name": "RET_DOCK_BATTERY_TEMP", "display": "Returning to dock – battery temp", "state": "returning"},
    "774": {"name": "RET_DOCK_APP", "display": "Returning to dock (app triggered)", "state": "returning"},
    "775": {"name": "RET_DOCK_GARDEN_COMPLETE", "display": "Returning to dock – lawn complete", "state": "returning"},
    "776": {"name": "RET_DOCK_RELOCALISING", "display": "Returning to dock – relocalising", "state": "returning"},
    "777": {"name": "RET_DOCK_ZONE_CHANGE", "display": "Returning to dock – zone change", "state": "returning"},

    # Service/Maintenance (1025+)
    "1025": {"name": "SERVICE_DIAGNOSTIC_MODE", "display": "Diagnostic mode", "state": "maintenance"},
    "1026": {"name": "SERVICE_EOL_MODE", "display": "EOL mode", "state": "maintenance"},
    "1027": {"name": "SERVICE_REQUESTING_STATUS", "display": "Getting status", "state": "unknown"},
    "1281": {"name": "SW_UPDATE_MODE", "display": "Firmware update", "state": "updating"},
    "1537": {"name": "LOW_POWER_MODE", "display": "Low power mode", "state": "low_power"},
    "1792": {"name": "LEAVING_DOCK", "display": "Leaving dock", "state": "leaving"},

    # Synthetic States (app-side only)
    "0": {"name": "GETTING_STATUS", "display": "Getting status", "state": "unknown"},
    "1": {"name": "OFFLINE", "display": "Offline", "state": "offline"},
    "2": {"name": "UNPAIRED", "display": "No mower paired", "state": "unpaired"},
    "3": {"name": "NOT_MAPPED", "display": "Mower not mapped", "state": "not_mapped"},
    "4": {"name": "NO_PIN", "display": "PIN not set", "state": "no_pin"},
    "5": {"name": "DISABLED", "display": "Mower disabled", "state": "disabled"},
    "64513": {"name": "WAKING_UP_INDEGO", "display": "Getting status", "state": "unknown"},
    "69420": {"name": "SYNTHETIC_COMMAND_SENT", "display": "Command sent", "state": "unknown"},
}

# =============================================================================
# DEVICE/HARDWARE ERROR CODES (Mower-reported errors) with severity
# =============================================================================

# Severity can be: INFO, WARNING, ERROR, CRITICAL
DEVICE_ERROR_CODES: Dict[str, Dict[str, Any]] = {
    # No error
    "0": {"msg": "No error", "severity": "INFO"},

    # Internal/System errors (40-70)
    "45": {"msg": "Unknown internal error", "severity": "ERROR"},
    "46": {"msg": "Wheel motor overload", "severity": "ERROR"},
    "48": {"msg": "Perimeter wire short circuit", "severity": "ERROR"},
    "49": {"msg": "Perimeter wire broken", "severity": "ERROR"},
    "55": {"msg": "Button cell almost empty", "severity": "WARNING"},
    "57": {"msg": "Compass error", "severity": "ERROR"},
    "58": {"msg": "No data from mobile module", "severity": "ERROR"},
    "60": {"msg": "Mower tilted", "severity": "WARNING"},

    # Wheel/Motor/Sensor errors (100-220)
    "101": {"msg": "Mower was lifted", "severity": "WARNING"},
    "102": {"msg": "Lift sensor right front steering wheel", "severity": "ERROR"},
    "103": {"msg": "Lift sensor left front steering wheel", "severity": "ERROR"},
    "104": {"msg": "Stop button pressed", "severity": "WARNING"},
    "105": {"msg": "Mower tilted >45°", "severity": "ERROR"},
    "106": {"msg": "Invalid input", "severity": "ERROR"},
    "107": {"msg": "System error", "severity": "ERROR"},
    "108": {"msg": "System error", "severity": "ERROR"},
    "109": {"msg": "System error", "severity": "ERROR"},
    "110": {"msg": "Charging station error", "severity": "ERROR"},
    "111": {"msg": "Charging contact error", "severity": "ERROR"},
    "115": {"msg": "Permanent tactile detected", "severity": "WARNING"},
    "126": {"msg": "Charging current/voltage too high", "severity": "ERROR"},
    "127": {"msg": "Charging current/voltage too high", "severity": "ERROR"},
    "128": {"msg": "Cutter motor overload", "severity": "ERROR"},
    "129": {"msg": "Cutter load too high", "severity": "ERROR"},
    "130": {"msg": "Cutter load too high", "severity": "ERROR"},
    "131": {"msg": "Cutter load too high", "severity": "ERROR"},
    "132": {"msg": "Cutter blade blocked", "severity": "ERROR"},
    "133": {"msg": "Internal error", "severity": "ERROR"},
    "134": {"msg": "Internal error", "severity": "ERROR"},
    "135": {"msg": "Wheel drive error", "severity": "ERROR"},
    "136": {"msg": "Left wheel blocked", "severity": "ERROR"},
    "137": {"msg": "Right wheel blocked", "severity": "ERROR"},
    "138": {"msg": "Left wheel motor error", "severity": "ERROR"},
    "139": {"msg": "Right wheel motor error", "severity": "ERROR"},
    "140": {"msg": "Wheel drive temperature too high", "severity": "ERROR"},
    "142": {"msg": "Internal wheel drive error", "severity": "ERROR"},
    "143": {"msg": "Intermittent error", "severity": "WARNING"},
    "144": {"msg": "Internal communication error", "severity": "ERROR"},
    "145": {"msg": "Sensor error", "severity": "ERROR"},

    # Perimeter/Wire errors (149-197)
    "149": {"msg": "Mower out of perimeter limit", "severity": "ERROR"},
    "150": {"msg": "No signal from perimeter wire", "severity": "ERROR"},
    "151": {"msg": "Waiting for loop signal", "severity": "WARNING"},
    "152": {"msg": "Loop signal interference", "severity": "WARNING"},
    "153": {"msg": "Loop signal too weak", "severity": "WARNING"},
    "160": {"msg": "Battery temperature too high", "severity": "WARNING"},
    "161": {"msg": "Battery temperature too low", "severity": "WARNING"},
    "162": {"msg": "Charging error", "severity": "ERROR"},
    "163": {"msg": "Charging error – battery defective", "severity": "ERROR"},
    "164": {"msg": "Charging error – charger defective", "severity": "ERROR"},
    "165": {"msg": "Charging error – connection", "severity": "ERROR"},
    "166": {"msg": "Charging error – timeout", "severity": "ERROR"},
    "170": {"msg": "Battery cell imbalance", "severity": "ERROR"},
    "171": {"msg": "Battery capacity too low", "severity": "WARNING"},
    "172": {"msg": "Battery communication error", "severity": "ERROR"},
    "190": {"msg": "Perimeter wire not connected", "severity": "ERROR"},
    "191": {"msg": "Perimeter wire short", "severity": "ERROR"},
    "192": {"msg": "Perimeter wire broken", "severity": "ERROR"},
    "193": {"msg": "Perimeter wire interference", "severity": "WARNING"},
    "194": {"msg": "No perimeter signal detected", "severity": "ERROR"},
    "195": {"msg": "Loop signal lost", "severity": "ERROR"},
    "196": {"msg": "Loop signal error", "severity": "ERROR"},
    "197": {"msg": "Perimeter wire crossed", "severity": "ERROR"},

    # Drive errors (216)
    "216": {"msg": "Left wheel stuck", "severity": "ERROR"},

    # GPS errors (210-213)
    "210": {"msg": "GPS error", "severity": "ERROR"},
    "211": {"msg": "GPS signal lost", "severity": "ERROR"},
    "212": {"msg": "GPS position error", "severity": "ERROR"},
    "213": {"msg": "GPS module error", "severity": "ERROR"},

    # Sensor errors (220-226)
    "220": {"msg": "Lift sensor error", "severity": "ERROR"},
    "221": {"msg": "Tilt sensor error", "severity": "ERROR"},
    "222": {"msg": "Compass error", "severity": "ERROR"},
    "223": {"msg": "Gyroscope error", "severity": "ERROR"},
    "224": {"msg": "Accelerometer error", "severity": "ERROR"},
    "225": {"msg": "Ultrasonic sensor error", "severity": "ERROR"},
    "226": {"msg": "Rain sensor error", "severity": "WARNING"},

    # Navigation/Stuck errors (700-799)
    "701": {"msg": "Mower stuck", "severity": "ERROR"},
    "702": {"msg": "Mower trapped", "severity": "ERROR"},
    "703": {"msg": "Mower too high", "severity": "WARNING"},
    "704": {"msg": "Unable to proceed", "severity": "ERROR"},
    "705": {"msg": "Uneven ground", "severity": "WARNING"},
    "706": {"msg": "Grass too high", "severity": "WARNING"},

    # Communication errors (800-899)
    "801": {"msg": "Bluetooth error", "severity": "ERROR"},
    "802": {"msg": "WiFi connection lost", "severity": "ERROR"},
    "803": {"msg": "API connection error", "severity": "ERROR"},
    "804": {"msg": "No connection to server", "severity": "ERROR"},
    "805": {"msg": "Communication timeout", "severity": "WARNING"},

    # Firmware/Software errors (900-999)
    "901": {"msg": "Firmware error", "severity": "ERROR"},
    "902": {"msg": "Software error", "severity": "ERROR"},
    "903": {"msg": "Configuration error", "severity": "ERROR"},
    "904": {"msg": "Memory error", "severity": "ERROR"},

    # Battery/System errors (1000+)
    "1000": {"msg": "System error", "severity": "ERROR"},
    "1001": {"msg": "Unknown error", "severity": "ERROR"},
    "1002": {"msg": "Shutdown detected", "severity": "WARNING"},
    "1008": {"msg": "Mower is stuck", "severity": "ERROR"},
    "1108": {"msg": "Inclination angle too large", "severity": "WARNING"},
    "1138": {"msg": "Last run error", "severity": "ERROR"},
    "1146": {"msg": "Orientation filter error", "severity": "ERROR"},
    "1148": {"msg": "On-/Off error. Need PIN code to unlock", "severity": "ERROR"},
    "1156": {"msg": "Unsupported battery pack", "severity": "ERROR"},

    # Special Alert Codes (string-based) – with correct severity
    "ntfy_blade_life": {"msg": "Reminder blade life", "severity": "INFO"},
    "smartMow.mowerUnreachable": {"msg": "SmartMowing disabled", "severity": "WARNING"},
    "firmware.updateComplete": {"msg": "Software update complete", "severity": "INFO"},
    "smartMow.mowerReachable": {"msg": "Mower reachable. SmartMow is now enabled.", "severity": "INFO"},
}

# =============================================================================
# API ERROR CODES (from RE: Suffix format: endpoint_http_status_mower_error)
# =============================================================================

API_ERROR_CODES = {
    # General Protocol Errors (suffix: _1 to _9)
    "_1": {"msg": "Checksum frame error", "severity": "ERROR"},
    "_2": {"msg": "ID not supported", "severity": "ERROR"},
    "_3": {"msg": "Invalid command length", "severity": "ERROR"},
    "_4": {"msg": "Invalid frame length", "severity": "ERROR"},
    "_5": {"msg": "ALM disabled", "severity": "ERROR"},
    "_6": {"msg": "Software update in progress", "severity": "WARNING"},
    "_7": {"msg": "Not supported", "severity": "WARNING"},
    "_8": {"msg": "Invalid item identifier", "severity": "ERROR"},
    "_9": {"msg": "Invalid data value", "severity": "ERROR"},

    # Pairing Errors (suffix: _13312, _18176, _18177)
    "_13312": {"msg": "Invalid pairing data", "severity": "ERROR", "context": "POST /alms/{alm}/pair"},
    "_18176": {"msg": "Pairing rejected by mower", "severity": "ERROR", "context": "POST /alms/{alm}/pair"},
    "_18177": {"msg": "Pairing rejected – language mismatch", "severity": "ERROR", "context": "POST /alms/{alm}/pair"},

    # Mow Errors (suffix: _12288 to _12543, used with PUT /state → mow)
    "_12288": {"msg": "Battery not OK / low temperature – cannot mow", "severity": "ERROR", "context": "PUT /state (mow)"},
    "_12289": {"msg": "Unknown garden – mower not mapped", "severity": "ERROR", "context": "PUT /state (mow)"},
    "_12290": {"msg": "PIN error – follow display instructions", "severity": "ERROR", "context": "PUT /state (mow)"},
    "_12291": {"msg": "Mower is going home – cannot start mowing", "severity": "WARNING", "context": "PUT /state (mow)"},
    "_12292": {"msg": "PIN not set – unable to mow", "severity": "ERROR", "context": "PUT /state (mow)", "user_action": "Set PIN on mower display"},
    "_12293": {"msg": "Manual intervention required", "severity": "ERROR", "context": "PUT /state (mow)"},
    "_12543": {"msg": "Other mow error", "severity": "ERROR", "context": "PUT /state (mow)"},

    # Return to Dock Errors (suffix: _12544 to _12799, used with PUT /state → returntodock)
    "_12544": {"msg": "Mower already docked", "severity": "INFO", "context": "PUT /state (returntodock)"},
    "_12545": {"msg": "Garden error – follow display instructions", "severity": "ERROR", "context": "PUT /state (returntodock)"},
    "_12546": {"msg": "Mower is learning the lawn – cannot return", "severity": "WARNING", "context": "PUT /state (returntodock)"},
    "_12547": {"msg": "Unknown garden – cannot return", "severity": "ERROR", "context": "PUT /state (returntodock)"},
    "_12799": {"msg": "Other dock error", "severity": "ERROR", "context": "PUT /state (returntodock)"},

    # Pause Errors (suffix: _12800 to _12802, used with PUT /state → pause)
    "_12800": {"msg": "Cannot pause – mower not mowing", "severity": "INFO", "context": "PUT /state (pause)"},
    "_12801": {"msg": "Cannot pause – mower learning lawn", "severity": "WARNING", "context": "PUT /state (pause)"},
    "_12802": {"msg": "Cannot pause – battery low", "severity": "WARNING", "context": "PUT /state (pause)"},

    # Map Errors
    "_10497": {"msg": "Battery not OK – cannot create map", "severity": "ERROR", "context": "POST /map"},
    "_10498": {"msg": "Mower not in dock – unable to create map", "severity": "ERROR", "context": "POST /map"},
    "_10499": {"msg": "Map already exists", "severity": "WARNING", "context": "POST /map"},
    "_10500": {"msg": "PIN error – unable to create map", "severity": "ERROR", "context": "POST /map"},
    "_10501": {"msg": "Mower going home – unable to create map", "severity": "WARNING", "context": "POST /map"},
    "_10502": {"msg": "PIN not set – unable to create map", "severity": "ERROR", "context": "POST /map"},
    "_10503": {"msg": "Manual intervention required – follow display", "severity": "ERROR", "context": "POST /map"},
    "_10752": {"msg": "Map not available", "severity": "ERROR", "context": "GET /map"},
    "_10751": {"msg": "Other map error", "severity": "ERROR", "context": "POST /map"},

    # Calendar/Scheduling Errors (suffix: _14080 to _14081)
    "_14080": {"msg": "Invalid calendar data", "severity": "ERROR", "context": "PUT /calendar"},
    "_14081": {"msg": "Unknown garden", "severity": "ERROR", "context": "PUT /calendar"},

    # Map Delete Errors (suffix: _13824 to _13825)
    "_13824": {"msg": "Mower not in dock – cannot delete map", "severity": "ERROR", "context": "DELETE /map"},
    "_13825": {"msg": "No map to delete", "severity": "INFO", "context": "DELETE /map"},

    # Security/PIN Errors (suffix: _16896, _17152 to _17153)
    "_16896": {"msg": "Mower not in dock – cannot change PIN", "severity": "ERROR", "context": "PUT /security"},
    "_17152": {"msg": "Invalid autolock value", "severity": "ERROR", "context": "PUT /security"},
    "_17153": {"msg": "Already locked/unlocked – cannot change autolock", "severity": "INFO", "context": "PUT /security"},
    "_16897": {"msg": "PIN change not allowed", "severity": "ERROR", "context": "PUT /security"},
    "_16898": {"msg": "PIN too short", "severity": "ERROR", "context": "PUT /security"},
    "_17154": {"msg": "Autolock value out of range", "severity": "ERROR", "context": "PUT /security"},

    # Date & Time Errors (suffix: _14336, _14337, _14338)
    "_14336": {"msg": "Invalid date/time value", "severity": "ERROR", "context": "PUT /dateAndTime"},
    "_14337": {"msg": "Invalid timezone", "severity": "ERROR", "context": "PUT /dateAndTime"},
    "_14338": {"msg": "Invalid date format", "severity": "ERROR", "context": "PUT /dateAndTime"},

    # Border Cut Errors (suffix: _15616 to _15619)
    "_15616": {"msg": "Border cut cannot be changed in current state", "severity": "ERROR", "context": "PUT /borderCut"},
    "_15617": {"msg": "Border cut not supported", "severity": "WARNING", "context": "PUT /borderCut"},
    "_15618": {"msg": "Border cut already active", "severity": "INFO", "context": "PUT /borderCut"},
    "_15619": {"msg": "Border cut cancelled", "severity": "INFO", "context": "PUT /borderCut"},

    # Config Errors (suffix: _8, _9 in config context)
    "_config_8": {"msg": "Invalid config ID", "severity": "ERROR", "context": "PUT /config"},
    "_config_9": {"msg": "Invalid config data", "severity": "ERROR", "context": "PUT /config"},
}

# =============================================================================
# HTTP ERROR CODE PATTERNS (Composite: endpoint_http_code_suffix)
# =============================================================================

HTTP_ERROR_PATTERNS = {
    # 400 Bad Request
    "04_400": {"msg": "Invalid email address", "severity": "ERROR", "context": "POST /users"},
    "09_202": {"msg": "Mower disabled – pairing rejected", "severity": "WARNING", "context": "POST /alms/{alm}/pair"},

    # 401 Unauthorized
    "00_401": {"msg": "Wrong credentials – authentication failed", "severity": "ERROR", "context": "POST /authenticate"},
    "01_401": {"msg": "Facebook authentication failed", "severity": "ERROR", "context": "POST /authenticate?facebook"},
    "06_401_password": {"msg": "Wrong current password – profile update failed", "severity": "ERROR", "context": "PUT /users/{id}"},
    "06_401_password_empty": {"msg": "Password not changed", "severity": "WARNING", "context": "PUT /users/{id}"},
    "150_401": {"msg": "Login required – session expired or invalid token", "severity": "ERROR", "context": "Any endpoint"},

    # 403 Forbidden
    "09_403": {"msg": "Pairing forbidden – access denied", "severity": "ERROR", "context": "POST /alms/{alm}/pair"},
    "10_403": {"msg": "Cannot unpair – mower disabled", "severity": "ERROR", "context": "DELETE /alms/{alm}/pair"},

    # 404 Not Found
    "09_404": {"msg": "Mower not found – invalid serial", "severity": "ERROR", "context": "POST /alms/{alm}/pair"},
    "14_404": {"msg": "ALM info not found", "severity": "WARNING", "context": "GET /alms/{alm}/info"},

    # 409 Conflict
    "04_409": {"msg": "Email already in use – account creation failed", "severity": "ERROR", "context": "POST /users"},
    "06_409": {"msg": "Email already in use – profile update failed", "severity": "ERROR", "context": "PUT /users/{id}"},
    "09_409": {"msg": "Mower already paired to account", "severity": "WARNING", "context": "POST /alms/{alm}/pair"},
    "61_409": {"msg": "SmartMowing disabled – cannot enable", "severity": "WARNING", "context": "PUT /predictive"},

    # 500 Internal Server Error (with mower error suffix)
    "16_500": {"msg": "Mower state update failed – see details", "severity": "ERROR", "context": "PUT /state"},
    "17_500": {"msg": "Map retrieval failed – see details", "severity": "ERROR", "context": "GET /map"},
    "18_500": {"msg": "Map creation failed – see details", "severity": "ERROR", "context": "POST /map"},
    "20_500": {"msg": "Calendar update failed – see details", "severity": "ERROR", "context": "PUT /calendar"},
    "22_500": {"msg": "Security update failed – see details", "severity": "ERROR", "context": "PUT /security"},
    "53_500": {"msg": "Map deletion failed – see details", "severity": "ERROR", "context": "DELETE /map"},

    # Specific 500 with mower error suffixes (more precise)
    "16_500_12288": {"msg": "Cannot mow – battery too low or temperature too low", "severity": "ERROR", "context": "PUT /state (mow)"},
    "16_500_12289": {"msg": "Cannot mow – no map available", "severity": "ERROR", "context": "PUT /state (mow)"},
    "16_500_12290": {"msg": "Cannot mow – PIN required", "severity": "ERROR", "context": "PUT /state (mow)"},
    "16_500_12292": {"msg": "Cannot mow – PIN not set", "severity": "ERROR", "context": "PUT /state (mow)"},

    # 500 with Mower Disabled (_5 suffix) – generic catch-all
    "XX_5XX": {"msg": "Mower disabled – operation not available", "severity": "ERROR", "context": "Any endpoint"},

    # Additional specific cases
    "16_202": {"msg": "Mower disabled – command rejected", "severity": "WARNING", "context": "PUT /state"},

    # 504 Gateway Timeout
    "504_timeout": {"msg": "Mower or API not reachable – timeout", "severity": "WARNING", "context": "Any endpoint"},

    # Network/Connectivity
    "0_network": {"msg": "No internet connectivity – cannot reach API", "severity": "ERROR", "context": "Network layer"},
}

# =============================================================================
# ERROR SEVERITY LEVELS
# =============================================================================

class ErrorSeverity(Enum):
    """Error severity classification."""
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_mower_state_info(state_code: str) -> Optional[dict]:
    """Get mower state information.

    Args:
        state_code: State code as string

    Returns:
        Dict with 'name', 'display', 'state' or None
    """
    return MOWER_STATE_CODES.get(str(state_code))

def get_device_error_description(error_code: str) -> str:
    """Get device/hardware error description.

    Args:
        error_code: Error code as string

    Returns:
        Error description string
    """
    entry = DEVICE_ERROR_CODES.get(str(error_code))
    if entry:
        return entry.get("msg", f"Unknown device error: {error_code}")
    return f"Unknown device error: {error_code}"

def get_device_error_severity(error_code: str) -> ErrorSeverity:
    """Get device/hardware error severity.

    Args:
        error_code: Error code as string

    Returns:
        ErrorSeverity enum value
    """
    entry = DEVICE_ERROR_CODES.get(str(error_code))
    if entry:
        severity_str = entry.get("severity", "ERROR")
        severity_map = {
            "INFO": ErrorSeverity.INFO,
            "WARNING": ErrorSeverity.WARNING,
            "ERROR": ErrorSeverity.ERROR,
            "CRITICAL": ErrorSeverity.CRITICAL,
        }
        return severity_map.get(severity_str, ErrorSeverity.ERROR)
    return ErrorSeverity.ERROR

def get_api_error_details(error_suffix: str) -> Optional[dict]:
    """Get API error details from suffix.

    Args:
        error_suffix: Error suffix (e.g., "_12292", "_10752")

    Returns:
        Dict with 'msg', 'severity', 'context' or None
    """
    return API_ERROR_CODES.get(error_suffix)

def get_http_error_pattern(composite_code: str) -> Optional[dict]:
    """Get HTTP error pattern details.

    Args:
        composite_code: Composite error code (e.g., "04_409", "16_500_12288")

    Returns:
        Dict with 'msg', 'severity', 'context' or None
    """
    # Try exact match first
    if composite_code in HTTP_ERROR_PATTERNS:
        return HTTP_ERROR_PATTERNS[composite_code]

    # Check for XX_5XX pattern (mower disabled)
    if "_5" in composite_code and "XX" not in composite_code:
        parts = composite_code.split("_")
        if len(parts) >= 2 and parts[1].startswith("5"):
            return HTTP_ERROR_PATTERNS.get("XX_5XX")

    return None

def parse_composite_error(error_code: str) -> Tuple[Optional[dict], Optional[str]]:
    """Parse composite error code and extract details.

    Handles formats:
    - State Code: "257" (mower state)
    - API Suffix: "_12292" (API error)
    - HTTP Pattern: "09_409" (HTTP conflict)
    - HTTP + Suffix: "16_500_12288" (HTTP 500 with mower error)
    - Simple device error: "104" (device error)

    Args:
        error_code: Error code string

    Returns:
        Tuple of (error_details_dict, error_description_str)
    """
    error_code = str(error_code).strip()

    # 1. Check if it's a mower state code
    state_info = get_mower_state_info(error_code)
    if state_info:
        return (
            {"name": state_info["name"], "display": state_info["display"], "state": state_info["state"]},
            state_info["display"]
        )

    # 2. Check if it's an API suffix (starts with "_")
    if error_code.startswith("_"):
        api_details = get_api_error_details(error_code)
        if api_details:
            return (api_details, api_details["msg"])

    # 3. Check if it's a composite HTTP pattern (contains "_" and at least one digit)
    if "_" in error_code and any(c.isdigit() for c in error_code):
        parts = error_code.split("_")
        # HTTP pattern with suffix (e.g., "16_500_12288")
        if len(parts) >= 3 and parts[1].isdigit():
            http_pattern = "_".join(parts[:2])
            error_suffix = "_" + parts[2]
            http_details = get_http_error_pattern(http_pattern)
            api_details = get_api_error_details(error_suffix)
            if http_details and api_details:
                combined_msg = f"{http_details['msg']}: {api_details['msg']}"
                severity = api_details.get("severity", http_details.get("severity", "ERROR"))
                return (
                    {"msg": combined_msg, "severity": severity, "context": http_details.get("context")},
                    combined_msg
                )
        # Pure HTTP pattern (e.g., "09_409")
        http_details = get_http_error_pattern(error_code)
        if http_details:
            return (http_details, http_details["msg"])

    # 4. Check if it's a device error (with severity)
    device_entry = DEVICE_ERROR_CODES.get(error_code)
    if device_entry:
        msg = device_entry["msg"]
        severity = device_entry.get("severity", "ERROR")
        return (
            {"msg": msg, "severity": severity},
            msg
        )

    # 5. Unknown
    return (None, f"Unknown error code: {error_code}")

def get_error_description(error_code: str) -> str:
    """Get human-readable error description.

    Args:
        error_code: Error code as string

    Returns:
        Error description or "Unknown error code" if not found
    """
    _, description = parse_composite_error(error_code)
    return description

def get_error_severity(error_code: str) -> ErrorSeverity:
    """Get error severity level.

    Args:
        error_code: Error code as string

    Returns:
        ErrorSeverity enum value
    """
    details, _ = parse_composite_error(error_code)
    if details and "severity" in details:
        severity_str = details["severity"]
        severity_map = {
            "INFO": ErrorSeverity.INFO,
            "WARNING": ErrorSeverity.WARNING,
            "ERROR": ErrorSeverity.ERROR,
            "CRITICAL": ErrorSeverity.CRITICAL,
        }
        return severity_map.get(severity_str, ErrorSeverity.ERROR)
    return ErrorSeverity.ERROR

def format_error_message(error_code: str, include_context: bool = False) -> str:
    """Format error message for display.

    Args:
        error_code: Error code as string
        include_context: Whether to include endpoint context

    Returns:
        Formatted error message
    """
    details, description = parse_composite_error(error_code)

    if not details:
        return description

    severity = details.get("severity", "ERROR")
    severity_label = {
        "INFO": "[INFO]",
        "WARNING": "[WARNING]",
        "ERROR": "[ERROR]",
        "CRITICAL": "[CRITICAL]",
    }.get(severity, "[UNKNOWN]")

    message = f"{severity_label} {description}"

    if include_context and "context" in details:
        message += f" [{details['context']}]"

    if include_context and "user_action" in details:
        message += f" — Action: {details['user_action']}"

    return message

# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# Keep old ERROR_CODE_MAP for backward compatibility (now maps to msg only)
ERROR_CODE_MAP = {code: entry["msg"] for code, entry in DEVICE_ERROR_CODES.items()}