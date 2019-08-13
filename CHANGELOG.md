# Changelog

## 0.6.1 2019-08-12
Tested with Hassio 0.97.1 and Bosch Indego 1000

### Breaking changes

### Changes
- Fixed issue 8 and 9:
    - 8: Indego mower state detail not updating
    - 9: Service for indego mower disapperared after version 0.3
    
## 0.6 2019-08-11
Tested with Hassio 0.97.1 and Bosch Indego 1000

### Breaking changes

### Changes
- Added sensor **Indego State Detailed**
- Modified sensor **Indego Mower State** to have 5 states:
    - Docked
    - Mowing
    - Diagnostic mode
    - End of life
    - Software update
    - Stuck
- Better handling of API calls (in case of unknown response)

## 0.5 2019-08-11
Tested with Hassio 0.96.5 and 0.97.1 and Bosch Indego 1000

### Breaking changes

### Changes
- Rewritten API to make less calls to Bosch API servers.
- Added class Mower to implement better handling of API and updates.
- Added two sensors: **Indego battery %** and **Indego battery V** (experimental)

## 0.3 2019-08-01
Tested with Hassio 0.96.5 and Bosch Indego 1000

### Breaking changes
Fixed a typo in service name. New name is "indego.mower_command"
Changed default names on sensors to make them shorter.

### Changes
Uses pyIndego 0.1.6
- Added getSerial in API
Added sensor for Runtime
Added properties on sensor **mower state**
- model
- serial
- firmware 
Added properties on sensor **lawn mowed**
- Session Operation
- Session Mowing
- Session Charging
Added binary sensor **update available**
Added sensor "runtime total" with properties
- Total Operation
- Total Mowing
- Total Charging 
Code refactoring and typos corrected

## 0.2 2019-07-29
Tested with Hassio 0.96.5

### Breaking changes
- Changed from Platform to Domain. This means changes in the component configuration in the configuration.yaml.

### Changes

- Exposed a service-call to HA to send commands to mower
- Added different icons to the sensors
- Dynamic icon for Alert Sensor
- Added RELEASENOTES.md
- Updated API with new function for counting Alerts and showing Detailed Alerts description

## 0.1 2019-07-27

### Changes
Added 3 new sensors:
- lawn_moved
- mower_alert
- mowing_mode
