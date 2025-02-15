"""The OwnerRez integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_TOKEN, CONF_USERNAME


from .const import DOMAIN, CONF_DAYS
from .api import OwnerRes

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OwnerRez from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # 1. Create API instance
    config = entry.data
    MyAPI = OwnerRes(
        config.get(CONF_USERNAME), config.get(CONF_API_TOKEN), config.get(CONF_DAYS)
    )
    # TODO 2. Validate the API connection (and authentication)
    # 3. Store an API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = MyAPI

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
