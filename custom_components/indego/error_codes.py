"""Comprehensive error code mappings for Bosch Indego mowers.

This module provides complete error handling for:
1. Mower State Codes (firmware states)
2. API Error Codes (operation errors from endpoints)
3. HTTP Error Patterns (composite codes from API responses)
4. Communication/System Errors

Based on Bosch Indego Connect v4.1.2 Reverse Engineering.
"""

from enum import Enum
from typing import Optional, Tuple

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
    "266": {"name": "IN_DOCK_LEAVING_DOCK", "display": "Leaving dock", "state": "docked"},

    # Lawn States (512-599)
    "512": {"name": "IN_LAWN_LEAVING_DOCK", "display": "Leaving dock", "state": "mowing"},
    "513": {"name": "IN_LAWN_MOWING", "display": "Mowing", "state": "mowing"},
    "514": {"name": "IN_LAWN_RELOCALISING", "display": "Relocalising", "state": "mowing"},
    "515": {"name": "IN_LAWN_LOADING_MAP", "display": "Loading map", "state": "mowing"},
    "516": {"name": "IN_LAWN_MAPPING", "display": "Learning lawn", "state": "mowing"},
    "517": {"name": "IN_LAWN_PAUSED", "display": "Paused", "state": "paused"},
    "518": {"name": "IN_LAWN_BORDER_CUT", "display": "Border cut", "state": "mowing"},
    "519": {"name": "IN_LAWN_IDLE", "display": "Idle in lawn", "state": "mowing"},
    "520": {"name": "IN_LAWN_MAPPING_PAUSED", "display": "Learning lawn (paused)", "state": "paused"},
    "521": {"name": "IN_LAWN_BORDER_CUTTING", "display": "Border cutting", "state": "mowing"},
    "522": {"name": "IN_LAWN_UNUSED", "display": "Border cutting", "state": "mowing"},
    "523": {"name": "IN_LAWN_SPOT_MOWING", "display": "Spot mowing", "state": "mowing"},
    "524": {"name": "IN_LAWN_RANDOM_MOWING", "display": "Random mowing", "state": "mowing"},
    "525": {"name": "IN_LAWN_SPOT_MOWING_COMPLETE", "display": "Spot mowing complete", "state": "mowing"},
    "526": {"name": "IN_LAWN_RANDOM_MOWING_COMPLETE", "display": "Random mowing complete", "state": "mowing"},

    # Returning to Dock (768-799)
    "768": {"name": "RET_DOCK", "display": "Returning to dock", "state": "returning"},
    "769": {"name": "RET_DOCK_HMI", "display": "Returning to dock", "state": "returning"},
    "770": {"name": "RET_DOCK_BS", "display": "Returning to dock", "state": "returning"},
    "771": {"name": "RET_DOCK_BATTERY_LOW", "display": "Returning to dock – battery low", "state": "returning"},
    "772": {"name": "RET_DOCK_CALENDAR", "display": "Returning to dock – calendar", "state": "returning"},
    "773": {"name": "RET_DOCK_BATTERY_TEMP", "display": "Returning to dock – battery temp", "state": "returning"},
    "774": {"name": "RET_DOCK_APP", "display": "Returning to dock", "state": "returning"},
    "775": {"name": "RET_DOCK_GARDEN_COMPLETE", "display": "Returning to dock – lawn complete", "state": "returning"},
    "776": {"name": "RET_DOCK_RELOCALISING", "display": "Returning to dock – relocalising", "state": "returning"},

    # Service/Maintenance (1025+)
    "1025": {"name": "SERVICE_DIAGNOSTIC_MODE", "display": "Diagnostic mode", "state": "error"},
    "1026": {"name": "SERVICE_EOL_MODE", "display": "EOL mode", "state": "error"},
    "1027": {"name": "SERVICE_REQUESTING_STATUS", "display": "Getting status", "state": "error"},
    "1281": {"name": "SW_UPDATE_MODE", "display": "Firmware update", "state": "error"},
    "1537": {"name": "LOW_POWER_MODE", "display": "Low power mode", "state": "error"},
    "1792": {"name": "LEAVING_DOCK", "display": "Leaving dock", "state": "error"},

    # Synthetic States (app-side only)
    "0": {"name": "GETTING_STATUS", "display": "Getting status", "state": "unknown"},
    "1": {"name": "OFFLINE", "display": "Offline", "state": "offline"},
    "2": {"name": "UNPAIRED", "display": "No mower paired", "state": "unknown"},
    "3": {"name": "NOT_MAPPED", "display": "Mower not mapped", "state": "error"},
    "4": {"name": "NO_PIN", "display": "PIN not set", "state": "error"},
    "5": {"name": "DISABLED", "display": "Mower disabled", "state": "error"},
    "64513": {"name": "WAKING_UP_INDEGO", "display": "Getting status", "state": "unknown"},
    "69420": {"name": "SYNTHETIC_COMMAND_SENT", "display": "Command sent", "state": "unknown"},
}

# =============================================================================
# DEVICE/HARDWARE ERROR CODES (Mower-reported errors)
# =============================================================================

