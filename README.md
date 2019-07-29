# Indego
Home Assistant Custom Component for Bosch Indego Lawn Mower.

## Files
Place the folder Indego (including the files) in custom-component in your Home Assistant folder for custom-components:

    config/custom_components
    
## Configuration
Add the domain to your configuration.yaml

    indego:
      name: MowerName
      username: !secret indego_username
      password: !secret indego_password
      id: !secret indego_id

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to your secrets.yaml: 

    indego_username: name@mail.com
    indego_password: mysecretpw
    indego_id: 123456789

## Usage

There are four sensor entities:

|Sensor | Description|
|-------|------------|
|MowerName_mower_state | Current state of the mower|
|MowerName_lawn_mowed | Current percentage of the lawn that is mowed|
|MowerName_alerts | Number of alerts on the mower|
|MowerName_mowing_mode | The mowing mode set for the mower|

There are a service exposed to HA:

|Service |Description|
|-------|------------|
|indego.mower_command | Send Json string to the service|

|Json string|Description|
|-------|------------|
|{"command":"mow"} | Start/continue mowing|
|{"command":"pause"} | Pause mower|
|{"command":"returnToDock"} | Return mower to dock|

Debugging:

    logger:
      logs:
        custom_components.indego: debug

## Credits

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
