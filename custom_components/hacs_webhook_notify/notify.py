"""Notify platform for Webhook Notify."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    NotifyEntity,
    NotifyEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template

from .const import (
    CONF_WEBHOOK_URL,
    CONF_HEADERS,
    CONF_AUTH_TOKEN,
    CONF_PAYLOAD_TEMPLATE,
    CONF_NAME,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Webhook Notify platform."""
    async_add_entities([WebhookNotifyEntity(hass, entry)])


class WebhookNotifyEntity(NotifyEntity):
    """Notification entity that sends messages via HTTP POST webhook."""

    _attr_has_entity_name = True
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        config = entry.data

        self._hass = hass
        self._webhook_url = config.get(CONF_WEBHOOK_URL, "")
        self._auth_token = config.get(CONF_AUTH_TOKEN, "")
        self._payload_template: Template | None = None
        self._custom_headers: dict[str, str] = {}

        self._attr_name = config.get(CONF_NAME, DEFAULT_NAME) or DEFAULT_NAME
        self._attr_unique_id = f"{entry.entry_id}_notify"

        template_str = config.get(CONF_PAYLOAD_TEMPLATE, "")
        if template_str:
            self._payload_template = Template(template_str, hass)

        headers_str = config.get(CONF_HEADERS, "")
        if headers_str:
            try:
                self._custom_headers = json.loads(headers_str)
            except json.JSONDecodeError:
                _LOGGER.warning("Invalid headers JSON, ignoring custom headers")

    def _build_headers(self, extra_headers: dict | None = None) -> dict[str, str]:
        """Build request headers."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        headers.update(self._custom_headers)
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _build_payload(
        self, message: str, title: str | None = None, data: dict | None = None
    ) -> dict:
        """Build the default JSON payload."""
        payload: dict[str, Any] = {"message": message}
        if title:
            payload["title"] = title
        if data:
            payload["data"] = data
        return payload

    async def async_send_message(self, message: str, **kwargs: Any) -> None:
        """Send a message via webhook."""
        # HA 2024.4+ passes title and data via kwargs, older versions via ATTR_*
        data = kwargs.get("data") or kwargs.get(ATTR_DATA) or {}
        title = kwargs.get("title") or kwargs.get(ATTR_TITLE) or ""
        title = title.strip() or "通知"

        # Extract optional overrides from data
        url = data.pop("url", self._webhook_url)
        extra_headers = data.pop("headers", None)
        override_payload = data.pop("payload", None)

        headers = self._build_headers(extra_headers)

        if override_payload is not None:
            payload = override_payload
        elif self._payload_template is not None:
            try:

                def _json_escape(s: str) -> str:
                    """Escape newline/quote/etc for safe embedding in JSON."""
                    return json.dumps(s)[1:-1]

                rendered = self._payload_template.async_render(
                    {
                        "message": _json_escape(message),
                        "title": _json_escape(title),
                        "data": data,
                    }
                )
                payload = json.loads(str(rendered))
            except Exception as err:
                _LOGGER.error("Payload template render failed: %s", err)
                return
        else:
            payload = self._build_payload(message, title, data)

        _LOGGER.debug("Sending webhook to %s: %s", url, payload)

        session = async_get_clientsession(self._hass)
        try:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    _LOGGER.error(
                        "Webhook failed [%s] %s: %s", resp.status, url, body[:500]
                    )
                else:
                    _LOGGER.debug("Webhook sent [%s] %s", resp.status, url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Webhook error %s: %s", url, err)
