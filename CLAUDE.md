# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Home Assistant (HACS) 自定义集成，通过 HTTP POST (Webhook) 发送通知消息。支持 UI 配置、内置消息模板预设（企业微信/钉钉/Slack/Discord）、Jinja2 自定义模板、多实例。

## 架构

```
custom_components/hacs_webhook_notify/
├── __init__.py          # 入口：async_forward_entry_setups → notify 平台
├── config_flow.py       # 配置流：URL、名称、Token、Headers、模板预设
├── const.py             # 常量 + TEMPLATE_PRESETS（内置模板）
├── notify.py            # NotifyEntity → HTTP POST JSON
├── manifest.json        # 集成元数据
├── strings.json         # 翻译源文件（英文）
└── translations/
    ├── en.json           # 英文翻译
    └── zh-Hans.json      # 简体中文翻译
```

### 核心数据流

1. **配置**：用户在 HA UI 填写 Webhook URL → config_flow 校验 URL scheme / Headers JSON / 模板 → 创建 ConfigEntry → `entry.data`
2. **加载**：`__init__.py` → `async_forward_entry_setups(entry, [Platform.NOTIFY])` → HA 调用 `notify.py` 的 `async_setup_entry` → `async_add_entities`
3. **发送通知**：调用 `notify.<name>` → `WebhookNotifyEntity.async_send_message(**kwargs)` → 模板渲染（如有）→ HTTP POST JSON
4. **运行时覆盖**：`data.url` / `data.headers` / `data.payload` 可动态覆盖（优先级最高）

### Payload 优先级

```
data.payload 覆盖  >  消息模板渲染  >  默认 {message, title, data}
```

## 关键设计决策

- **NotifyEntity 架构**（HA 2024.4+）：使用 `NotifyEntity` + `async_forward_entry_setups`，不再使用遗留的 `BaseNotificationService` + `discovery.async_load_platform`
- **`_attr_supported_features = NotifyEntityFeature.TITLE`**：声明后 HA UI 自动显示 title 输入框
- **title 默认值 "通知"**：`async_send_message` 入口处 `title.strip() or "通知"`，模板和默认路径均生效
- **内置模板预设**：`const.py` → `TEMPLATE_PRESETS`，config_flow 下拉选择。预设只决定模板格式，不影响服务名称
- **服务名称支持中文**：`NotifyEntity` 架构下中文名称可在 HA UI 正常显示
- **多实例支持**：同一预设可多次添加（配不同 URL、不同群），服务名由用户自由命名区分
- **零外部依赖**：仅用 HA 内置 `aiohttp`，通过 `async_get_clientsession(hass)` 获取共享 session
- **异常不透传**：`aiohttp.ClientError` / `asyncio.TimeoutError` catch 后记日志，不中断自动化
- **超时控制**：`aiohttp.ClientTimeout(total=10)` 10 秒总超时

## 开发注意事项（踩坑记录）

### HA 2026 兼容性

- **`Template.async_render()` 返回 `Wrapper` 对象**：HA 2026 不再返回纯字符串，`json.loads()` 前必须 `str(rendered)`
- **`BaseNotificationService` 已移除**：HA 2026.7 中 `discovery.async_load_platform` 加载 notify 平台会静默失败（"Config entry was never loaded"），必须用 `NotifyEntity`

### 模板渲染

- **消息含换行/特殊字符需 JSON 转义**：模板变量 `{{ message }}` 插入原始字符串会破坏 JSON 结构。传入前需 `json.dumps(s)[1:-1]` 预处理换行、引号、反斜杠等
- **模板预设校验**：config_flow 提交时用测试数据渲染模板 → `json.loads(str(rendered))` 验证合法性

### UI 开发

- **title 输入框可见性**：不加 `NotifyEntityFeature.TITLE` 时 HA UI 不显示 title 字段，用户需切 YAML 模式才能填
- **`vol.In` 的 label 直接显示**：预设下拉的选项名不走翻译文件，直接在 `vol.In` 的 dict 里写中文 label
- **config_flow 中 `name` 字段**：当用户选了预设且不填名称时，名称为 `DEFAULT_NAME`（"webhook"），会被 HA slugify

## 开发命令

无测试、无构建步骤。直接将 `custom_components/hacs_webhook_notify/` 放置到 HA 的 `custom_components/` 下，重载集成即可。

- **本地调试**：HA 中通过 UI 添加集成（设置 → 设备与服务 → 添加集成 → 搜索 "Webhook Notify"）
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

## 文件注意事项

- `notify.py` 平台入口必须命名为 `async_setup_entry(hass, entry, async_add_entities)` — HA 按此名称查找 notify 平台
- `config_flow.py` 的 `VERSION` 用于 config entry 迁移，变更 `entry.data` 结构时必须递增并添加 `async_migrate_entry`
- `strings.json` 是翻译源文件，`translations/` 下是运行时副本，**修改时两边同步**
- `hacs.json` 中 `"content_in_root": false` 表示文件在 `custom_components/` 子目录
- 使用 `async_get_clientsession(self._hass)` 获取 session，**不要**手动创建 `aiohttp.ClientSession`
- `NotifyEntity` 的 `async_send_message` 用 `**kwargs` 接收参数以兼容不同 HA 版本（title/data 可能通过 kwargs 或 ATTR_* 传递）
