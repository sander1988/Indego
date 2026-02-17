import logging
import time
import asyncio
import aiofiles
import os

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
        self._attr_is_streaming = False
        self.content_type = "image/svg+xml"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await asyncio.sleep(3)
        await self.refresh_map("unknown")

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        if self._svg_map is None:
            svg_path = self._indego_hub.map_path()
            _LOGGER.debug("Camera: loading map from file %s (fallback)", svg_path)
            if not os.path.exists(svg_path):
                _LOGGER.warning("Camera: SVG-File not available - no picture")
                return None
            try:
                async with aiofiles.open(svg_path, "r") as f:
                    self._svg_map = await f.read()
            except Exception as e:
                _LOGGER.error("Camera: Error during reading of SVG-File: %s", e)
                return None

        return self._svg_map.encode("utf-8")

    def update_streaming_state(self, is_streaming: bool) -> None:
        if not is_streaming and self._attr_is_streaming:
            _LOGGER.debug("Streaming updated to %s, forcing reload of map", is_streaming)
            self._svg_map = None
        if self._attr_is_streaming != bool(is_streaming):
            self._attr_is_streaming = bool(is_streaming)
            self.async_write_ha_state()

    async def refresh_map(self, mower_state: str):
        try:
            svg_path = self._indego_hub.map_path()
            if not os.path.exists(svg_path):
                _LOGGER.warning("Camera: SVG-File %s not present – no update", svg_path)
                return

            async with aiofiles.open(svg_path, "r") as f:
                svg_text = await f.read()

            svg_text = svg_text.replace('#FAFAFA', 'transparent').replace('#CCCCCC', 'transparent')

            xpos = getattr(self._indego_hub._indego_client.state, "svg_xPos", None)
            ypos = getattr(self._indego_hub._indego_client.state, "svg_yPos", None)

            if xpos is not None and ypos is not None:
                icon_path = "M1 14V5H13C18.5 5 23 9.5 23 15V17H20.83C20.42 18.17 19.31 19 18 19C16.69 19 15.58 18.17 15.17 17H10C9.09 18.21 7.64 19 6 19C3.24 19 1 16.76 1 14M6 11C4.34 11 3 12.34 3 14C3 15.66 4.34 17 6 17C7.66 17 9 15.66 9 14C9 12.34 7.66 11 6 11M15 10V12H20.25C19.92 11.27 19.5 10.6 19 10H15Z"
                symbol = (
                    f'<path d="{icon_path}" fill="#009688" stroke="#009688" '
                    f'stroke-width="1.5" transform="translate({xpos - 24} {ypos - 24}) scale(3.0)" />'
                )

                svg_text = svg_text.replace('<path id="mower"', '<!-- removed mower -->')
                svg_text = svg_text.replace("</svg>", symbol + "</svg>")

            self._svg_map = svg_text
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Camera: Error during map update: %s", e)
