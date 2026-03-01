# ShadowGrid 开发文档索引

## 核心文档

- [README.md](./README.md) - 项目简介和快速开始
- [COMMANDS.md](./COMMANDS.md) - 命令使用手册
- [CHANGELOG.md](./CHANGELOG.md) - 版本变更日志

## API 文档

- [SERVER_API.md](./SERVER_API.md) - **服务端 HTTP API 参考**
  - 登录认证
  - 客户端列表
  - 命令发送
  - 结果获取

- [CLIENT_PROTOCOL.md](./CLIENT_PROTOCOL.md) - **客户端 WebSocket 协议规范**
  - 连接流程
  - 消息格式
  - 所有命令的详细说明
  - 完整代码示例

## 技术栈

- **服务端**: Python FastAPI + WebSocket
- **客户端**: Python WebSocket-client
- **打包**: PyInstaller

## 端口配置

- HTTPS: 8444
- WSS: 8444

## 完整示例

### 使用 Go 开发 Admin 客户端

参考 `SERVER_API.md`:

```go
package main

import (
    "encoding/base64"
    "encoding/json"
    "fmt"
    "net/http"
)

// 1. 登录
auth := base64.StdEncoding.EncodeToString([]byte("admin:admin123"))
req, _ := http.NewRequest("POST", "https://server:8444/login", nil)
req.Header.Set("Authorization", "Basic "+auth)
resp, _ := http.DefaultClient.Do(req)

// 2. 获取客户端列表
req, _ = http.NewRequest("GET", "https://server:8444/clients", nil)
resp, _ = http.DefaultClient.Do(req)
var data map[string]interface{}
json.NewDecoder(resp.Body).Decode(&data)

// 3. 发送命令
cmd := map[string]interface{}{
    "type": "ls",
    "payload": "/",
}
body, _ := json.Marshal(cmd)
req, _ = http.NewRequest("POST", fmt.Sprintf("https://server:8444/command/%s", clientID), 
    bytes.NewBuffer(body))
req.Header.Set("Content-Type", "application/json")
http.DefaultClient.Do(req)
```

### 使用 Node.js 开发 Client

参考 `CLIENT_PROTOCOL.md`:

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('wss://server:8444/ws/client-123', {
    rejectUnauthorized: false
});

ws.on('open', () => {
    ws.send(JSON.stringify({
        type: 'register',
        client_id: 'client-123',
        hostname: 'my-host'
    }));
});

ws.on('message', (data) => {
    const msg = JSON.parse(data);
    if (msg.type === 'command') {
        const result = handleCommand(msg.payload);
        ws.send(JSON.stringify({
            type: 'result',
            command_id: msg.id,
            result: result
        }));
    }
});

function handleCommand(cmd) {
    if (cmd.type === 'ls') {
        return {
            status: 'ok',
            result: getDirectoryList(cmd.payload),
            result_type: 'list'
        };
    }
    // ... other commands
}
```

## 目录结构

```
ShadowGrid/
├── server.py          # FastAPI 服务端
├── client.py          # Python 客户端
├── admin.py           # Python 管理终端
├── requirements.txt   # Python 依赖
├── SERVER_API.md      # 服务端 API 文档
├── CLIENT_PROTOCOL.md # 客户端协议文档
└── templates/         # Web 模板
    ├── index.html
    └── login.html
```

## 支持的语言

基于标准 HTTP/WebSocket 协议，可使用任何语言开发:
- Python
- Go
- Node.js
- Java
- C#
- Rust
- ...

## 许可证

GPL-3.0

## 作者

帅丘
