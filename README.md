[![GitHub release](https://img.shields.io/github/release/sander1988/Indego.svg)](https://github.com/sander1988/Indego/releases/) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Indego
Join the Discord channel to discuss around this integration and vote for your favourite change to happen!
https://discord.gg/aD33GsP

Home Assistant Custom Component for Bosch Indego Lawn Mower.

![Entities in Home Asistant](/doc/0-Sensors_3.png)

## Installation

### Alternative 1
Install via HACS Community Store: https://hacs.xyz/

### Alternative 2
Copy the folder `indego` in `custom_components` into your `custom_components` in your Home Assistant.

## Reboot
Reboot HA in order to get HA to find the newly added custom component.

## Configuration

### Authentication using Bosch SingleKey ID
Bosch moved to a new authentication method called Bosch SingleKey ID (using OAuth) at the beginning of 2023. 
Therefore we needed to rewrite the authentication flow. 

Currently **only** Google Chrome is the supported for authenticating with the Bosch SingleKey ID servers when adding the integration in HA.
Also a small extension needs to be installed (temporarily) in Google Chrome to handle the response from the Bosch authentication servers. 
More (technical) information on the why can be found in this [issue](https://github.com/sander1988/Indego/issues/171).

Optionally you can remove or disable the extension after adding the Bosch Indego integration to HomeAssistant.

### Installing the Chrome extension
1. The **HomeAssistant Indego authentication helper** extension can be downloaded [here](/chrome-extension.zip). 
2. Extract the ZIP archive.
3. Go to [extensions](chrome://extensions/) in Google Chrome.
4. Enable **Developer mode** (right top).
5. Choose **Load unpacked** and select the unpacked extension.


### Adding a mower
_Make sure you are accessing your HomeAssistant through Google Chrome and have the **HomeAssistant Indego authentication helper** extension enabled (as described above)._

Please add this integration through the HomeAssistant interface (Settings > Devices & Services > Add Integration). Search for **Bosch Indego Mower**. 
Configuration through YAML (configuration) files is no longer supported.

You can add this integration multiple times in case you own multiple Indego mowers.

## Usage

### Entities
 All sensors are autodiscovered and should appear as "unused entities" after adding the component.

| Description | Screenshot |
|-------------|------------|
| <img width=400/> | <img width=325/> |
***Mower state***<br>Shows state of the mower. | ![State](/doc/1-State_3.png)
***Mower state detail***<br>Shows detailed state of the mower. | ![State Detail](/doc/2-StateDetail_1.png)
***Lawn mowed***<br>Shows percentage of lawn mowed. | ![Lawn mowed](/doc/3-LawnMowed_3.png)
***Total mowing time***<br>Shows the total mowing time for the mower. | ![Mowtime total](/doc/4-MowTime_3.png)
***Battery***<br>Shows the status of the battery. | ![Battery sensor percent](/doc/5-Battery_3.png)
***Alerts***<br>Shows all alerts | ![Alerts sensor](/doc/7-Alerts_3.png)
***Last completed mow***<br>Shows when the lawn was completed last time. | ![Last mow](/doc/8-LastCompleted_3.png)
***Next mow time***<br>Show the next planned mow. | ![Next mow](/doc/9-NextMow_3.png)
***Mowing mode***<br>Shows the mowing mode set. | ![Mowing mode](/doc/10-MowingMode_2.png)
***Online***<br>Shows if the mower is online/offline. Possble values:<br> *True, False* | ![Online status](/doc/11-Online_3.png)
***Update available***<br>Shows if there is an update available for the firmware. Possble values:<br> *On, Off* | ![Update available](/doc/12-Update_4.png)



## Service
This list might incomplete. You can find all services provided by this component in HomeAssistant under Developer tools > Services and search for 'Bosch Indego Mower'.

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

### indego.delete_alert ####
Deletes one specific Alert. Example:<br>
`alert_index: 0` deletes the latest alert.

Accepted values are:
|value               |Description                           |
|--------------------|--------------------------------------|
| `each number`      | Delete Alert number X (0 for latest) |

### indego.delete_alert_all ####
Deletes all Alerts. Example:<br>
`alert_index: 0` 

Accepted values are:
|value     |Description         |
|----------|--------------------|
| `0`      | Delete all Alerts  |

### indego.read_alert ####
Marks one specific Alert as read. Example:<br>
`alert_index: 0` marks the latest alert.

Accepted values are:
|value               |Description                                 |
|--------------------|--------------------------------------------|
| `each number`      | Mark Alert number X as read (0 for latest) |

### indego.read_alert_all ####
Marks all Alerts as read. Example:<br>
`alert_index: 0` 

Accepted values are:
|value     |Description               |
|----------|--------------------------|
| `0`      | Mark all Alerts as read  |

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
To see the debug logs from the component (and the pyIndego library) in your log file, specify these options in your configuration file:

``` yaml
#configuration.yaml
logger:
  logs: 
    custom_components.indego: debug
    pyIndego: debug
```

## Supported models
As known today the following models are supported:
* Indego 1000
* Indego 1100
* Indego 1200
* Indego 10C
* Indego 13C
* Indego 350
* Indego 400
* Indego S+ 350 1gen
* Indego S+ 350 2gen
* Indego S+ 400 1gen
* Indego S+ 400 2gen
* Indego S+ 500
* Indego M+ 700 1gen
* Indego M+ 700 2gen

## Contribution
If you experience any readings from your mower that the sensor does not read out correct (could be Alerts or mower state), please dont hesitate to write an issue. I need your input in order to make this component as useful as possible. All suggestions are welcome!

## Known issues
* A special [Chrome plugin](#installing-the-chrome-extension) is required to complete the account linking in HomeAssistant.
* The Bosch Cloud (running on Azure) might block this integration from time to time. You might see HTTP 4XX errors like 'The connection to the Bosch Indego API failed!'. This might happen during component setup or during state updates. In that case you might be able to workaround the issue by changing the user agent (during initial component setup or for existing components under Settings > Devices & services > Bosch Indego Mower > Configure).
* You might see HTTP 5XX errors from time to time (most of time once a day). In that case there is a problem on the Bosch Cloud side which is temporary unavailable.
* HTTP 5XX errors can also occur right after you have sent an impossible command to the mower. Like docking the mower while it's already docked. 

## New issues
If you experience issues/bugs with this the best way to report them is to open an issue in **this** repo.

[Issue link](https://github.com/sander1988/Indego/issues)


## Credits

### Thanks to
[Eduard](https://github.com/eavanvalkenburg)
[Jumper78](https://github.com/Jumper78)
[dykandDK](https://github.com/dykandDK)
[ultrasub](https://github.com/UltraSub)
[Gnol86](https://github.com/Gnol86)
naethan bekkm onkelfarmor ltjessem nsimb jjandersson
[Shamshala](https://github.com/Shamshala)
nath
[bekkm](https://github.com/bekkm)
[urbatecte](https://github.com/urbatecte)
[Windmelodie](https://github.com/Windmelodie)
[Fuempel](https://github.com/Fuempel)
[MagaliDB](https://github.com/MagaliDB)
[mhosse](https://github.com/mhosse)
[Promises](https://github.com/Pr0mises)
[Sander1988](https://github.com/sander1988)

Fork from iMarkus/Indego https://github.com/iMarkus/Indego

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller

<a href="https://www.buymeacoffee.com/jm73" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
