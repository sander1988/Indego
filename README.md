[![GitHub release](https://img.shields.io/github/release/sander1988/Indego.svg)](https://github.com/sander1988/Indego/releases/) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Bosch Indego Mower

**Home Assistant Custom Component for Bosch Indego robotic lawn mowers**

A comprehensive Home Assistant integration that provides full control and monitoring of your Bosch Indego lawn mower. Get real-time status, battery information, mowing schedules, and more.

![Sensors in Home Assistant](/doc/01_sensors.png)
![Diagnostics in Home Assistant](/doc/02_diagnostics.png)

## ✨ Features

- 🎮 **Full Mower Control** - Start, pause, dock, and schedule mowing
- 📊 **Real-time Monitoring** - Battery, location, alerts, and more
- 📍 **Lawn Mapping** - Visual SVG map with mower position overlay (dynamic streaming based on movement)
- 🤖 **SmartMowing Switch** - Toggle automatic schedule optimization based on weather
- ⚠️ **Alert Management** - Monitor and manage mower alerts with action buttons and complete error list extraction
- 🌍 **Multi-language Support** - German, English, Dutch, French, Spanish, Italian, Danish, Norwegian, Polish, Swedish, Slovak, and more
- 🏠 **Native Entities** - Lawn Mower and Vacuum entities for seamless Home Assistant integration
- 📱 **Multiple Mowers** - Support for multiple mowers in one Home Assistant instance
- 🔌 **Service Monitoring** - Bosch Cloud API availability detection with HTTP 5xx error tracking
- 🔋 **Advanced Battery Info** - Detailed battery metrics (voltage, temperature, cycles, discharge)
- 🛡️ **Intelligent Offline Detection** - 3-layer system (error codes, timeout, successful updates)
- 📍 **Stuck Detection** - Automatic detection when mower is immobilized (> 60 seconds without movement)
- 👤 **Custom User Agent** - Configurable User-Agent for API requests to work around Bosch restrictions
- 📈 **Session Tracking** - Counter for completed mowing sessions
- 🎯 **Dynamic Camera Streaming** - Camera shows as streaming when mower is actively moving/mowing
- 🔲 **Alert Action Buttons** - Quick action buttons to manage specific alerts

## 📖 Table of Contents

- [Features](#-features)
- [Community](#-community)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Monitored Entities](#-monitored-entities)
- [Advanced Features](#-advanced-features--monitoring)
- [Entity Reference](#-entity-reference)
- [Services & Control](#-services--control)
- [Debugging](#-debugging)
- [Supported Models](#-supported-models)
- [Known Issues](#️-known-issues)
- [Contribution & Support](#-contribution--support)
- [Credits](#-credits)

## 💬 Community

Join our Discord community to discuss features, vote on improvements, and get support:
[discord.gg/aD33GsP](https://discord.gg/aD33GsP)

## Installation

### Option 1: Via HACS (Recommended)

1. Add this repository to HACS (Community Store)
2. Search for "Bosch Indego"
3. Click "Install"
4. Restart Home Assistant

[HACS Repository](https://hacs.xyz/)

### Option 2: Manual Installation

1. Copy the `indego` folder from `custom_components` to your Home Assistant `custom_components` folder
2. Restart Home Assistant

## Getting Started

### 1. Install Chrome Extension (Required for Authentication)

Bosch Indego uses OAuth authentication (Bosch SingleKey ID). To complete authentication, you need a Chrome extension:

1. Download: [HomeAssistant Indego authentication helper](/chrome-extension.zip)
2. Extract the ZIP file
3. Go to `chrome://extensions/` in Google Chrome
4. Enable **Developer mode** (top right)
5. Click **Load unpacked** and select the extracted folder
6. ✅ You can disable the extension after setup if you prefer

**Note:** Currently only Google Chrome supports the Bosch authentication flow.

### 2. Add the Integration

1. In Home Assistant: **Settings → Devices & Services → Create Integration**
2. Search for **"Bosch Indego"**
3. Click **Create**
4. Follow the authentication flow (uses the Chrome extension above)
5. All sensors will appear as "Unused Entities" after setup

**You can add this integration multiple times if you own multiple mowers.**

### 3. Configuration Options (Optional)

After adding the integration, you can enable additional features in **Settings → Devices & Services → Bosch Indego → Configure**:

- **Custom User Agent** - Useful if Bosch Cloud is blocking requests. Try alternatives like `HomeAssistant/Indego` or `HA/Indego`
- **Expose as Lawn Mower** - Enable native Home Assistant Lawn Mower entity (recommended for automation compatibility)
- **Expose as Vacuum** - Enable legacy Vacuum entity for backward compatibility
- **Show All Alerts** - Store all historical alerts (use sparingly due to Entity Registry limits)

## 📊 Monitored Entities

All entities are automatically discovered after setup and will appear as "Unused Entities" in Home Assistant.

### 📡 Sensors

**Find all sensors at:** Home Assistant → Settings → Devices & Services → Indego → Sensors

#### Mowing Status

| Sensor | Description |
|--------|-------------|
| **Mower State** | Current state of the mower (e.g., mowing, paused, charging) |
| **State Detail** | Detailed state information with more context |
| **Mowing Mode** | Current mowing mode setting (e.g., Normal, SmartMowing) |
| **Lawn Mowed** | Percentage of lawn mowed (%) |
| **Lawn Mowed Size** | Absolute lawn area mowed in current session (m²) |
| **Garden Size** | Total lawn area (m²) |

#### Battery & Charging Information

| Sensor | Description |
|--------|-------------|
| **Battery Level** | Current battery charge (%) |
| **Battery Voltage** ⚙️ | Battery voltage (V) - diagnostic |
| **Battery Temperature** ⚙️ | Battery cell temperature (°C) - diagnostic |
| **Ambient Temperature** ⚙️ | Ambient air temperature (°C) - diagnostic |
| **Battery Cycles** ⚙️ | Battery charge cycles count - diagnostic |
| **Battery Discharge** ⚙️ | Battery discharge capacity (Ah) - diagnostic |
| **Battery Charging** ⚙️ | Whether mower is currently charging (On/Off) |

**⚙️ = Diagnostic sensors (hidden by default)**

#### Mowing Sessions & Schedule

| Sensor | Description |
|--------|-------------|
| **Session Count** | Total number of completed mowing sessions |
| **Total Mowing Time** | Total cumulative mowing time (hours) |
| **Last Completed Mow** | Timestamp of last full lawn mowing completion |
| **Next Mow Time** | Scheduled next mowing time |

#### Position & Movement

| Sensor | Description |
|--------|-------------|
| **Mower Position X** ⚙️ | X coordinate on map (pixels) - diagnostic |
| **Mower Position Y** ⚙️ | Y coordinate on map (pixels) - diagnostic |

#### Alerts & Maintenance

| Sensor | Description |
|--------|-------------|
| **Last Error Code** | Last error code and timestamp with error description |
| **Firmware Version** ⚙️ | Current firmware version - diagnostic |
| **Maintenance Hours** | Maintenance counter (hours) with status (good/service_due_soon/service_required) |

### 🔔 Binary Sensors

| Binary Sensor | Description |
|--------|-------------|
| **Online Status** | Whether mower is connected (On/Off) - with intelligent 3-layer offline detection |
| **Alerts** | Active alert status indicator with count of unread alerts |
| **Mower Stuck** | Indicates if mower is stuck (detected by no movement >5px for 60+ seconds during mowing) |
| **Service Status** | Bosch Cloud API availability - detects HTTP 5xx errors |
| **Update Available** | Firmware update availability (On/Off) |

### 🎛️ Switches

| Switch | Description |
|--------|-------------|
| **SmartMowing** | Toggle SmartMowing mode on/off - enables automatic schedule optimization based on weather conditions |

### 🔘 Buttons (Alert Management)

| Button | Description |
|--------|-------------|
| **Delete Alert (Last)** | Delete the most recent alert from the mower |
| **Delete All Alerts** | Delete all alerts from the mower at once |
| **Mark Alert as Read (Last)** | Mark the most recent alert as read |
| **Mark All Alerts as Read** | Mark all alerts as read without deleting them |

### 🏠 Native Home Assistant Entities (Optional)

These entities can be enabled in **Settings → Devices & Services → Bosch Indego → Configure**:

#### Lawn Mower Entity

Enable **"Expose as Lawn Mower"** to add a native Home Assistant Lawn Mower entity with full controls:

- **Commands**: Start Mowing, Pause, Dock (return to charging)
- **States**: DOCKED, MOWING, PAUSED, RETURNING, ERROR
- **Features**: Automatically maps 60+ mower states to Home Assistant standard activities
- **Entity ID**: `lawn_mower.indego_<SERIAL>`

#### Vacuum Entity (Legacy)

Enable **"Expose as Vacuum"** for backward compatibility with Vacuum automations:

- **Commands**: Start, Pause, Return to Dock
- **States**: Docked, Cleaning, Idle, Paused, Returning, Error
- **Entity ID**: `vacuum.indego_<SERIAL>`

#### Camera (Lawn Map)

Visual SVG map with mower position overlay:

- **Dynamic Streaming**: Shows as streaming when mower is actively moving/mowing
- **Map Updates**: Refreshes on mower position changes (>5px movement)
- **File Location**: `www/indego_map_<SERIAL>.svg`
- **Entity ID**: `camera.indego_<SERIAL>_lawn_map`


## 🔍 Advanced Features & Monitoring

### 🛠️ Diagnostics & Troubleshooting

#### Device Diagnostics
Available at: **Settings → Devices & Services → Bosch Indego → Device → Diagnostics**

Complete system snapshot including:
- Current mower state and detailed state information
- Battery status (percentage, voltage, temperature, cycles, discharge)
- Garden size and mowing progress metrics
- Runtime statistics (operation, mowing, charging hours)
- Alert history with timestamps and codes
- Maintenance status and hours
- Last API response time
- Position data (X, Y coordinates on map)
- Firmware version and update availability

#### Integration Diagnostics
For Home Assistant administrators to analyze integration health:
- Connection metrics and refresh cycle tracking
- Error code statistics
- Session counter data
- Configuration details (redacted for security)

### 🏥 System Health

Bosch Indego integrates with Home Assistant System Health for service monitoring:

**Access at:** Settings -> System -> Repairs -> System information (top right three dots menu)

Monitors:
- **Bosch API Health**: Detects HTTP 5xx errors and service availability
- **Mower Connectivity**: Shows online/offline status of connected mowers
- **Last Update**: Time of last successful API response (with warnings if >10 minutes stale)
- **Authentication Status**: OAuth2 token validation

Helps distinguish between Bosch Cloud outages vs. local connectivity problems.

### 🔧 Auto Repairs

Automatic issue detection and resolution:

**Authentication Failure Repair**
- **When triggered**: OAuth2 token becomes invalid or expires
- **Resolution**: Click "Fix" to re-authenticate with Bosch SingleKey ID
- **Auto-clears**: After successful re-authentication

**Connection Failure Repair**
- **When triggered**: 5+ consecutive API timeout failures
- **Resolution**: Auto-clears when connectivity is restored
- **Purpose**: Helps distinguish temporary network issues from permanent problems

**Manage at:** Settings → System → Repairs

### 🚨 Alert Management & Error Tracking

#### Complete Alert & Error List

The `binary_sensor.indego_<SERIAL>_alert` sensor stores all active mower alerts as individual attributes:

**Available Attributes (for each alert):**
- `alerts_count` - Number of active alerts
- `last_alert_error_code` - Most recent error code
- `last_alert_message` - Most recent error message
- `last_alert_date` - Most recent error timestamp
- `last_alert_read` - Read status of most recent alert

**Complete Error History (error_0, error_1, error_2, ...):**
- `error_N` - Complete error: `"802: WiFi connection lost - 2024-01-01 12:34:56"`
- `error_N_code` - Error code only: `"802"`
- `error_N_description` - Error description: `"WiFi connection lost"`
- `error_N_timestamp` - Time of error: `"2024-01-01 12:34:56"`
- `error_N_message` - Original API message
- `error_N_read` - Read status (true/false)

**Note:** Use with `show_all_alerts: true` option to store complete history (use sparingly due to Entity Registry limits).

#### Error Code Reference

Over 90 error codes are mapped in the integration. See error list in **Developer Tools → Services → search "indego"** or check [error_codes.py](custom_components/indego/error_codes.py) for complete reference.

### 💻 Service Monitoring

The `binary_sensor.indego_<SERIAL>_service_status` sensor monitors Bosch Cloud API availability:

- **UP** (On) - Bosch API is responding normally
- **DOWN** (Off) - Bosch Cloud experiencing 5xx errors (usually temporary)
- **Attribute** `last_service_error` - HTTP error code (e.g., "HTTP 503")

**Note:** 5xx errors are typically temporary Bosch Cloud issues and resolve automatically.

### 🛡️ Intelligent Offline Detection (3-Layer System)

The integration uses a sophisticated 3-layer system to accurately detect when your mower is offline:

**Layer 1: Error Code Detection**
- Immediately marks mower as offline on API errors: 802, 803, 804 (connection failures)
- Provides instant feedback when mower loses connectivity

**Layer 2: Timeout System**
- After 300 seconds (5 minutes) without a successful API response, mower is marked offline
- Handles situations where the API doesn't return explicit error codes
- Automatically recovers when connectivity is restored

**Layer 3: Last Successful Update Tracking**
- Continuously tracks `_last_successful_update` timestamp
- Monitors refresh cycles to detect prolonged connection loss
- Works in conjunction with error codes and timeout system

**How It Works:**
1. Each successful API call updates the timestamp
2. Every refresh cycle checks for timeout or error conditions
3. If timeout exceeded OR error codes detected → mower state set to offline
4. Online state automatically restored when connection resumes

### 🎬 Camera Streaming & Map

The lawn map camera entity provides dynamic streaming capabilities:

- **Streaming State**: Camera's `is_streaming` property indicates active mower movement
- **Movement Detection**: Automatically detects if mower is in a mowing, moving, or cutting state (states 500-799)
- **Map Updates**: SVG map reloads when mower movement is detected for fresh position data
- **Visual Feedback**: Streaming indicator in Home Assistant UI shows when mower is actively working

### 🎯 Stuck Detection

Automatic stuck mower detection system:

- **Binary Sensor**: `binary_sensor.indego_<SERIAL>_mower_stuck`
- **Detection Threshold**: No movement > 5 pixels for 60+ seconds while mowing
- **Tracking**: Only during active mowing/movement states (state numbers 500-799)
- **Attributes**:
  - `stuck_since` - Timestamp when mower became stuck
  - `stuck_x` - X position (pixels) where mower is stuck
  - `stuck_y` - Y position (pixels) where mower is stuck

### 🌍 Multi-Mower Support

The integration fully supports multiple mowers on the same Bosch account:

- **Add Multiple Times**: You can add this integration multiple times to manage different mowers
- **Service Routing**: Services automatically detect which mower to control via the `mower_serial` parameter
- **Unified Dashboard**: All mowers appear as separate devices in Home Assistant
- **Concurrent Polling**: Each mower is polled independently with optimal refresh intervals

**Using Services with Multiple Mowers:**
```yaml
service: indego.command
data:
  command: mow
  mower_serial: "0123456789ABCDEF"  # Required for multiple mowers
```

### ⚙️ Advanced Configuration

#### API Polling Strategy

**Refresh Intervals:**
- **State Polling**: Immediate on each update cycle (uses 230-second API long-poll timeout)
- **Generic Data** (firmware, mode): Every 10 minutes
- **Position Updates**: Every 60 seconds
- **Map Refresh**: On position changes (>5px movement) or state transitions
- **Battery/Garden Data**: Every 10 minutes

**Retry Strategy** (on connection failures):
- Backoff delays: [0 sec (immediate), 10 sec, 30 sec, 60 sec]
- After 60 seconds: Marks mower as offline after 5+ consecutive failures
- Automatic recovery: Clears offline state on successful reconnection

#### OAuth2 Token Management

- **Token Refresh**: Every 12 hours (aggressive strategy to prevent 400 errors)
- **Bosch Tokens Expire**: At 24 hours, so early refresh prevents gaps
- **Authentication Flow**: Uses Bosch SingleKey ID
- **Required Scope**: `openid profile email offline_access https://prodindego.onmicrosoft.com/indego-mobile-api/Indego.Mower.User`

#### User Agent Configuration

Bosch Cloud may occasionally block requests. Configure custom User-Agent strings:

**Access in:** Settings → Devices & Services → Bosch Indego → Configure → "Custom User Agent"

**Available Options:**
- `HomeAssistant/Indego` - Full description
- `HA/Indego` - Shorter form (default)

**When to change:** If you encounter HTTP 4XX (block) errors, try switching the user agent.

#### Session Tracking

The integration tracks completed mowing sessions:

- **Session Counter**: `sensor.indego_<SERIAL>_session_count` - Total number of completed sessions
- **Increment Logic**: Counter increments when transitioning INTO mowing state (from non-mowing states)
- **Session Attributes** on `lawn_mowed` sensor:
  - `last_session_operation_min` - Total session duration
  - `last_session_cut_min` - Active cutting time
  - `last_session_charge_min` - Charging time between sessions

#### Battery Diagnostics

Detailed battery information available as diagnostic sensors (disabled by default):

| Sensor | Unit | Purpose |
|--------|------|---------|
| **Battery Voltage** | V | Monitor charging voltage for diagnostics |
| **Battery Temperature** | °C | Track battery thermal behavior |
| **Ambient Temperature** | °C | Monitor environmental conditions |
| **Battery Cycles** | count | Track battery age and health |
| **Battery Discharge** | Ah | Monitor discharge capacity |

**Enable these sensors:** Settings → Devices & Services → Indego → Sensors → Enable

#### Multilingual Support

The integration includes translations for 11 languages:
- German (Deutsch), English, Dutch (Nederlands), French (Français)
- Spanish (Español), Italian (Italiano), Danish (Dansk), Norwegian (Norsk)
- Polish (Polski), Swedish (Svenska), Slovak (Slovenčina)

Language selection is handled automatically by Home Assistant based on your system settings.

## 📚 Entity Reference

### Mower States & Activity Mapping

The integration maps 60+ distinct mower states to Home Assistant standard activities:

**Docked States** (0, 101, 257-263, 1281, 64513):
- Mower is at rest in charging dock
- Lawn Mower Activity: DOCKED
- Vacuum State: DOCKED

**Mowing States** (266, 512-525, 768-776, 1005):
- Mower is actively cutting grass or moving during mowing session
- Lawn Mower Activity: MOWING
- Vacuum State: CLEANING / IDLE

**Paused States** (517, 519):
- Mower paused mid-mowing session
- Lawn Mower Activity: PAUSED
- Vacuum State: PAUSED

**Returning States** (detected from "Returning to" state descriptions):
- Mower actively returning to dock
- Lawn Mower Activity: RETURNING
- Vacuum State: RETURNING

**Error States** (1025, 1026, 1027, 1038, 1537, 99999):
- Mower encountered an error condition
- Lawn Mower Activity: ERROR
- Vacuum State: ERROR

**Charging States** (detected from "Charging" in state descriptions):
- Mower is charging in dock
- Tracked separately via `binary_sensor.indego_<SERIAL>_battery_charging`

### Entity Attributes Reference

**Mower State** (`sensor.indego_<SERIAL>_mower_state`):
- Attributes: `last_updated`

**Mower State Detail** (`sensor.indego_<SERIAL>_mower_state_detail`):
- Attributes: `last_updated`, `state_number`, `state_description`
- Provides human-readable state descriptions like "Mowing - Relocalizing", "Charging", "Returning to Dock"

**Battery** (`sensor.indego_<SERIAL>_battery_percentage`):
- Attributes: `voltage_V`, `discharge_Ah`, `cycles`, `battery_temp_°C`, `ambient_temp_°C`, `last_updated`

**Lawn Mowed** (`sensor.indego_<SERIAL>_lawn_mowed`):
- Attributes: `last_completed_mow`, `next_mow`, `last_session_operation_min`, `last_session_cut_min`, `last_session_charge_min`, `last_updated`

**Runtime Total** (`sensor.indego_<SERIAL>_runtime_total`):
- State Class: `total_increasing` (for statistics)
- Attributes: `total_operation_time_h`, `total_mowing_time_h`, `total_charging_time_h`

**Alerts** (`binary_sensor.indego_<SERIAL>_alert`):
- Attributes: Complete error list with:
  - `alerts_count` - Number of active alerts
  - `last_alert_error_code`, `last_alert_message`, `last_alert_date`, `last_alert_read`
  - For each alert: `error_N`, `error_N_code`, `error_N_description`, `error_N_timestamp`, `error_N_message`, `error_N_read`

**Mower Stuck** (`binary_sensor.indego_<SERIAL>_mower_stuck`):
- Attributes: `stuck_since`, `stuck_x`, `stuck_y`

**Maintenance Hours** (`sensor.indego_<SERIAL>_maintenance_hours`):
- Attributes: `maintenance_status` (values: "good", "service_due_soon", "service_required")
- Status logic:
  - < 50 hours: "good"
  - 50-149 hours: "service_due_soon"
  - >= 150 hours: "service_required"

### Entity Categories

Different entity categories are used to organize features in Home Assistant:

**CONFIG Category** (buttons for alert management):
- `button.indego_<SERIAL>_delete_last_alert`
- `button.indego_<SERIAL>_delete_all_alerts`
- `button.indego_<SERIAL>_read_last_alert`
- `button.indego_<SERIAL>_read_all_alerts`
- `switch.indego_<SERIAL>_smartmowing_switch`

**DIAGNOSTIC Category** (detailed information):
- `sensor.indego_<SERIAL>_battery_voltage`
- `sensor.indego_<SERIAL>_battery_temperature`
- `sensor.indego_<SERIAL>_ambient_temperature`
- `sensor.indego_<SERIAL>_battery_cycles`
- `sensor.indego_<SERIAL>_battery_discharge`
- `sensor.indego_<SERIAL>_mower_svg_x`
- `sensor.indego_<SERIAL>_mower_svg_y`
- `sensor.indego_<SERIAL>_firmware_version`

Diagnostic entities are hidden by default but can be enabled via: **Settings → Devices & Services → Indego → Sensors → Enable**

## 🎮 Services & Control

Control your mower through Home Assistant services. All services support multiple mowers via the `mower_serial` parameter.

### Mower Commands

**Service:** `indego.command`

Sends control commands to your mower (compatible with Lawn Mower and Vacuum entities).

**Parameters:**
- `command` (required): One of:
  - `mow` - Start mowing
  - `pause` - Pause current operation
  - `returnToDock` - Return to charging dock
- `mower_serial` (optional): Serial number (required only for multiple mowers)

**Example:**
```yaml
service: indego.command
data:
  command: mow
```

**Service Compatibility:**
- These commands trigger the corresponding Lawn Mower entity methods (async_start_mowing, async_dock, async_pause)
- Commands can also be sent directly to Lawn Mower entity via Home Assistant UI

### SmartMowing Control

The SmartMowing feature can be controlled in two ways:

#### 1. Via Switch (UI Control)

Use the **SmartMowing** switch entity in Home Assistant UI:

- **Entity ID**: `switch.indego_<SERIAL>_smartmowing_switch`
- **Location**: Home Assistant dashboard or automations
- **State Detection**: Automatically detects current SmartMowing status from mower's mode
- **Real-time Sync**: Switch state updates automatically based on mower's current settings

#### 2. Via Service (Automation)

**Service:** `indego.smartmowing`

Enable or disable SmartMowing programmatically for automations.

**Parameters:**
- `enable` (required): `true` | `false`
- `mower_serial` (optional): Serial number (only needed for multiple mowers)

**Example:**
```yaml
service: indego.smartmowing
data:
  enable: true
```

**What SmartMowing Does:**
- Automatic schedule adjustment based on weather and lawn growth
- Mower adapts mowing plan to optimal conditions
- Can be toggled on/off based on your preferences

### Alert Management

#### Delete Specific Alert
**Service:** `indego.delete_alert`

**Parameters:**
- `alert_index` (required): Index of alert to delete (0 = most recent, 1 = second most recent, etc.)
- `mower_serial` (optional)

**Example:**
```yaml
service: indego.delete_alert
data:
  alert_index: 0
```

#### Delete All Alerts
**Service:** `indego.delete_alert_all`

Batch deletes all alerts with configurable delays between deletions.

**Parameters:**
- `mower_serial` (optional)

**Batch Settings:**
- Delay between deletions: 10 seconds
- Maximum rounds: 20 (removes up to 20 alerts per call)

#### Mark Alert as Read
**Service:** `indego.read_alert`

**Parameters:**
- `alert_index` (required): Index of alert (0 = most recent, 1 = second most recent, etc.)
- `mower_serial` (optional)

**Example:**
```yaml
service: indego.read_alert
data:
  alert_index: 0
```

#### Mark All Alerts as Read
**Service:** `indego.read_alert_all`

Batch marks all alerts as read with configurable delays.

**Parameters:**
- `mower_serial` (optional)

**Batch Settings:**
- Delay between read operations: 10 seconds
- Maximum rounds: 20

### Download Lawn Map

**Service:** `indego.download_map`

Downloads the current lawn map from Bosch Cloud API and saves as `www/indego_map_<SERIAL>.svg` in your Home Assistant configuration directory. 

**Used by:**
- Camera entity to display the mowing map with mower position overlay
- Custom dashboards via the SVG map file

**Parameters:**
- `mower_serial` (optional): Serial number (only needed for multiple mowers)

**Note:** The map is automatically downloaded and cached. Use this service to force a fresh map update.

**File Location:** `<HA_CONFIG>/www/indego_map_<SERIAL>.svg`

## 🐛 Debugging

To enable debug logging for troubleshooting, add this to your Home Assistant configuration:

```yaml
logger:
  logs:
    custom_components.indego: debug
    pyIndego: debug
```

Then check your logs in **Settings → System → Logs** for detailed debugging information.

## 📋 Supported Models

The integration supports the following Bosch Indego models:

- Indego 1000, 1100, 1200
- Indego 10C, 13C
- Indego 350, 400
- Indego S+ 350 (1st & 2nd Gen)
- Indego S+ 400 (1st & 2nd Gen)
- Indego S+ 500
- Indego M+ 700 (1st & 2nd Gen)

_Not seeing your model? Please [open an issue](https://github.com/sander1988/Indego/issues) to request support._

## ⚠️ Known Issues

1. **Chrome Extension Required**
   - A [Chrome extension](/chrome-extension.zip) is required to complete the authentication setup (Bosch SingleKey ID OAuth flow)
   - Can be disabled/removed after initial setup

2. **Bosch Cloud API Issues**
   - The Bosch Cloud (Azure) may occasionally block the integration: `HTTP 4XX` errors ("The connection to the Bosch Indego API failed!")
   - **Workaround:** Try changing the user agent during setup or in **Settings → Devices & Services → Bosch Indego Mower → Configure**

3. **Temporary Bosch Cloud Outages**
   - `HTTP 5XX` errors typically indicate temporary Bosch Cloud unavailability (often occurs once daily)
   - These are temporary and resolve automatically

4. **Invalid Commands**
   - Sending impossible commands (e.g., docking while already docked) may cause temporary `HTTP 5XX` errors from Bosch

## 💡 Contribution & Support

### Found a Bug or Have a Suggestion?

1. Check [existing issues](https://github.com/sander1988/Indego/issues) first
2. Open a [new issue](https://github.com/sander1988/Indego/issues/new) with:
   - Your mower model and firmware version
   - Steps to reproduce
   - Relevant logs (with debug enabled)
   - Screenshots if applicable

### Getting Help

- 📚 [Documentation & Issues](https://github.com/sander1988/Indego/issues)
- 💬 [Discord Community](https://discord.gg/aD33GsP)
- 📋 Services reference: **Developer Tools → Services** (search "Bosch Indego")

## 🙏 Credits

**Maintainers:** [@whylev](https://github.com/whylev), [@kimzeuner](https://github.com/kimzeuner), [@sander1988](https://github.com/sander1988)

**Contributors:**
[Eduard](https://github.com/eavanvalkenburg), [Jumper78](https://github.com/Jumper78), [dykandDK](https://github.com/dykandDK), [ultrasub](https://github.com/UltraSub), [Gnol86](https://github.com/Gnol86), naethan, bekkm, onkelfarmor, ltjessem, nsimb, jjandersson, [Shamshala](https://github.com/Shamshala), nath, [urbatecte](https://github.com/urbatecte), [Windmelodie](https://github.com/Windmelodie), [Fuempel](https://github.com/Fuempel), [MagaliDB](https://github.com/MagaliDB), [mhosse](https://github.com/mhosse), [Promises](https://github.com/Pr0mises)

**Inspiration:**
- [Bosch Indego API Documentation](http://grauonline.de/wordpress/?page_id=219)
- [Bosch Indego Controller](https://github.com/jofleck/iot-device-bosch-indego-controller)
