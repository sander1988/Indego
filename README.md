# Indego
Home Assistant Custom Component for Bosch Indego Lawn Mower

## Files
Place the files in custom-component in your Home Assistant folder for custom-componentes

    config/custom_components
    
## Configuration
Add the domain to your configuration.yaml

indego:
  name: Mower name
  username: !secret indego_username
  password: !secret indego_password
  id: !secret indego_id

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to secrets.yaml: 

  indego_username: name@mail.com
  indego_password: mysecretpw
  indego_id: 123456789

## Usage

There are four sensor entities:

|sensor | description|
|-------|------------|
|<name>_mower_state | This is the current state of the mower. Updated every 30 seconds.|
|<name>_lawn_mowed | This is the current percentage of the lawn that is mowed.|
|<name>_alerts | Number of alerts on the mower|
|<name>_mowing_mode | The mowing mode set for the mower|

There are a service exposed to HA:

|service | description|
|-------|------------|
|indego.mower_command | Send json string to the service|

|json string| description|
|-------|------------|
|{"command":"mow"}|start/continue mowing|
|{"command":"pause"}|pause mower|
|{"command":"returnToDock"}|Return mower to dock|

Debugging:

    logger:
      default: error
      logs:
        custom_components.indego: debug


Credits:

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
