# Changelog

## 0.2 2019-07-29
Tested with Hassio 0.96.5

### Breaking changes
Changed from platform to domain. This means changes in the component configuration in the configuration.yaml.

### Changes

Exposed a service-call to HA to send commands to mower
Added different icons to the sensors
Dynamic icon for Alert Sensor
Added RELEASENOTES.md

indego:
  name: Mower name
  username: !secret indego_username
  password: !secret indego_password
  id: !secret indego_id

## 0.1 2019-07-27

### Changes
Added 3 new sensors:
- lawn_moved
- mower_alert
- mowing_mode
