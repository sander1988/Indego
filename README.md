[![GitHub release](https://img.shields.io/github/release/jm-73/Indego.svg)](https://GitHub.com/jm-73/Indego/releases/) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Indego
Join the Discord channel to discuss around this integration and vote for your favourite change to happen!
https://discord.gg/aD33GsP

Home Assistant Custom Component for Bosch Indego Lawn Mower.

![Entities in Home Asistant](/doc/0-Sensors_1.png)

## Installation

### Alternative 1
Install via HACS Community Store: https://hacs.xyz/
### Alternative 2
Copy the folder `indego` in `custom_components` into your `custom_components` in your Home Assistant.

## Reboot
Reboot HA in order to get HA to find the newly added custom component.

## Configuration
Add the domain to your configuration.yaml. Username, password and id (serial) is mandatory. Name (default = Indego) and polling (default = false) is optional.
``` yaml
#configuration.yaml
indego:
#Required
  username: !secret indego_username
  password: !secret indego_password
  id:       !secret indego_id
#Optional
  name:     Indego
```

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to your secrets.yaml: 
``` yaml
#secrets.yaml
indego_username: "name@mail.com"
indego_password: "mysecretpw"
indego_id:       "123456789"
```
## Usage

### Entities
 All sensors are auto discovered and should appear as "unused entities" after adding the component.
| Description | Screenshot |
| <img width=600/> | <img width=200/> |
***Mower state***<br>Shows state of the mower.<br>Possible values:<br> *Mowing, Docked*. | pic
***Mower state detail***<br>Shows detailed state of the mower.<br>Possible values:<br> A lot... | pic
***Lawn mowed***<br>Shows percentage of lawn mowed. | ![Lawn mowed](/doc/3-LawnMowed_3.png)
***Total mowing time***<br>Shows the total mowing time for the mower. Mow time, chargin time and total operating time shows as attruibutes. | ![Runtime total](/doc/4-Mowtime_3.png)
***Battery***<br>Shows the status of the battery. | ![Battery sensor percent](/doc/5-Battery_3.png)
***Alerts***<br>Shows all alerts | ![Alerts sensor](/doc/7-Alerts_3.png)
***Last completed mow***<br>Shows when the lawn was completed last time. | pic
***Next mow time***<br>Show the next planned mow. | pic
***Mowing mode***<br>Shows the mowing mode set. Possble values:<br> *manual, calendar, smartmowing* | pic
***Online***<br>Shows if the mower is online/offline/sleeping. Possble values:<br> *True, False* | [Online status](/doc/11-Online_3.png)
***Update available***<br>Shows if there is an update available for the firmware. Possble values:<br> *True, False* | [Update available](/doc/12-Update_3.png)



| Description | Screenshot |
| <img width=600/> | <img width=200/> |
***Mower state***<br>Shows state of the mower.<br>Possible values:<br> *Mowing, Docked*. | ![Mower state](/doc/1-State_1.png)
***Mower state detail***<br>Shows detailed state of the mower.<br>Possible values:<br> A lot... | ![Mower state](/doc/2-StateDetail.png)
***Lawn mowed***<br>Shows percentage of lawn mowed. | ![Lawn mowed](/doc/3-LawnMowed_2.png)
***Total mowing time***<br>Shows the total mowing time for the mower. Mow time, chargin time and total operating time shows as attruibutes. | ![Runtime total](/doc/4-Runtime.png)
***Battery***<br>Shows the status of the battery. | ![Battery sensor percent](/doc/5-Battery_2.png)
***Alerts***<br>Shows all alerts | ![Alerts sensor](/doc/7-Alerts_2.png)
***Last completed mow***<br>Shows when the lawn was completed last time. | ![Last completed mow](/doc/8-LastCompleted.png)
***Next mow time***<br>Show the next planned mow. | ![Next mow](/doc/9-NextMow.png)
***Mowing mode***<br>Shows the mowing mode set. Possble values:<br> *manual, calendar, smartmowing* | ![Next mow](/doc/10-MowingMode.png)
***Online***<br>Shows if the mower is online/offline/sleeping. Possble values:<br> *True, False* | [Next mow](/doc/11-Online_2.png)
***Update available***<br>Shows if there is an update available for the firmware. Possble values:<br> *True, False* | [Update available](/doc/12-Update_2.png)

## Service

### indego.command ####
Sends a command to the mower. Example code:<br>
`command: mow`

Accepted values are:
|Command         |Description           |
|----------------|----------------------|
| `mow`          | Start/continue mowing|
| `pause`        | Pause mower          |
| `returnToDock` | Return mower to dock |

![Services](/doc/S1-Command1.png)

### indego.smartmowing ####
Changes mowing mode. Example:<br>
`enable: true`

Accepted values are:
|value        |Description           |
|-------------|----------------------|
| `true`      | SmartMowing enabled  |
| `false`     | SmartMowing disabled |


## Examples
Creating automation in HA gui:

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
    service: indego.command
```

## Debugging
To get debug logs from the component in your log file, specify theese options in your configuration file:

``` yaml
#configuration.yaml
logger: 
  default: critical 
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
Eduard Jumper dykandDK ultrasub Gnol86 naethan bekkm onkelfarmor ltjessem nsimb jjandersson shamshala nath

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller

<a href="https://www.buymeacoffee.com/jm73" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
