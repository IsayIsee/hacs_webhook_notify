"""Constants for the Webhook Notify integration."""

DOMAIN = "hacs_webhook_notify"

# Config entry data keys
CONF_WEBHOOK_URL = "webhook_url"
CONF_NAME = "name"
CONF_HEADERS = "headers"
CONF_AUTH_TOKEN = "auth_token"
CONF_PAYLOAD_TEMPLATE = "payload_template"
CONF_TEMPLATE_PRESET = "template_preset"

DEFAULT_NAME = "webhook"

# Built-in message template presets for common webhook services.
# Each preset provides a JSON template string with Jinja2 placeholders
# ({{ message }}, {{ title }}, {{ data }}) that the component renders
# at notification time.
TEMPLATE_PRESETS = {
    "wecom_text": {
        "name": "WeCom Text",
        "template": (
            '{"msgtype":"text","text":{"content":"{{ title }}\\n{{ message }}"}}'
        ),
    },
    "wecom_markdown": {
        "name": "WeCom Markdown",
        "template": (
            '{"msgtype":"markdown","markdown":{"content":"## {{ title }}\\n{{ message }}"}}'
        ),
    },
    "dingtalk_text": {
        "name": "DingTalk Text",
        "template": (
            '{"msgtype":"text","text":{"content":"{{ title }}\\n{{ message }}"}}'
        ),
    },
    "dingtalk_markdown": {
        "name": "DingTalk Markdown",
        "template": (
            '{"msgtype":"markdown","markdown":{"title":"{{ title }}","text":"{{ message }}"}}'
        ),
    },
    "slack": {
        "name": "Slack",
        "template": (
            '{"text":"*{{ title }}*\\n{{ message }}"}'
        ),
    },
    "discord": {
        "name": "Discord",
        "template": (
            '{"content":"**{{ title }}**\\n{{ message }}"}'
        ),
    },
}
