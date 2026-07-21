"""Webhook Notify integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Webhook Notify from a config entry."""
    config = dict(entry.data)
    config["entry_id"] = entry.entry_id

    await discovery.async_load_platform(
        hass,
        Platform.NOTIFY,
        DOMAIN,
        config,
        {},
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, [Platform.NOTIFY]
    )
