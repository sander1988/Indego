import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)


class IndegoEntity(RestoreEntity):
    """Base class for Indego entities."""

    def __init__(self, entity_id, name, icon, attributes, device_info: DeviceInfo):
        self.entity_id = entity_id
        self._unique_id = entity_id
        self._name = name

        self._icon = icon
        if icon is not None:
            self._updateble_icon = callable(icon)
            if self._updateble_icon:
                self._icon_func = icon
                self._icon = None

        self._attr = {key: None for key in attributes} if attributes is not None else None
        self._device_info = device_info
        self._state = None
        self._should_poll = False

    @callback
    def _schedule_immediate_update(self):
        """Schedule update."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    @property
    def icon(self):
        """Return the icon for the frontend based on the status."""
        return self._icon

    @property
    def extra_state_attributes(self) -> dict:
        """Return attributes."""
        return self._attr

    def add_attributes(self, attr: dict):
        """Update attributes."""
        self._attr.update(attr)

    def set_attributes(self, attr: dict):
        """Update attributes."""
        self._attr = attr

    def clear_attributes(self):
        """Clear attributes."""
        self._attr = None

    @property
    def unique_id(self) -> str:
        """Get unique_id."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return self._device_info
