"""Config flow for Webhook Notify integration."""
from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.template import Template

from .const import (
    DOMAIN,
    CONF_WEBHOOK_URL,
    CONF_NAME,
    CONF_HEADERS,
    CONF_AUTH_TOKEN,
    CONF_PAYLOAD_TEMPLATE,
    CONF_TEMPLATE_PRESET,
    DEFAULT_NAME,
    TEMPLATE_PRESETS,
)


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

            # Validate service name: ASCII only (HA slugifies Chinese to pinyin)
            name_raw = user_input.get(CONF_NAME, "").strip()
            if name_raw and not all(ord(c) < 128 for c in name_raw):
                errors[CONF_NAME] = "invalid_name"

            # Validate custom headers JSON if provided
            headers_str = user_input.get(CONF_HEADERS, "").strip()
            if headers_str:
                try:
                    json.loads(headers_str)
                except json.JSONDecodeError:
                    errors[CONF_HEADERS] = "invalid_json"

            # Resolve payload template from preset or custom input
            template_preset = user_input.get(CONF_TEMPLATE_PRESET, "none")
            if template_preset == "custom":
                template_str = user_input.get(CONF_PAYLOAD_TEMPLATE, "").strip()
                if template_str:
                    try:
                        tmpl = Template(template_str, self.hass)
                        rendered = tmpl.async_render(
                            {"message": "test", "title": "test", "data": {}}
                        )
                        json.loads(str(rendered))
                    except Exception:
                        errors[CONF_PAYLOAD_TEMPLATE] = "invalid_template"
            elif template_preset in TEMPLATE_PRESETS:
                template_str = TEMPLATE_PRESETS[template_preset]["template"]
            else:
                template_str = ""

            if not errors:
                if template_preset in TEMPLATE_PRESETS:
                    name = TEMPLATE_PRESETS[template_preset]["name"]
                else:
                    name = name_raw if name_raw else DEFAULT_NAME
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_WEBHOOK_URL: webhook_url,
                        CONF_NAME: name,
                        CONF_AUTH_TOKEN: user_input.get(CONF_AUTH_TOKEN, "").strip(),
                        CONF_HEADERS: headers_str,
                        CONF_PAYLOAD_TEMPLATE: template_str,
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
                    vol.Optional(CONF_TEMPLATE_PRESET, default="none"): vol.In(
                        {
                            "none": "默认格式 (Default)",
                            "wecom_text": "企业微信 - 文本消息",
                            "wecom_markdown": "企业微信 - Markdown",
                            "dingtalk_text": "钉钉 - 文本消息",
                            "dingtalk_markdown": "钉钉 - Markdown",
                            "slack": "Slack",
                            "discord": "Discord",
                            "custom": "自定义 (Custom)",
                        }
                    ),
                    vol.Optional(CONF_PAYLOAD_TEMPLATE, default=""): str,
                }
            ),
            errors=errors,
        )
