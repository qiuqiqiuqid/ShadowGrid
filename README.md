# ShadowGrid - 暗影矩阵

## 变更日志

### v1.0.1 (2026-03-01)

**优化改进**
- 性能优化：命令响应延迟降至 0.5 秒
- 新增 shell 命令支持
- 优化 ls 命令输出格式
- 截图保存添加时间戳
- 统一端口配置为 8444

**问题修复**
- 修复 Basic Auth 认证错误
- 修复 ImageGrab 模块检查逻辑
- 修复 ls 命令 NoneType 错误
- 修复路径安全检查
- 修复 SSL 证书验证

**技术改进**
- 简化 login 接口
- 优化 command 响应时间

### v1.0 (2026-02-15)
- 初始版本

## 快速开始

### 1. 启动服务端
```bash
python server.py --admin-password your_password
```
服务端监听端口：**8444** (HTTPS/WSS)

### 2. 启动客户端
```bash
python client.py
```
或直接运行打包的 exe：
```bash
shadowgrid-agent.exe
```

### 3. 启动管理端
```bash
python admin.py
```
按提示输入服务器地址和密码即可。

## 功能说明

| 功能 | 描述 |
|------|------|
| 加密通信 | HTTPS (8444) + WSS (WebSocket Secure) |
| 命令执行 | 远程执行系统命令 |
| 文件管理 | 上传/下载/删除/移动/查找 |
| 屏幕截图 | 远程桌面截图 |
| 目录浏览 | 列出远程目录内容 |

### 客户端命令列表

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
| `screenshot` | 无 | 截取远程屏幕 |

### 命令示例

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

## 配置说明

### 端口配置

所有组件统一使用 **8444** 端口：

- **服务端**: `https://your-server:8444`
- **WebSocket**: `wss://your-server:8444/ws`
- **管理端**: 连接 `https://your-server:8444`

### 修改配置

**server.py** - 修改端口：
```python
SERVER_PORT = 8444  # 修改此处
```

**client.py** - 修改端口：
```python
SERVER_URL = "https://your-server:8444"
```

### SSL/TLS 证书

程序会自动生成自签名证书（首次运行时）：

```bash
# 自动创建证书文件
python server.py --admin-password your_password
```

如需手工生成：
```bash
openssl genrsa -out key.pem 2048
openssl req -new -x509 -key key.pem -out cert.pem -days 365
```

## 系统要求

- Python 3.7+
- PyInstaller（打包客户端）
- Windows/Linux/macOS（客户端）

## 依赖安装

```bash
pip install -r requirements.txt
```

依赖包：
- fastapi - Web 框架
- uvicorn - ASGI 服务器
- websocket-client - WebSocket 客户端
- Pillow - 图像处理（截图）
- requests - HTTP 请求
- PyOpenSSL - SSL 支持

## 项目结构

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
└── dist/              # 打包输出
    └── shadowgrid-agent.exe
```

## 安全提示

⚠️ **重要安全指南**

1. **加密通信** - 所有通信使用 HTTPS/WSS 加密
2. **强密码** - 使用至少 12 位复杂密码
3. **内网使用** - 仅在授权网络中使用
4. **定期更新** - 定期更换密码和证书
5. **合法授权** - 仅用于合法授权的远程管理

## 许可证
GPL-3.0 - 仅供合法授权使用

## 作者
帅丘

## 相关文档
- [COMMANDS.md](./COMMANDS.md) - 详细命令文档
