[![GitHub release](https://img.shields.io/github/release/jm-73/Indego.svg)](https://GitHub.com/jm-73/Indego/releases/) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Indego
Join the Discord channel to discuss around this integration and vote for your favourite change to happen!
https://discord.gg/aD33GsP

Home Assistant Custom Component for Bosch Indego Lawn Mower.

![Entities in Home Asistant](/doc/0-Sensors.png)

## Installation

### Alternative 1
Install via HACS Community Store: https://hacs.xyz/
### Alternative 2
Copy the folder `indego` in `custom_components` into your `custom_components` in your Home Assistant.

## Reboot
Reboot HA in order to get HA to find the newly added files.

## Configuration
Add the domain to your configuration.yaml. Username, password and id (serial) is mandatory. Name (default = Indego) and polling (default = true) is optional.
``` yaml
#configuration.yaml
indego:
  name:     Indego
  username: !secret indego_username
  password: !secret indego_password
  id:       !secret indego_id
  polling:  True
```
Polling the battery will make the mower to wake up for 10 minutes every hour. The operating hours will increase with 2,5 hours roughly for 24h. This also drains the battery. A typical drain for 24h will be around 50%. This makes your mower to charge one extra time every other day. 

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to your secrets.yaml: 
``` yaml
#secrets.yaml
indego_username: "name@mail.com"
indego_password: "mysecretpw"
indego_id:       "123456789"
```
## Usage

### Entities
 All sensors are auto discovered and should appear as "unused entities" after adding the component. List of available sensor entities:
| Description | Screenshot |
:--------------------------------|:---------------------------------:
Mower State: Shows what state the mower reports.  Possible values are: Mowing, Docked, Charging. | ![Mower state](/doc/1-State.png)
Mower State Detailed: Show detailed state of the mower.  Possible values:                        | ![Mower state](/doc/2-StateDetail.png)
![Lawn mowed](/doc/3-LawnMowed.png)          ![Runtime total](/doc/4-Runtime.png)
![Battery sensor percent](/doc/5-Battery.png) ![Battery sensor volt](/doc/6-BatteryV.png)
![Battery sensor](/doc/7-Alerts.png)           ![Last completed mow](/doc/8-LastCompleted.png)
![Next mow](/doc/9-NextMow.png) ! ![Next mow](/doc/10-MowingMode.png)

### Service

#### indego.command ####
Sends a command to the mower. Example code:
command: mow

Accepted values are:
|Command       |Description           |
|--------------|----------------------|
| mow          | Start/continue mowing|
| pause        | Pause mower          |
| returnToDock | Return mower to dock |

#### indego.smartmowing ####
Changes mow mode. Example:
enable: true

Accepted values are:
|value        |Description           |
|-------------|----------------------|
| true        | SmartMowing eabled   |
| false       | SmartMowing disabled |


### Examples
Creating automation in HA gui:

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
To get debug logs from the component in your log file, specify theese options in your configuration file:

``` yaml
#configuration.yaml
logger:
  logs:
    custom_components.indego: debug
```

To get debug logs from the python API library in your log file, add this line to your configuration file in additon to the lines above:

``` yaml
    pyIndego: debug
```

## Contribution
If you experience any readings from your mower that the sensor does not read out correct (could be Alerts or mower state), please dont hesitate to write an issue. I need your input in order to make this component as useful as possible. All suggestions are welcome!

## Issues
If you experience issues/bugs with this the best way to report them is to open an issue in **this** repo.

[Issue link](https://github.com/jm-73/Indego/issues)

## Credits

### Thanks to
dykandDK ultrasub Gnol86 naethan bekkm onkelfarmor ltjessem nsimb jjandersson shamshala nath

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
