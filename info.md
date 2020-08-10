{% if prerelease %}
### NB!: This is a Beta version!
{% endif %}
# Bosch Indego Mower
![Screenshot](https://github.com/jm-73/Indego/blob/master/doc/0-Sensors_3.png)

You can add this component to Home Assistant via `configuration.yaml` file.

## Minimal configuration
```yaml
#configuration.yaml
indego:
  name:     Indego
  username: !secret indego_username
  password: !secret indego_password
```

Add your credentials used with Bosch Mower app (mail address, password and mower serial number) to your secrets.yaml:
```yaml
#secrets.yaml
indego_username: name@mail.com
indego_password: mysecretpw
```