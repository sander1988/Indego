# Indego
Home Assistant Custom Component for Bosch Indego Lawn Mower.


![Entities in Home Asistant](/doc/1-Indego_Sensors.png)

## Installation
Copy the folder `indego` in your `config/custom_components` in your Home Assistant.
    
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

|Sensor                    | Description                                      |
|--------------------------|--------------------------------------------------|
|Indego mower state        | Current state                                    |
|Indego lawn mowed         | Current percentage of the lawn that is mowed     |
|Indego mowing mode        | The mowing mode set                              |
|Indego runtime total      | Sum the total runtime of the mover               |
|Indego alerts             | Number of alerts                                 |
|Indego battery %          | Battery percentage (experimental)                |
|Indego battery V          | Battery voltageNumber (experimental)             |
|Indego mower state detail | Current state in detail                          |

**Indego mover state** has properties for model name, serial and firmware.

![Mower State](/doc/2-Indego_mower_state.png)

**Indego lawn moved** has properties for session total, mowing and charging time.

![Lawn Mowed](/doc/3-Indego_lawn_mowed2.png)

**Indego runtime total** has properties for total, mowig and charging time.

![Runtime Total](/doc/4-Indego_runtime_total.png)

**Indego battery %** has properties for percentage, voltage, cycles, discharge and temperature.
![Battery sensor](/doc/5-Indego_battery.png)

### Service
There are a service exposed to HA called **indego.mower_command**. It sends a specified command to the mower. Accepted commands are:

|Command      |Description           |
|-------------|----------------------|
|mow          | Start/continue mowing|
|pause        | Pause mower          |
|returnToDock | Return mower to dock |

Example creating automation in HA gui:

![Services](/doc/6-Indego_Call_service.png)

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

## Issues

If you experience issues/bugs with this the best way to report them is to open an issue in **this** repo.

[Issue link](https://github.com/jm-73/Indego/issues)

## Credits

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
