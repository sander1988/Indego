"""Error Code System Documentation

This document explains the new comprehensive error code system for the Indego integration.

## Overview

The error code system handles four types of errors:

1. **Mower State Codes** (200-299, 512-799, 1000+)
   - Firmware states from the mower
   - Example: 513 = "Mowing", 768 = "Returning to dock"

2. **Device/Hardware Error Codes** (0-1156)
   - Physical sensor/motor/battery failures
   - Example: 802 = "WiFi connection lost", 701 = "Mower stuck"

3. **API Error Code Suffixes** (_1 to _18177)
   - Operation-specific failures from API
   - Example: _12292 = "PIN not set", _12288 = "Battery not OK"

4. **HTTP Error Code Patterns** (composite)
   - HTTP status + endpoint context
   - Example: "09_409" = "Mower already paired", "16_500_12288" = "Mow failed: Battery not OK"

## Usage Examples

### Basic Error Description
```python
from .error_codes import get_error_description

# Device error
desc = get_error_description("802")
# Returns: "WiFi connection lost"

# API error suffix
desc = get_error_description("_12292")
# Returns: "PIN not set – unable to mow"

# HTTP pattern
desc = get_error_description("09_409")
# Returns: "Mower already paired to account"
```

### Error Severity
```python
from .error_codes import get_error_severity, ErrorSeverity

severity = get_error_severity("_12292")
# Returns: ErrorSeverity.ERROR

if severity == ErrorSeverity.CRITICAL:
    _LOGGER.critical("Critical error!")
elif severity == ErrorSeverity.ERROR:
    _LOGGER.error("Error occurred")
elif severity == ErrorSeverity.WARNING:
    _LOGGER.warning("Warning!")
else:
    _LOGGER.info("Info only")
```

### Formatted Error Messages
```python
from .error_codes import format_error_message

# Simple format
msg = format_error_message("802")
# Returns: "⚠️ WiFi connection lost"

# With context
msg = format_error_message("_12292", include_context=True)
# Returns: "❌ PIN not set – unable to mow [PUT /state (mow)] — Action: Set PIN on mower display"
```

### Composite Error Parsing
```python
from .error_codes import parse_composite_error

# Parse error and get full details
details, description = parse_composite_error("16_500_12288")
# description: "Mower state update failed: Battery not OK / low temperature – cannot mow"
# details['severity']: "ERROR"
# details['context']: "PUT /state"
```

### Mower State Information
```python
from .error_codes import get_mower_state_info

state_info = get_mower_state_info("513")
# Returns: {
#     'name': 'IN_LAWN_MOWING',
#     'display': 'Mowing',
#     'state': 'mowing'
# }
```

## Error Code Tables

### Mower State Codes
- **200-299**: Dock/Charging states (257, 258, 259, 260, 261, 262, 263, 266)
- **512-599**: Lawn states (512-526)
- **768-799**: Returning to dock states (768-776)
- **1000+**: Service/maintenance states (1025-1792)
- **0, 1-5, 64513, 69420**: Synthetic/virtual states

### Device Error Codes
- **0**: No error
- **40-70**: Internal/system errors
- **100-220**: Wheel/motor/sensor errors
- **149-194**: Perimeter/wire errors
- **216**: Drive errors
- **700-799**: Navigation/stuck errors
- **800-805**: Communication errors
- **900-999**: Firmware/software errors
- **1000-1156**: Battery/system errors

### API Error Suffixes
- **_1 to _9**: General protocol errors
- **_12288 to _12543**: Mow operation errors
- **_12544 to _12799**: Return to dock errors
- **_12800 to _12802**: Pause operation errors
- **_10497 to _10752**: Map operation errors
- **_14080 to _14081**: Calendar errors
- **_13824 to _13825**: Map delete errors
- **_16896 to _17153**: Security/PIN errors
- **_14336**: Date & time errors
- **_15616**: Border cut errors

### HTTP Error Patterns
- **00_401**: Wrong credentials
- **04_409**: Email already in use
- **09_409**: Mower already paired
- **16_500**: Mower state update failed
- **150_401**: Login required (session expired)
- **504_timeout**: Gateway timeout

## Integration Points

The error code system is integrated in:

1. **`_update_error_tracking()`**
   - Uses `get_error_severity()` for appropriate logging level
   - Stores `error_severity` attribute on alert entity

2. **`_update_alerts()`**
   - Enhanced error descriptions with severity
   - Stores `error_{index}_severity` for each alert

3. **`_update_state()`**
   - Better HTTP error handling
   - ClientResponseError mapped to error descriptions

4. **Logging**
   - Severity-based log levels (CRITICAL/ERROR/WARNING/INFO)
   - Formatted error messages with icons

## Backward Compatibility

The old `ERROR_CODE_MAP` is still available for backward compatibility:

```python
from .error_codes import ERROR_CODE_MAP

# Old way still works
msg = ERROR_CODE_MAP.get("802", "Unknown")
# Returns: "WiFi connection lost"
```

## Future Extensions

To add new error codes:

1. **Device Error**: Add to `DEVICE_ERROR_CODES` dict
2. **API Error Suffix**: Add to `API_ERROR_CODES` dict
3. **HTTP Pattern**: Add to `HTTP_ERROR_PATTERNS` dict
4. **Mower State**: Add to `MOWER_STATE_CODES` dict

Example:
```python
DEVICE_ERROR_CODES["2000"] = "New motor error"
API_ERROR_CODES["_20000"] = {"msg": "New API error", "severity": "ERROR"}
HTTP_ERROR_PATTERNS["99_500"] = {"msg": "New endpoint failed", "severity": "ERROR"}
MOWER_STATE_CODES["2000"] = {"name": "NEW_STATE", "display": "New state", "state": "unknown"}
```

## Testing

Test the error code system:

```python
from custom_components.indego.error_codes import *

# Test device errors
print(get_error_description("802"))

# Test API errors
print(get_error_description("_12292"))

# Test HTTP patterns
print(get_error_description("09_409"))

# Test composite errors
details, desc = parse_composite_error("16_500_12288")
print(desc)
print(f"Severity: {details['severity']}")

# Test severity
severity = get_error_severity("_12292")
print(f"Severity level: {severity.name}")

# Test formatted messages
msg = format_error_message("802", include_context=True)
print(msg)
```

## Coverage Summary

- **Mower State Codes**: 27 states (100% from RE)
- **Device Error Codes**: 50+ codes (100% from existing)
- **API Error Codes**: 40+ codes (100% from RE)
- **HTTP Error Patterns**: 30+ patterns (100% from RE)
- **Total Coverage**: 150+ error scenarios

## Performance

- Error lookups: O(1) dict lookup
- Parsing composite errors: O(1) for known patterns, O(n) for regex matching
- No external dependencies or network calls

## Known Limitations

1. Regex patterns (like `XX_5XX`) require explicit matching
2. New error codes must be manually added
3. No automatic error code discovery from API responses
"""
