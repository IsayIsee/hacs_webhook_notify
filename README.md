# Webhook Notify for Home Assistant

通过 HTTP POST (Webhook) 发送通知消息的 Home Assistant 自定义集成。完全通过 UI 界面配置，无需编辑 YAML 文件。

## 功能

- 🔔 将 Home Assistant 通知通过 Webhook HTTP POST 转发到任意服务
- 🖥️ 纯 UI 配置，无需手动编辑 YAML
- 🎨 **内置消息模板预设**：企业微信 / 钉钉 / Slack / Discord 一键选择，无需手动拼 JSON
- 🔑 支持 Bearer Token 认证
- 📋 支持自定义 HTTP 请求头和 Jinja2 消息模板
- 🔄 支持多个 Webhook 实例（不同服务名称区分）
- 🎯 运行时动态覆盖 URL、请求头和消息载荷

## 安装

### 方法一：手动安装

1. 将 `custom_components/hacs_webhook_notify/` 目录复制到 Home Assistant 配置目录的 `custom_components/` 下：

   ```
   <config_dir>/
   └── custom_components/
       └── hacs_webhook_notify/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── const.py
           ├── notify.py
           ├── strings.json
           └── translations/
               ├── en.json
               └── zh-Hans.json
   ```

2. 重启 Home Assistant

### 方法二：通过 HACS 安装（自定义仓库）

> **注意**：本集成尚未提交到 HACS 默认仓库，需以"自定义仓库"方式添加。

1. 在 Home Assistant 侧边栏打开 **HACS**
2. 进入 **集成** 页面，点击右上角 **⋮ → 自定义仓库**
3. 填入本仓库的 GitHub URL，类别选择 **集成 (Integration)**，点击 **添加**
4. 添加成功后，点击右下角 **+ 浏览并下载存储库**，搜索 "Webhook Notify" 并安装
5. 重启 Home Assistant

## 配置

1. 进入 **设置 → 设备与服务 → 添加集成**
2. 搜索 **"Webhook Notify"**
3. 填写配置表单：
     | 字段 | 必填 | 说明 |
     |------|------|------|
     | **Webhook URL** | ✅ | 目标 HTTP 端点，必须以 `http://` 或 `https://` 开头 |
     | **服务名称** | ❌ | 支持中文，如"消息推送-企业微信"。用于在自动化中区分各实例 |
     | **认证令牌** | ❌ | 自动添加 `Authorization: Bearer <token>` 请求头 |
     | **自定义请求头** | ❌ | JSON 格式额外 HTTP 头，如 `{"X-API-Key": "value"}` |
     | **消息模板预设** | ❌ | 下拉选择内置格式（企业微信/钉钉/Slack/Discord），选后自动套用 |
     | **自定义模板** | ❌ | 仅当预设选"自定义"时填写，JSON + Jinja2 格式 |
4. 点击 **提交**

## 使用

### 日常用法（已选模板预设）

配置时选择了"企业微信 - Markdown"等预设后，只需填 `message` 和 `title`，格式自动转换：

```yaml
service: notify.消息推送-企业微信    # 你配置的服务名
data:
  message: "传感器触发告警"
  title: "⚠️ 告警"
```

> **变量支持**：`message` 和 `title` 均支持 HA 模板变量：
> ```yaml
> message: |
>   机房: {{ states('sensor.temp_1') }}°C
>   PVE01: {{ states('sensor.temp_2') }}°C
>   空调进风: {{ states('sensor.temp_3') }}°C
> ```

### 运行时覆盖

需要临时换 URL 或自定义消息体时，通过 `data` 覆盖：

```yaml
service: notify.消息推送-企业微信
data:
  message: "紧急通知"
  data:
    url: "https://another-webhook.example.com/hook"    # 临时换 URL
    headers:                                            # 追加请求头
      X-Priority: "high"
    payload:                                            # 完全接管消息体
      msgtype: text
      text:
        content: "自定义格式消息"
```

### 自动化示例

```yaml
automation:
  - alias: "温度告警"
    trigger:
      - platform: numeric_state
        entity_id: sensor.miaomiaoce_t2_7644_temperature
        above: 35
    action:
      - service: notify.消息推送-企业微信
        data:
          title: "🌡️ 温度告警"
          message: |
            当前温度：{{ states('sensor.miaomiaoce_t2_7644_temperature') }}°C
            湿度：{{ states('sensor.miaomiaoce_t2_7644_humidity') }}%
```

### 多个 Webhook 实例

可以多次添加集成，每次配置不同的服务名称和 URL：

- 实例 1：名称 `office` → 调用 `notify.office`
- 实例 2：名称 `home` → 调用 `notify.home`

## Webhook 接收格式

插件发送的 HTTP POST 请求格式：

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token>    # 仅当配置了认证令牌
```

**Body:**
```json
{
  "message": "通知内容",
  "title": "通知标题",
  "data": {
    "priority": "high",
    "...": "..."
  }
}
```

## 测试 Webhook

可以使用以下方式快速测试 webhook 接收端：

### 使用 webhook.site

1. 打开 https://webhook.site
2. 复制生成的唯一 URL
3. 在集成配置中填入该 URL
4. 调用 notify 服务发送测试消息
5. 在 webhook.site 页面查看收到的请求

### 使用本地 echo server

```bash
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
        self.send_response(200)
        self.end_headers()
HTTPServer(('0.0.0.0', 8888), H).serve_forever()
"
```

然后将 webhook URL 配置为 `http://<HA_HOST>:8888/webhook`。

## 常见 Webhook 服务对接

**推荐方式**：添加集成时在"消息模板预设"下拉中选择对应服务即可，无需手写 JSON。

| 服务 | Webhook URL 格式 | 预设选项 |
| --- | --- | --- |
| 企业微信机器人 | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx` | 企业微信 - 文本 / Markdown |
| 钉钉机器人 | `https://oapi.dingtalk.com/robot/send?access_token=xxx` | 钉钉 - 文本 / Markdown |
| Slack | `https://hooks.slack.com/services/xxx` | Slack |
| Discord | `https://discord.com/api/webhooks/xxx` | Discord |
| 自建服务 | `https://your-server.com/hook` | 默认格式（直接兼容） |
| Node-RED | `http://node-red:1880/endpoint` | 默认格式（直接兼容） |

### 自定义模板（高级）

当预设不满足需求时，选择"自定义"预设，自行编写 JSON + Jinja2 模板。可用变量：`{{ message }}`、`{{ title }}`、`{{ data }}`。

```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "## {{ title }}\n> {{ message }}\n> 时间：{{ data.time }}"
  }
}
```

调用时：

```yaml
service: notify.自定义通知服务
data:
  title: "🌡️ 温度告警"
  message: "当前温度超出安全阈值"
  data:
    time: "{{ now().strftime('%H:%M:%S') }}"
```

## 许可证

Apache License 2.0
