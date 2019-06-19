# Indego
Fork from iMarkus/Indego

Home Assistant Custom Component for Bosch Indego Lawn Mower

Place the indego.py in

    config/custom_components/sensor
    
Add new platform to your configuration.yaml

    - platform: indego
      host: api.indego.iot.bosch-si.com
      port: 443
      username: !secret indego_username
      password: !secret indego_password
      id: !secret indego_id

Add your account (usually mail address), password and serial number to secrets.yaml or directly in configuration.yaml. 

    indego_username: x.y@mail.com
    indego_password: mysecretpw
    indego_id: 123456789

Finally add your new sensor called indego_state: 

    sensor.indego_state

Debugging:

    logger:
      default: error
      logs:
        custom_components.sensor.indego: debug
