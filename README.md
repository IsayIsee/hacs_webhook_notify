# Webhook Notify for Home Assistant

通过 HTTP POST (Webhook) 发送通知消息的 Home Assistant 自定义集成。完全通过 UI 界面配置，无需编辑 YAML 文件。

## 功能

- 🔔 将 Home Assistant 通知通过 Webhook HTTP POST 转发到任意服务
- 🖥️ 纯 UI 配置，无需手动编辑 YAML
- 🔑 支持 Bearer Token 认证
- 📋 支持自定义 HTTP 请求头（JSON 格式）
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
     | **Webhook URL** | ✅ | 接收通知的 HTTP 端点，必须以 `http://` 或 `https://` 开头 |
     | **服务名称** | ❌ | 用于区分多个 webhook 实例，默认为 "webhook" |
     | **认证令牌** | ❌ | 若填写，自动添加 `Authorization: Bearer <token>` 请求头 |
     | **自定义请求头** | ❌ | JSON 格式的额外 HTTP 头，如 `{"X-Custom": "value"}` |
4. 点击 **提交**

## 使用

### 基本用法

```yaml
service: notify.hacs_webhook_notify
data:
  message: "这是一条测试消息"
  title: "通知标题"
```

### 带附加数据

```yaml
service: notify.hacs_webhook_notify
data:
  message: "传感器触发告警"
  title: "⚠️ 告警"
  data:
    priority: high
    sensor: motion_sensor_1
    value: "检测到移动"
```

### 运行时覆盖

可在调用时动态修改 webhook URL、请求头和消息体：

```yaml
service: notify.hacs_webhook_notify
data:
  message: "发送到另一个 webhook"
  data:
    url: "https://another-service.com/hook"
    headers:
      X-API-Key: "my-api-key"
    payload:
      text: "自定义消息格式"
      channel: "#alerts"
```

### 自动化示例

```yaml
automation:
  - alias: "门铃通知"
    trigger:
      - platform: state
        entity_id: binary_sensor.doorbell
        to: "on"
    action:
      - service: notify.hacs_webhook_notify
        data:
          title: "🔔 门铃"
          message: "有人按门铃！"
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

| 服务 | Webhook URL 格式 | 说明 |
| --- | --- | --- |
| 企业微信机器人 | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx` | 消息格式需用运行时覆盖 |
| 钉钉机器人 | `https://oapi.dingtalk.com/robot/send?access_token=xxx` | 消息格式需用运行时覆盖 |
| Slack | `https://hooks.slack.com/services/xxx` | 消息格式需用运行时覆盖 |
| Discord | `https://discord.com/api/webhooks/xxx` | 消息格式需用运行时覆盖 |
| 自建服务 | `https://your-server.com/hook` | 直接兼容 JSON 格式 |
| Node-RED | `http://node-red:1880/endpoint` | 直接兼容 JSON 格式 |

> **核心技巧**：这些平台不接受默认的 `{"message":"...","title":"..."}` 格式，需要通过 `data.payload` 字段覆盖整个请求体，直接发送平台要求的 JSON 结构。

### 企业微信机器人

```yaml
# 文本消息
service: notify.hacs_webhook_notify
data:
  message: "这条内容不会出现在请求中"
  data:
    payload:
      msgtype: text
      text:
        content: "警报：传感器检测到异常温度！"

# Markdown 消息
service: notify.hacs_webhook_notify
data:
  message: ""
  data:
    payload:
      msgtype: markdown
      markdown:
        content: |
          ## ⚠️ 温度告警
          > 当前温度：**38.5°C**
          > 阈值：36.0°C
          > 请及时检查空调设备
```

### 钉钉机器人

```yaml
service: notify.hacs_webhook_notify
data:
  message: ""
  data:
    payload:
      msgtype: markdown
      markdown:
        title: "⚠️ 告警通知"
        text: |
          ### 传感器触发告警
          - 传感器：`motion_sensor_1`
          - 状态：检测到移动
          - 时间：{{ now().strftime('%H:%M:%S') }}
```

### Slack

```yaml
service: notify.hacs_webhook_notify
data:
  message: ""
  data:
    payload:
      text: "传感器触发告警！"
      blocks:
        - type: header
          text:
            type: plain_text
            text: "⚠️ 告警"
        - type: section
          text:
            type: mrkdwn
            text: |
              *传感器:* `motion_sensor_1`
              *状态:* 检测到移动
              *时间:* {{ now().strftime('%Y-%m-%d %H:%M') }}
```

### Discord

```yaml
service: notify.hacs_webhook_notify
data:
  message: ""
  data:
    payload:
      content: "<@&role_id> 传感器告警！"
      embeds:
        - title: "⚠️ 温度告警"
          description: "当前温度超出安全阈值"
          color: 16711680
          fields:
            - name: "传感器"
              value: "`temp_sensor_1`"
            - name: "当前温度"
              value: "**38.5°C**"
          footer:
            text: "Home Assistant • {{ now().strftime('%Y-%m-%d %H:%M') }}"

## 许可证

MIT License
