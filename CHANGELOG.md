# Changelog

## 0.8.0 2020-06-02
Tested with Hassio 0.98.5 and Bosch Indego 1000

### Changes
- Bumped pyIndego to 0.8.8
- Added sensor for next mow.
- Component now handles offline mower. (Fix #32 component cant handle offline mower)
- Mower state now shows if mower is online or offline. (Fix #36 Online/offline sensor) 
- A new sensor added for last completed mow. Value also shown as a property to sensor for Lawn Mowed. (Fix #37 Add latest complete mowing)
- Sensors now updates after mower come back online. (Fix #38 Sensors not showing values when mower goes from offline to online)
- This error is due to the component raising an error when timing out instead of handling the error. HA does not want an error raised, then it stops initiating the component. (Fix #39 Error during setup of component indego)
- Added model Indego S+ 350 2019.

## 0.7.4 2019-08-22
Tested with Hassio 0.97.2 and Bosch Indego 1000

### Changes
- Bumped pyIndego to 0.7.8
- Fix #12 and #32: Able to handle a mower that is offline and show API values that can be fetched regardless
- Added badge for HACS Default

## 0.7.3 2019-08-21
Tested with hassio 0.97.2 and Bosch Indego 1000

### Changes
- Renamed Integration in manifest to make it easier to find in HACS store

### Known issues
Issue #12: If mower is offline, one API call (OperationData) gets a timeout. Sometimes this crashes the component at setup and stops it from loading.

## 0.7.2 2019-08-21

### Changes
- Fixed documentation bug for HACS

## 0.7.1 2019-08-15

### Changes
- Bumped pyIndego to 0.7.6.
- Fixes #19 (Better handling of Alert codes not i database)
- Fixes #23 (Better handling of multiple alerts of same type)
- Preparing to fix #2 (add component to HACS)

## 0.7 2019-08-15

### Changes
- Bumped pyIndego to 0.7.4.
- Fixes 13 (Typo in README.md)
- Added max and min values on **Indego battery %** and **Indego Battery V**.
- Indego mower percent now shows an adjusted value for Gen 1 mowers. For gen 2 mower it shows the reported value (as it is reported correctly).
- Added units to all properties on sensors
- Added alert descriptions for the three latest alerts on Alerts sensor
- Added list of alerts for alerts sensor. The sensor now shows the 3 latest non-cleared alerts.

## Known issues
- Issue #12: If mower is offline, one API call (OperationData) gets a timeout. Sometimes this crashes the component at setup and stops it from loading.

## 0.6.1 2019-08-12
Tested with Hassio 0.97.1 and Bosch Indego 1000

### Changes
- Fixed issue 8 and 9:
    - 8: Indego mower state detail not updating
    - 9: Service for indego mower disapperared after version 0.3
    
## 0.6 2019-08-11
Tested with Hassio 0.97.1 and Bosch Indego 1000

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
