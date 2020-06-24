"""Class for Indego Sensors."""
import logging
from datetime import datetime

from homeassistant.components.sensor import ENTITY_ID_FORMAT as SENSOR_FORMAT
from homeassistant.const import CONF_ID, TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_UPDATED, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the sensor platform."""
    async_add_devices(
        [
            device
            for device in hass.data[DOMAIN].entities.values()
            if isinstance(device, IndegoSensor)
        ]
    )
    return True


class IndegoSensor(RestoreEntity):
    """Class for Indego Sensors."""

    def __init__(
        self, serial, entity_id, name, icon, device_class, unit_of_measurement
    ):
        """Initialize a sensor.

        Args:
            serial (str): serial of the mower
            entity_id (str): entity_id of the sensor
            name (str): name of the sensor
            icon (str, Callable): string or function for icons
            device_class (str): device class of the sensor
            unit_of_measurement (str): unit of measurement of the sensor

        """
        self._serial = serial
        self.entity_id = SENSOR_FORMAT.format(entity_id)
        self._unique_id = entity_id
        self._name = name
        self._updateble_icon = callable(icon)
        if self._updateble_icon:
            self._icon_func = icon
            self._icon = icon(None)
        else:
            self._icon = icon
        self._device_class = device_class
        self._unit = unit_of_measurement
        self._state = None
        self._attr = {}
        self._should_poll = False

    async def async_added_to_hass(self):
        """Once the sensor is added, see if it was there before and pull in that state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is not None and state.state is not None:
            self.state = state.state
        else:
            return
        async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )

    @callback
    def _schedule_immediate_update(self):
        """Schedule update."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    @property
    def state(self):
        """Get the state."""
        return self._state

    @state.setter
    def state(self, new):
        """Set the state to new."""
        if self._state != new:
            self._state = new
            if self._updateble_icon:
                self._icon = self._icon_func(self._state)
            self.async_schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Get unique_id."""
        return self._unique_id

    @property
    def device_state_attributes(self) -> dict:
        """Return attributes."""
        return self._attr

    def add_attribute(self, attr: dict):
        """Update attributes."""
        self._attr.update(attr)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit

    # @property
    # def device_info(self) -> dict:
    #     """Return the device_info."""
    #     return {
    #         "identifiers": {(DOMAIN, self._serial)},
    #         "name": self.name,

    #         "Model": self._IAPI.generic_data.model_description,
    #         "Serial": self._IAPI.generic_data.alm_sn,
    #         "Firmware": self._IAPI.generic_data.alm_firmware_version,
    #         "via_device": (DOMAIN, self._serial),
    #     }


# class IndegoStateSensor(Entity):
#     def __init__(self, IAPI, device_label):
#         _LOGGER.debug("Indego State Sensor setup!")
#         _LOGGER.debug(f"device Label : {device_label}")
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label
#         _LOGGER.debug(f"state : {self._IAPI.state.state}")
#         _LOGGER.debug(f"state_description : {self._IAPI.state_description}")

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI.state_description

#     @property
#     def icon(self):
#         return "mdi:robot"

#     @property
#     def device_state_attributes(self):
#         return {
#             "Model": self._IAPI.generic_data.model_description,
#             "Serial": self._IAPI.generic_data.alm_sn,
#             "Firmware": self._IAPI.generic_data.alm_firmware_version,
#         }


# class IndegoStateSensorDetail(Entity):
#     def __init__(self, IAPI, device_label):
#         _LOGGER.debug("Indego State Sensor Detail setup!")
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label
#         _LOGGER.debug(f"state : {self._IAPI.state.state}")
#         _LOGGER.debug(f"state_description2 : {self._IAPI.state_description}")
#         _LOGGER.debug(f"state_detail : {self._IAPI.state_description_detail}")

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI.state_description_detail

#     @property
#     def icon(self):
#         return "mdi:robot"

#     @property
#     def device_state_attributes(self):
#         return {
#             "State #": self._IAPI.state.state,
#             "State description": self._IAPI.state_description_detail,
#             "Model #": self._IAPI.generic_data.bareToolnumber,
#         }


# class IndegoBattery(Entity):
#     def __init__(self, IAPI, device_label):
#         _LOGGER.debug("Indego Battery Sensor setup!")
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label
#         # self._battery_percent_max   = self._IAPI._battery_percent
#         # self._battery_percent_min   = self._IAPI._battery_percent
#         _LOGGER.debug(
#             f"percent_adjusted: {self._IAPI.operating_data.battery.percent_adjusted}"
#         )

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def unit_of_measurement(self):
#         return "%"

#     @property
#     def state(self):
#         return self._IAPI.operating_data.battery.percent_adjusted

#     @property
#     def icon(self):
#         tmp_icon = "mdi:battery-50"
#         return tmp_icon

