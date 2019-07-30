# Indego
Home Assistant Custom Component for Bosch Indego Lawn Mower.

## Installation
Place the folder indego in your custom_component in the Home Assistant config folder (config/custom_components).
    
## Configuration
Add the domain to your configuration.yaml
``` yaml
#configuration.yaml
indego:
  name: MowerName
  username: !secret indego_username
  password: !secret indego_password
  id: !secret indego_id
```

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to your secrets.yaml: 
``` yaml
#secrets.yaml
indego_username: name@mail.com
indego_password: mysecretpw
indego_id: 123456789
```
## Usage

### Entities
There are four sensor entities:

|Sensor | Description|
|-------|------------|
|MowerName_mower_state | Current state of the mower|
|MowerName_lawn_mowed | Current percentage of the lawn that is mowed|
|MowerName_alerts | Number of alerts on the mower|
|MowerName_mowing_mode | The mowing mode set for the mower|

Add them to your HA gui. Example of the sensors in the HA frontend.
![GitHub Logo](/doc/Indego_Sensors.PNG)
Format: ![Alt Text](url)

### Service
There are a service exposed to HA called indego.mower_command. It sends a specified command to the mower.

|Service |Description|
|-------|------------|
|indego.mower_command | Send Json string to the service|

|Json string|Description|
|-------|------------|
|{"command":"mow"} | Start/continue mowing|
|{"command":"pause"} | Pause mower|
|{"command":"returnToDock"} | Return mower to dock|

Example creating automation in HA gui:


Example for automations.yaml:

``` yaml
# automations.yaml
- id: '1564475250261'
  alias: Mower start
  trigger:
  - at: '10:30'
    platform: time
  condition: []
  action:
  - data:
      command: mow
    service: indego.mover_command
```

## Debugging
To get debug logs in your log file, specify theese options in your configuration file:

``` yaml
#configuration.yaml
logger:
  logs:
    custom_components.indego: debug
```

## Credits

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
