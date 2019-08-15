# Indego
Home Assistant Custom Component for Bosch Indego Lawn Mower.


![Entities in Home Asistant](/doc/0-Indego_sensors.png)

## Installation
Copy the folder `indego` into your `config/custom_components` in your Home Assistant.
    
## Configuration
Add the domain to your configuration.yaml
``` yaml
#configuration.yaml
indego:
  name:     Indego
  username: !secret indego_username
  password: !secret indego_password
  id:       !secret indego_id
```

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to your secrets.yaml: 
``` yaml
#secrets.yaml
indego_username: name@mail.com
indego_password: mysecretpw
indego_id:       123456789
```
## Usage

### Entities
 All sensors are auto discovered and should appear as "unused entities" after adding the component. List of available sensor entities:

|Sensors                                               | Sensors                                              |
|------------------------------------------------------|------------------------------------------------------|
| ![Mower State](/doc/1-Indego_mower_state.png)        | ![Mower State](/doc/2-Indego_mower_state_detail.png) |
| ![Lawn Mowed](/doc/3-Indego_lawn_mowed.png)          | ![Runtime Total](/doc/4-Indego_runtime_total.png)    |
| ![Battery sensor percent](/doc/5-Indego_battery.png) | ![Battery sensor volt](/doc/6-Indego_battery_v.png)  |
| ![Battery sensor](/doc/7-Indego_alert.png)           |                                                      |

### Service
There are a service exposed to HA called **indego.mower_command**. It sends a specified command to the mower. Accepted commands are:

|Command      |Description           |
|-------------|----------------------|
|mow          | Start/continue mowing|
|pause        | Pause mower          |
|returnToDock | Return mower to dock |

Example creating automation in HA gui:

![Services](/doc/8-Indego_call_service.png)

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
    service: indego.mower_command
```

## Debugging
To get debug logs in your log file, specify theese options in your configuration file:

``` yaml
#configuration.yaml
logger:
  logs:
    custom_components.indego: debug
```

## Contribution
If you experience any readings from your mower that the sensor does not read out correct (could be Alerts or mower state), please dont hesitate to write an issue. I need your input in order to make this component as useful as possible. All suggestions are welcome!

## Issues
If you experience issues/bugs with this the best way to report them is to open an issue in **this** repo.

[Issue link](https://github.com/jm-73/Indego/issues)

## Credits

### Thanks to
onkelfarmor ltjessem nsimb jjandersson shamshala

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