#     @property
#     def device_state_attributes(self):
#         return {
#             "Voltage": str(self._IAPI.operating_data.battery.voltage) + " V",
#             "Discharge": str(self._IAPI.operating_data.battery.discharge) + " Ah",
#             "Cycles": str(self._IAPI.operating_data.battery.cycles),
#             "Battery temp": str(self._IAPI.operating_data.battery.battery_temp)
#             + " "
#             + TEMP_CELSIUS,
#             "Ambient temp": str(self._IAPI.operating_data.battery.ambient_temp)
#             + " "
#             + TEMP_CELSIUS,
#         }


# class IndegoLawnMowedSensor(Entity):
#     def __init__(self, IAPI, device_label):
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def unit_of_measurement(self):
#         return "%"

#     @property
#     def icon(self):
#         return "mdi:percent"

#     @property
#     def state(self):
#         return self._IAPI.state.mowed

#     @property
#     def device_state_attributes(self):
#         return {
#             "Last session Operation": str(self._IAPI.state.runtime.session.operate)
#             + " min",
#             "Last session Cut": str(self._IAPI.state.runtime.session.cut) + " min",
#             "Last session Charge": str(self._IAPI.state.runtime.session.charge)
#             + " min",
#             "Last completed Mow": str(self._IAPI.last_completed_mow),
#             "Next Mow": str(self._IAPI.next_mow),
#         }


# class IndegoLastCompletedMowSensor(Entity):
#     def __init__(self, IAPI, device_label):
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def icon(self):
#         return "mdi:cash-100"

#     @property
#     def state(self):
#         return self._IAPI.last_completed_mow


# class IndegoNextMowSensor(Entity):
#     def __init__(self, IAPI, device_label):
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def icon(self):
#         return "mdi:chevron-right"

#     @property
#     def state(self):
#         return self._IAPI.next_mow

#     def should_poll(self):
#         """Return True if entity has to be polled for state.
#         False if entity pushes its state to HA.
#         """
#         return False


# class IndegoMowingMode(Entity):
#     def __init__(self, IAPI, device_label):
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI.generic_data.mowing_mode_description

#     @property
#     def icon(self):
#         tmp_icon = "mdi:alpha-m-circle-outline"
#         return tmp_icon


# class IndegoRuntimeTotal(Entity):
#     def __init__(self, IAPI, device_label):
#         self._mower = IndegoHub
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI.state.runtime.total.operate

#     @property
#     def unit_of_measurement(self):
#         return "h"

#     @property
#     def icon(self):
#         tmp_icon = "mdi:information-outline"
#         return tmp_icon

#     @property
#     def device_state_attributes(self):
#         return {
#             "Total operation time": str(self._IAPI.state.runtime.total.operate) + " h",
#             "Total mowing time": str(self._IAPI.state.runtime.total.cut) + " h",
#             "Total charging time": str(self._IAPI.state.runtime.total.charge) + " h",
#         }


# class IndegoAlertSensor(Entity):
#     def __init__(self, IAPI, device_label):
#         self._IAPI = IAPI
#         self._state = None
#         self._device_label = device_label

#     @property
#     def name(self):
#         return self._device_label

#     @property
#     def state(self):
#         return self._IAPI.alerts_count

#     @property
#     def icon(self):
#         tmp_icon = "mdi:check-circle-outline"
#         if self.state:
#             if self.state > 0:
#                 tmp_icon = "mdi:alert-outline"
#             else:
#                 tmp_icon = "mdi:check-circle-outline"
#         return tmp_icon


#    @property
#    def device_state_attributes(self):
#        if (self._IAPI._alert3_time != None ):
#            return {
#                "ID: " + self._IAPI._alert1_id: str(self._IAPI._alert1_error),
#                self._IAPI._alert1_time: str(self._IAPI._alert1_friendly_description),
#                "ID: " + self._IAPI._alert2_id: str(self._IAPI._alert2_error),
#                self._IAPI._alert2_time: str(self._IAPI._alert2_friendly_description),
#                "ID: " + self._IAPI._alert3_id: str(self._IAPI._alert3_error),
#                self._IAPI._alert3_time: str(self._IAPI._alert3_friendly_description)
#            }
#        else:
#            if (self._IAPI._alert2_time != None ):
#                return {
#                    "ID: " + self._IAPI._alert1_id: str(self._IAPI._alert1_error),
#                    self._IAPI._alert1_time: str(self._IAPI._alert1_friendly_description),
#                    "ID: " + self._IAPI._alert2_id: str(self._IAPI._alert2_error),
#                    self._IAPI._alert2_time: str(self._IAPI._alert2_friendly_description)
#                }
#            else:
#                if (self._IAPI._alert1_time != None ):
#                    return {
#                        "ID: " + self._IAPI._alert1_id: str(self._IAPI._alert1_error),
#                        self._IAPI._alert1_time: str(self._IAPI._alert1_friendly_description),
#                    }
#
# End of sensor.py
