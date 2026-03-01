# ShadowGrid - 暗影矩阵

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org)

一个轻量级、安全的远程控制系统，用于合法授权的远程管理与运维监控。

> ⚠️ **法律声明**: 本项目仅供合法授权的本地网络管理使用。未经明确授权，请勿将本项目用于任何非法用途。开发者不承担因 misuse 造成的任何责任。

## 🚀 快速开始

### prerequisite

- Python 3.7+
- Windows/Linux/macOS

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务端

```bash
python server.py --admin-password your_password
```

服务端将监听端口 **8444** (HTTPS/WSS)，首次运行会自动生成 SSL 证书。

### 3. 启动客户端

```bash
python client.py
```

或直接运行打包的可执行文件：

```bash
shadowgrid-agent.exe
```

### 4. 启动管理终端

```bash
python admin.py
```

按提示输入服务器地址和密码即可开始管理。

## 📋 功能特性

| 功能 | 描述 |
|------|------|
| 🔒 加密通信 | HTTPS + WebSocket Secure (WSS) |
| 💻 命令执行 | 远程执行 Shell 命令 |
| 📁 文件管理 | 上传/下载/删除/移动/查找文件 |
| 📸 屏幕截图 | 远程桌面实时截图 |
| 📂 目录浏览 | 浏览远程文件系统 |

## 📖 命令列表

### 客户端支持的命令

| 命令 | 参数 | 描述 |
|------|------|------|
| `ls` | `[路径]` | 列出目录内容 |
| `cd` | `<路径>` | 切换当前目录 |
| `pwd` | 无 | 显示当前工作目录 |
| `cat` | `<文件>` | 显示文件内容 |
| `dl` | `<文件> [目录]` | 下载文件到本地 |
| `ud` | `<文件> [目录]` | 上传文件到远程 |
| `rm` | `<路径> [-r]` | 删除文件或目录 |
| `mv` | `<源> <目标>` | 移动或重命名 |
| `file` | `<路径>` | 查看文件类型 |
| `find` | `<模式> [-t 类型]` | 查找文件 |
| `shell` | `<命令>` | 执行系统命令 |
| `screenshot` | 无 | 截取远程屏幕 |

### 使用示例

```bash
# 列出目录
ls
ls C:\Users\Public

# 切换目录
cd Documents

# 查看文件内容
cat config.txt

# 下载文件
dl report.pdf
dl report.pdf C:\Downloads

# 上传文件
ud backup.zip
ud backup.zip /tmp

# 删除文件
rm temp.txt
rm old_project -r

# 移动/重命名
mv old.txt new.txt
mv file.txt C:\backup

# 查看文件类型
file document.pdf

# 查找文件
find *.log
find secret* -t f
find tmp -t d

# 截图
screenshot
```

## ⚙️ 配置说明

### 端口配置

所有组件统一使用 **8444** 端口：

- **服务端**: `https://your-server:8444`
- **WebSocket**: `wss://your-server:8444/ws`
- **管理端**: 连接 `https://your-server:8444`

如需修改端口，请编辑 `server.py` 和 `client.py` 中的 `SERVER_PORT` 变量。

### SSL/TLS 证书

程序会自动生成自签名证书（首次运行时）：

```bash
python server.py --admin-password your_password
```

如需手动生成：

```bash
openssl genrsa -out key.pem 2048
openssl req -new -x509 -key key.pem -out cert.pem -days 365
```

## 📁 项目结构

```
ShadowGrid/
├── server.py          # FastAPI 服务端 (HTTPS/WSS)
├── client.py          # WebSocket 客户端
├── admin.py           # 命令行管理终端
├── requirements.txt   # Python 依赖
├── shadowgrid-agent.spec  # PyInstaller 打包配置
├── templates/         # Web 模板
│   ├── index.html
│   └── login.html
├── build/             # 构建临时文件
├── dist/              # 打包输出
│   └── shadowgrid-agent.exe
└── screenshots/       # 截图保存目录
```

## 🔐 安全指南

### ⚠️ 重要安全建议

1. **加密通信** - 所有通信使用 HTTPS/WSS 加密
2. **强密码** - 使用至少 12 位复杂密码
3. **内网使用** - 仅在授权的内部网络中使用
4. **定期更新** - 定期更换密码和证书
5. **合法授权** - 仅用于合法授权的远程管理

### 防火墙配置

确保端口 8444 在防火墙中开放：

```bash
# Windows
netsh advfirewall firewall add rule name="ShadowGrid" dir=in action=allow protocol=TCP localport=8444

# Linux
ufw allow 8444/tcp
```

## 📚 相关文档

- [COMMANDS.md](./COMMANDS.md) - 详细命令文档
- [SERVER_API.md](./SERVER_API.md) - 服务端 HTTP API 参考
- [CLIENT_PROTOCOL.md](./CLIENT_PROTOCOL.md) - 客户端 WebSocket 协议规范
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 开发文档索引

## 🏗️ 技术架构

```
┌─────────────────┐
│   Admin Terminal│
│   (admin.py)    │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   Server API    │
│   (server.py)   │
│   Port: 8444    │
└────────┬────────┘
         │ WSS
         ▼
┌─────────────────┐
│  Client Agent   │
│  (client.py)    │
│/shadowgrid-agent│
└─────────────────┘
```

### 通信流程

1. 客户端启动后通过 WebSocket 连接到服务端
2. 客户端发送注册消息 (client_id, hostname, unique_id)
3. 管理终端通过 HTTP API 发送命令到服务端
4. 服务端通过 WebSocket 将命令转发给客户端
5. 客户端执行命令并返回结果
6. 服务端将结果存储，管理终端可查询

## 📦 打包客户端

使用 PyInstaller 打包客户端：

```bash
pyinstaller shadowgrid-agent.spec
```

打包后的可执行文件位于 `dist/shadowgrid-agent.exe`

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发路线图

- [ ] 多语言支持 (i18n)
- [ ] 插件系统
- [ ] Web 管理界面
- [ ] 批量命令执行
- [ ] 命令历史记录
- [ ] 会话管理

## 📄 许可证

本项目采用 [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0) 许可证。

```
ShadowGrid - An open-source remote administration tool
Copyright (C) 2026  帅丘

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

## 📧 联系作者

如有问题或建议，请通过 GitHub Issues 联系。

---

<div align="center">

** please use this tool only for legal and authorized purposes**

</div>
