"""Constants for the Webhook Notify integration."""

DOMAIN = "hacs_webhook_notify"

CONF_WEBHOOK_URL = "webhook_url"
CONF_NAME = "name"
CONF_HEADERS = "headers"
CONF_AUTH_TOKEN = "auth_token"
CONF_PAYLOAD_TEMPLATE = "payload_template"
CONF_TEMPLATE_PRESET = "template_preset"

DEFAULT_NAME = "webhook"

TEMPLATE_PRESETS = {
    "wecom_text": (
        '{"msgtype":"text","text":{"content":"{{ title }}\\n{{ message }}"}}'
    ),
    "wecom_markdown": (
        '{"msgtype":"markdown","markdown":{"content":"## {{ title }}\\n{{ message }}"}}'
    ),
    "dingtalk_text": (
        '{"msgtype":"text","text":{"content":"{{ title }}\\n{{ message }}"}}'
    ),
    "dingtalk_markdown": (
        '{"msgtype":"markdown","markdown":{"title":"{{ title }}","text":"{{ message }}"}}'
    ),
    "slack": (
        '{"text":"*{{ title }}*\\n{{ message }}"}'
    ),
    "discord": (
        '{"content":"**{{ title }}**\\n{{ message }}"}'
    ),
}