DEVICE_ERROR_CODES = {
    # No error
    "0": "No error",

    # Internal/System errors (40-70)
    "45": "Unknown internal error",
    "55": "Button cell almost empty",
    "57": "Compass error",
    "58": "No data from mobile module",
    "60": "Mower tilted",

    # Wheel/Motor/Sensor errors (100-220)
    "101": "Mower was lifted",
    "102": "Lift sensor right front steering wheel",
    "103": "Lift sensor left front steering wheel",
    "104": "Stop button pressed",
    "105": "Mower tilted >45°",
    "106": "Invalid input",
    "107": "System error",
    "108": "System error",
    "109": "System error",
    "115": "Permanent tactile detected",
    "126": "Charging current/voltage too high",
    "127": "Charging current/voltage too high",
    "129": "Cutter load too high",
    "130": "Cutter load too high",
    "131": "Cutter load too high",
    "133": "Internal error",
    "134": "Internal error",
    "136": "Left wheel blocked",
    "137": "Right wheel blocked",
    "142": "Internal wheel drive error",
    "143": "Intermittent error",

    # Perimeter/Wire errors (149-194)
    "149": "Mower out of perimeter limit",
    "150": "No signal from perimeter wire",
    "151": "Waiting for loop signal",
    "162": "Charging error",
    "194": "No perimeter signal detected",

    # Drive errors (216)
    "216": "Left wheel stuck",

    # Navigation/Stuck errors (700-799)
    "701": "Mower stuck",
    "702": "Mower trapped",
    "703": "Mower too high",
    "704": "Unable to proceed",
    "705": "Uneven ground",
    "706": "Grass too high",

    # Communication errors (800-899)
    "801": "Bluetooth error",
    "802": "WiFi connection lost",
    "803": "API connection error",
    "804": "No connection to server",
    "805": "Communication timeout",

    # Firmware/Software errors (900-999)
    "901": "Firmware error",
    "902": "Software error",
    "903": "Configuration error",
    "904": "Memory error",

    # Battery/System errors (1100+)
    "1000": "System error",
    "1001": "Unknown error",
    "1002": "Shutdown detected",
    "1008": "Mower is stuck",
    "1108": "Inclination angle too large",
    "1138": "Last run error",
    "1146": "Orientation filter error",
    "1148": "On-/Off error. Need PIN code to unlock",
    "1156": "Unsupported battery pack",

    # Special Alert Codes (string-based)
    "ntfy_blade_life": "Reminder blade life",
    "smartMow.mowerUnreachable": "SmartMowing disabled",
    "firmware.updateComplete": "Software update complete",
    "smartMow.mowerReachable": "Mower reachable. SmartMow is now enabled.",
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

    # Date & Time Errors (suffix: _14336)
    "_14336": {"msg": "Invalid date/time value", "severity": "ERROR", "context": "PUT /dateAndTime"},

    # Border Cut Errors (suffix: _15616)
    "_15616": {"msg": "Border cut cannot be changed in current state", "severity": "ERROR", "context": "PUT /borderCut"},

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

    # 500 with Mower Disabled (_5 suffix)
    "XX_5XX": {"msg": "Mower disabled – operation not available", "severity": "ERROR", "context": "Any endpoint"},
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
    return DEVICE_ERROR_CODES.get(str(error_code), f"Unknown device error: {error_code}")


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

    # Try regex-like patterns
    # Check for XX_5XX pattern (mower disabled)
    if "_5" in composite_code and "XX" not in composite_code:
        parts = composite_code.split("_")
        if len(parts) >= 2 and parts[1].startswith("5"):
            return HTTP_ERROR_PATTERNS.get("XX_5XX")

    return None


def parse_composite_error(error_code: str) -> Tuple[Optional[dict], Optional[str]]:
    """Parse composite error code and extract details.

    Handles formats:
    - Simple: "12292" (device error)
    - API Suffix: "_12292" (API error)
    - HTTP Pattern: "09_409" (HTTP conflict)
    - HTTP + Suffix: "16_500_12288" (HTTP 500 with mower error)
    - State Code: "257" (mower state)

    Args:
        error_code: Error code string

    Returns:
        Tuple of (error_details_dict, error_description_str)
    """
    error_code = str(error_code).strip()

    # Check if it's a composite HTTP pattern
    if "_" in error_code:
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

        # API suffix (e.g., "_12292")
        api_details = get_api_error_details(error_code if error_code.startswith("_") else "_" + error_code)
        if api_details:
            return (api_details, api_details["msg"])

    # Check if it's a mower state code
    state_info = get_mower_state_info(error_code)
    if state_info:
        return (
            {"name": state_info["name"], "display": state_info["display"], "state": state_info["state"]},
            state_info["display"]
        )

    # Check if it's a device error
    device_msg = get_device_error_description(error_code)
    if not device_msg.startswith("Unknown"):
        return (
            {"msg": device_msg, "severity": "ERROR"},
            device_msg
        )

    # Unknown error
    return (None, f"Unknown error code: {error_code}")


def get_error_description(error_code: str) -> str:
    """Get human-readable error description (backward compatible).

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
    severity_icon = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔴",
    }.get(severity, "❓")

    message = f"{severity_icon} {description}"

    if include_context and "context" in details:
        message += f" [{details['context']}]"

    if include_context and "user_action" in details:
        message += f" — Action: {details['user_action']}"

    return message


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# Keep the old ERROR_CODE_MAP for backward compatibility
ERROR_CODE_MAP = {**DEVICE_ERROR_CODES}
