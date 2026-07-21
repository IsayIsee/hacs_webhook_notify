# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Home Assistant (HACS) 自定义集成，通过 HTTP POST (Webhook) 发送通知消息。用户通过 UI 界面配置 webhook URL 等参数，无需编辑 YAML 文件。

## 架构

```
custom_components/hacs_webhook_notify/
├── __init__.py          # 入口：async_setup_entry → discovery.async_load_platform 加载 notify
├── config_flow.py       # 配置流：填写 webhook URL、名称、认证令牌、自定义请求头
├── const.py             # 常量：DOMAIN, CONF_WEBHOOK_URL, CONF_NAME 等
├── notify.py            # 通知服务：BaseNotificationService → HTTP POST 发送 JSON
├── manifest.json        # 集成元数据
├── strings.json         # 翻译源文件（英文）
└── translations/
    ├── en.json           # 英文翻译
    └── zh-Hans.json      # 简体中文翻译
```

### 核心数据流

1. **配置**：用户在 HA UI 中填写 Webhook URL → config_flow 校验 URL scheme + JSON → 创建 ConfigEntry → 存入 `entry.data`
2. **加载**：`__init__.py` 的 `async_setup_entry` → `discovery.async_load_platform` → HA 调用 `notify.py` 的 `get_service()` → 传入 `discovery_info`（含 entry.data）
3. **发送通知**：用户/自动化调用 `notify.hacs_webhook_notify` → `WebhookNotificationService.async_send_message()` → 通过 `async_get_clientsession` 获取 HA 共享 aiohttp session → HTTP POST JSON
4. **运行时覆盖**：调用时 `data.url` / `data.headers` / `data.payload` 可动态覆盖配置

### 关键设计决策

- **遗留 BaseNotificationService 模式**：与 `ha_wecom` 一致，使用 `discovery.async_load_platform` 加载 notify 平台（注意：2024.4+ 的新模式是 `NotifyEntity` + `async_forward_entry_setups`，本项目选择遗留模式以保证最大兼容性）
- **零外部依赖**：仅使用 HA 内置的 `aiohttp`，通过 `async_get_clientsession(hass)` 获取共享 session（复用连接池、SSL 上下文），绝不手动创建 `ClientSession`
- **无状态设计**：每个 `WebhookNotificationService` 实例持有自己的配置，无 `hass.data` 存储，卸载即清理。`async_unload_entry` 直接调用 `async_unload_platforms`
- **URL 校验在 config_flow 阶段**：验证 URL 必须以 `http://` 或 `https://` 开头，失败时在表单 URL 字段显示 "invalid_url" 错误
- **Headers JSON 校验在 config_flow 阶段**：若填写自定义请求头，提交时即校验，失败时在表单 headers 字段显示 "invalid_json" 错误
- **多实例支持**：不调用 `async_set_unique_id`，允许用户添加多个同 URL 的 webhook 实例。HA 自动通过 `_2` 后缀区分同名服务
- **异常不透传**：`aiohttp.ClientError` 和 `asyncio.TimeoutError` 被 catch 并记录日志，不中断调用方自动化。HTTP 4xx/5xx 仅记录 warning，不抛异常
- **超时控制**：`aiohttp.ClientTimeout(total=10)` — 10 秒总超时，平衡可靠性和响应性

## 开发命令

此项目无测试、无构建步骤。作为 HA 自定义组件，直接将 `custom_components/hacs_webhook_notify/` 目录放置于 HA 实例的 `custom_components/` 下即可加载。

- **本地调试**：在 HA 开发环境中启动 HA，通过 UI 添加集成（设置 → 设备与服务 → 添加集成 → 搜索 "Webhook Notify"）
- **测试 webhook 接收**：
  ```bash
  python3 -c "
  from http.server import HTTPServer, BaseHTTPRequestHandler
  import json
  class H(BaseHTTPRequestHandler):
      def do_POST(self):
          length = int(self.headers.get('Content-Length', 0))
          body = self.rfile.read(length)
          print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
          self.send_response(200); self.end_headers()
  HTTPServer(('0.0.0.0', 8888), H).serve_forever()
  "
  ```

### 兼容性

- 最低 HA 版本：无特殊限制（使用遗留 `BaseNotificationService` 模式，不依赖新 API）
- ConfigFlow VERSION = 1
- 无外部 PyPI 依赖

## 文件注意事项

- `notify.py` 的工厂函数必须命名为 `get_service`（非 `async_get_service`）— HA notify 组件按此名称查找。函数签名固定为 `(hass, config, discovery_info)`
- `config_flow.py` 的 `VERSION` 用于 config entry 迁移逻辑，变更 entry.data 结构时必须递增并添加 `async_migrate_entry`
- `__init__.py` 中 `discovery_info` 需要包含 `entry_id` — 用于 HA 内部关联服务与 config entry
- `strings.json` 是翻译源文件，`translations/en.json` 是运行时副本，两者内容应保持一致
- 使用 `async_get_clientsession(self._hass)` 获取 aiohttp session — 这是 HA 推荐做法，不要手动创建 `ClientSession` 并 close
- `send_message` vs `async_send_message`：`BaseNotificationService` 提供两者，本项目覆盖 `async_send_message` 进行原生异步 HTTP 调用（避免 `async_add_executor_job` 的开销）
