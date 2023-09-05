import logging
import time

from homeassistant.components.camera import (
    Camera,
    ENTITY_ID_FORMAT as CAMERA_SENSOR_FORMAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .mixins import IndegoEntity


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the camera platform."""
    async_add_entities(
        [
            entity
            for entity in hass.data[DOMAIN][config_entry.entry_id].entities.values()
            if isinstance(entity, IndegoCamera)
        ]
    )


class IndegoCamera(IndegoEntity, Camera):

    def __init__(self, entity_id, name, device_info: DeviceInfo, indego_hub):
        IndegoEntity.__init__(self, CAMERA_SENSOR_FORMAT.format(entity_id), name, "mdi:image", None, device_info)
        Camera.__init__(self)
        self._indego_hub = indego_hub
        self._last_update_time = 0
        self._svg_map = None
        self.content_type = "image/svg+xml"

    @property
    def frame_interval(self) -> float:
        """Return the interval between frames of the mjpeg stream."""
        return 5.0

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        if self._svg_map is None or self.is_streaming and (time.time() - self._last_update_time) > self.frame_interval:
            _LOGGER.debug("Sync map")
            self._last_update_time = time.time()
            self._svg_map = await self._indego_hub.download_map(self._svg_map is None)
        return self._svg_map

    @Camera.is_streaming.setter
    def is_streaming(self, is_streaming: bool):
        if not is_streaming and self._attr_is_streaming:
            _LOGGER.debug("Streaming updated to %s, forcing reload of map", is_streaming)
            self._svg_map = None
        if self._attr_is_streaming != bool(is_streaming):
            self._attr_is_streaming = bool(is_streaming)
            self.async_write_ha_state()
