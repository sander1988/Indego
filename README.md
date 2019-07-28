# Indego
Home Assistant Custom Component for Bosch Indego Lawn Mower

Place the files in custom-component in your Home Assistant folder for custom-componentes

    config/custom_components
    
Add the sensor to your configuration.yaml

    sensor:
      - platform: indego
        name: Mower name
        username: !secret indego_username
        password: !secret indego_password
        id: !secret indego_id

Add your account (usually mail address), password and serial number to secrets.yaml: 

    indego_username: name@mail.com
    indego_password: mysecretpw
    indego_id: 123456789
    
Debugging:

    logger:
      default: error
      logs:
        custom_components.indego: debug

Credits:

Fork from iMarkus/Indego (thanks for the inspiration and all your work with the basics!)

Inspiration from http://grauonline.de/wordpress/?page_id=219

Inspiration from https://github.com/jofleck/iot-device-bosch-indego-controller
