import logging
import time
import asyncio
import aiofiles
import os
import re

from homeassistant.components.camera import (
    Camera,
    ENTITY_ID_FORMAT as CAMERA_SENSOR_FORMAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ENTITY_ONLINE, ENTITY_MOWER_STATE, CONF_MAP_ROTATION
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
    def __init__(
        self,
        entity_id,
        name,
        device_info: DeviceInfo,
        indego_hub,
        translation_key: str = None,
        entity_category=None,
    ):
        IndegoEntity.__init__(
            self,
            CAMERA_SENSOR_FORMAT.format(entity_id),
            name,
            "mdi:image",
            None,
            device_info,
        )
        Camera.__init__(self)
        self._indego_hub = indego_hub
        self._last_update_time = 0
        self._svg_map = None
        self._attr_is_streaming = False
        self._attr_translation_key = translation_key
        self._attr_entity_category = entity_category
        self.content_type = "image/svg+xml"
        self._mower_state = None

    @property
    def brand(self) -> str | None:
        """Return the brand of the camera."""
        return "Bosch"

    @property
    def model(self) -> str | None:
        """Return the model of the camera."""
        return "Indego"

    @property
    def is_on(self) -> bool:
        """Return True if camera is on (mower is online)."""
        try:
            online_state = self._indego_hub.entities[ENTITY_ONLINE].state
            return bool(online_state)
        except (KeyError, AttributeError):
            return False

    @property
    def is_streaming(self) -> bool:
        """Return True if camera is streaming (mower is actively mowing/moving)."""
        return self._attr_is_streaming

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await asyncio.sleep(3)
        await self.refresh_map("unknown")

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        if self._svg_map is None:
            svg_path = self._indego_hub.map_path()
            _LOGGER.debug("Camera: Loading lawn map from disk")
            if not os.path.exists(svg_path):
                _LOGGER.warning("Camera: Lawn map file not found - no image available")
                return None
            try:
                async with aiofiles.open(svg_path, "r") as f:
                    self._svg_map = await f.read()
            except Exception as e:
                _LOGGER.error("Camera: Failed to read lawn map file: %s", e)
                return None

        return self._svg_map.encode("utf-8")

    def update_streaming_state(self, is_streaming: bool) -> None:
        if not is_streaming and self._attr_is_streaming:
            _LOGGER.debug("Map reload triggered - mower movement detected")
            self._svg_map = None
        if self._attr_is_streaming != bool(is_streaming):
            self._attr_is_streaming = bool(is_streaming)
            self.async_write_ha_state()

    async def refresh_map(self, mower_state: str):
        """Refresh the lawn map and update streaming state based on mower state."""
        try:
            # Detect if mower is actively moving/mowing based on state
            # Mowing states are typically 500-799 or contain "mowing"/"moving" in description
            is_moving = self._is_mowing_state(mower_state)

            # Update streaming state - camera shows STREAMING when mower is moving
            if self._attr_is_streaming != is_moving:
                self._attr_is_streaming = is_moving
                _LOGGER.debug("Camera streaming state changed: %s (mower state: %s)", is_moving, mower_state)
                self.async_write_ha_state()

            svg_path = self._indego_hub.map_path()
            if not os.path.exists(svg_path):
                _LOGGER.debug("Camera: Lawn map file not yet available")
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

            # --- NEU: Karte um den eingestellten Winkel drehen ---
            rotation = self._indego_hub.config_entry.options.get(CONF_MAP_ROTATION, 0)
            if rotation:
                # ViewBox auslesen, um den Mittelpunkt für die Drehung zu berechnen
                viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_text)
                if viewbox_match:
                    parts = viewbox_match.group(1).split()
                    if len(parts) == 4:
                        x, y, w, h = map(float, parts)
                        cx = x + w / 2
                        cy = y + h / 2
                        center = f"{cx},{cy}"
                    else:
                        center = "50%,50%"
                else:
                    center = "50%,50%"

                # transform-Attribut zum <svg>-Tag hinzufügen (falls noch nicht vorhanden)
                svg_tag_match = re.search(r'(<svg[^>]*>)', svg_text)
                if svg_tag_match:
                    old_tag = svg_tag_match.group(1)
                    if 'transform=' not in old_tag:
                        new_tag = old_tag.rstrip('>') + f' transform="rotate({rotation}, {center})">'
                        svg_text = svg_text.replace(old_tag, new_tag, 1)

            self._svg_map = svg_text
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.debug("Camera: Error updating lawn map: %s", e)

    def _is_mowing_state(self, mower_state: str) -> bool:
        """Determine if mower is actively moving based on state.

        Mowing states in Indego:
        - 500-799: Active mowing states
        - States containing "mowing", "moving", "cutting" indicate active movement
        """
        if mower_state is None:
            return False

        state_str = str(mower_state).lower()

        # Check if state is in the mowing range (500-799)
        try:
            state_num = int(state_str)
            if 500 <= state_num <= 799:
                return True
        except (ValueError, TypeError):
            pass

        # Check for mowing-related keywords
        mowing_keywords = ['mowing', 'mow', 'cutting', 'cut', 'moving', 'drive']
        return any(keyword in state_str for keyword in mowing_keywords)
