"""Config flow for Webhook Notify integration."""
from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_WEBHOOK_URL, CONF_NAME, CONF_HEADERS, CONF_AUTH_TOKEN, DEFAULT_NAME


class WebhookNotifyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Webhook Notify."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate URL scheme
            webhook_url = user_input[CONF_WEBHOOK_URL].strip()
            if not webhook_url.startswith(("http://", "https://")):
                errors[CONF_WEBHOOK_URL] = "invalid_url"

            # Validate custom headers JSON if provided
            headers_str = user_input.get(CONF_HEADERS, "").strip()
            if headers_str:
                try:
                    json.loads(headers_str)
                except json.JSONDecodeError:
                    errors[CONF_HEADERS] = "invalid_json"

            if not errors:
                name = user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_WEBHOOK_URL: webhook_url,
                        CONF_NAME: name,
                        CONF_AUTH_TOKEN: user_input.get(CONF_AUTH_TOKEN, "").strip(),
                        CONF_HEADERS: headers_str,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_WEBHOOK_URL): str,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Optional(CONF_AUTH_TOKEN, default=""): str,
                    vol.Optional(CONF_HEADERS, default=""): str,
                }
            ),
            errors=errors,
        )
