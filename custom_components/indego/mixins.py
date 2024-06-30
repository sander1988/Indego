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
        self._attr_connected_to_cloud = None
        self._should_poll = False

    @callback
    def async_write_ha_state(self) -> None:
        """Prevent write state calls when the entity is disabled."""
        if not self.enabled:
            _LOGGER.debug("%s is disabled, preventing HA state update", self.entity_id)
            return
        super().async_write_ha_state()

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

    def add_attributes(self, attr: dict, sync_state: bool = True):
        """Update attributes."""
        self._attr.update(attr)
        if sync_state:
            self.async_schedule_update_ha_state()

    def set_attributes(self, attr: dict, sync_state: bool = True):
        """Update attributes."""
        self._attr = attr
        if sync_state:
            self.async_schedule_update_ha_state()

    def clear_attributes(self, sync_state: bool = True):
        """Clear attributes."""
        if self._attr is not None:
            self._attr = None
            if sync_state:
                self.async_schedule_update_ha_state()

    def clear_attribute(self, key: str, sync_state: bool = True) -> bool:
        """Clear a single attribute."""
        if self._attr is None or key not in self._attr:
            return False

        del self._attr[key]
        if sync_state:
            self.async_schedule_update_ha_state()
        return True

    def set_cloud_connection_state(self, state: bool):
        """Set the cloud connection state."""
        if self._attr_connected_to_cloud != state:
            self._attr_connected_to_cloud = state
            self.async_schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Get unique_id."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return self._device_info

    @property
    def available(self) -> bool:
        """Return the availability state based on the Bosch cloud connection state."""
        if self._attr_connected_to_cloud is None:
            return True  # Availability state not used for this entity.
        return self._attr_connected_to_cloud
