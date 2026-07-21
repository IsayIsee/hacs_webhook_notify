"""Support for sending notifications via HTTP POST webhook.

This integration allows Home Assistant to forward notification messages
to external services (WeCom, DingTalk, Slack, Discord, etc.) by sending
HTTP POST requests with JSON payloads to user-configured webhook URLs.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Webhook Notify from a config entry.

    Forwards the config entry to the notify platform, which creates
    a NotifyEntity for each configured webhook instance.
    """
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.NOTIFY])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Removes the notify entity associated with this config entry.
    """
    return await hass.config_entries.async_unload_platforms(
        entry, [Platform.NOTIFY]
    )
