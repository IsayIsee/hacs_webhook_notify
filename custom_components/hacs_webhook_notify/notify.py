"""Notify platform for Webhook Notify."""
from __future__ import annotations

import asyncio
import json
import logging

import aiohttp

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_WEBHOOK_URL,
    CONF_HEADERS,
    CONF_AUTH_TOKEN,
    CONF_PAYLOAD_TEMPLATE,
)

_LOGGER = logging.getLogger(__name__)


def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> WebhookNotificationService | None:
    """Get the Webhook Notify service."""
    if discovery_info is None:
        return None
    return WebhookNotificationService(hass, discovery_info)


class WebhookNotificationService(BaseNotificationService):
    """Notification service that sends messages via HTTP POST webhook."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the service."""
        self._hass = hass
        self._webhook_url = config.get(CONF_WEBHOOK_URL, "")
        self._auth_token = config.get(CONF_AUTH_TOKEN, "")
        self._payload_template: Template | None = None
        self._custom_headers: dict[str, str] = {}

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
        """Build the JSON payload."""
        payload: dict[str, Any] = {"message": message}
        if title:
            payload["title"] = title
        if data:
            payload["data"] = data
        return payload

    async def async_send_message(self, message: str, **kwargs: Any) -> None:
        """Send a message via webhook."""
        data = kwargs.get(ATTR_DATA) or {}
        title = kwargs.get(ATTR_TITLE, "")

        # Extract optional overrides from data
        url = data.pop("url", self._webhook_url)
        extra_headers = data.pop("headers", None)
        override_payload = data.pop("payload", None)

        headers = self._build_headers(extra_headers)

        if override_payload is not None:
            payload = override_payload
        elif self._payload_template is not None:
            try:
                rendered = self._payload_template.async_render(
                    {
                        "message": message,
                        "title": title.strip() if title else message,
                        "data": data,
                    }
                )
                payload = json.loads(rendered)
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
