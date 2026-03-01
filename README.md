# ShadowGrid - 暗影矩阵

## 启动画面

```
╔════════════════════════════════════════════╗
║     ██████╗ ██╗   ██╗██████╗  █████╗      ║
║    ██╔═══██╗██║   ██║██╔══██╗██╔══██╗     ║
║    ██║   ██║██║   ██║██████╔╝███████║     ║
║    ██║   ██║██║   ██║██╔══██╗██╔══██║     ║
║    ╚██████╔╝╚██████╔╝██║  ██║██║  ██║     ║
║     ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝     ║
║          ShadowGrid v1.0                   ║
║      Secure Remote Administration Tool     ║
╚════════════════════════════════════════════╝
```

## 简介
专业的远程管理和渗透测试工具，支持加密通信、命令行管理、实时文件操作。

## 功能说明

### 启动命令

```
usage: shadowgrid-agent.exe [-h] [--server SERVER] [--password PASSWORD]
```

### 命令列表

| 命令 | 参数 | 描述 |
|------|------|------|
| `ls` | `[路径]` | 列出目录内容 |
| `cd` | `[路径]` | 切换当前目录 |
| `pwd` | 无 | 显示当前工作目录 |
| `cat` | `<文件>` | 显示文件内容 |
| `dl` | `<文件> [目录]` | 下载文件到本地 |
| `ud` | `<文件> [目录]` | 上传文件到远程 |
| `rm` | `<路径> [-r]` | 删除文件或目录（-r 递归） |
| `mv` | `<源> <目标>` | 移动或重命名文件 |
| `file` | `<路径>` | 查看文件类型 |
| `find` | `<模式> [-t 类型]` | 查找文件（模式支持通配符） |
| `help` | 无 | 显示帮助信息 |

### 命令示例

```bash
# 列出当前目录
ls

# 列出指定目录
ls C:\Users\Public

# 切换目录
cd \Users\Public

# 显示当前路径
pwd

# 查看文件内容
cat config.txt

# 下载文件
dl report.pdf
dl report.pdf C:\Downloads

# 上传文件
udbackup.zip
ud backup.zip /tmp

# 删除文件
rm temp.txt

# 递归删除目录
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

# 显示帮助
help
```

## 配置说明

### 服务端配置 (server.py)

```python
# 管理员密码（启动时必须指定）
ADMIN_PASSWORD = 'your_secure_password'

# 服务器地址
SERVER_HOST = '0.0.0.0'

# 服务器端口
SERVER_PORT = 8443

# 证书文件
CERT_FILE = 'certs/server.crt'
KEY_FILE = 'certs/server.key'
```

启动命令：
```bash
python server.py --admin-password your_password
```

### 客户端配置 (client.py)

```python
# 服务器地址（WSS协议）
SERVER_URL = 'wss://your-server-ip:8443/ws'

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 30
```

### SSL/TLS 证书

程序会自动生成自签名证书：

```bash
# 自动创建 certs/ 目录和证书
python server.py --admin-password your_password
```

手工生成证书：
```bash
# 生成私钥
openssl genrsa -out certs/server.key 2048

# 生成证书
openssl req -new -x509 -key certs/server.key -out certs/server.crt -days 365
```

## 目录结构

```
SafeRemoteTool/
├── shadowgrid-agent.exe      # 客户端可执行文件（打包版）
├── server.py                 # 服务端主程序
├── admin.py                  # 管理端界面
├── README.md                 # 项目文档
├── requirements.txt          # 依赖包列表
├── certs/                    # SSL/TLS 证书目录
│   ├── server.crt
│   └── server.key
├── screenshots/              # 截图保存目录
│   └── *.png
└── templates/                # Web 页面模板
    ├── login.html
    ├── welcome.html
    └── dashboard.html
```

## 安全提示

⚠️ **重要安全指南**

1. **加密通信**
   - 使用 HTTPS (端口 8443) 用于 Web 界面
   - 使用 WSS (WebSocket Secure) 用于命令通道
   - 所有通信数据均加密传输

2. **密码安全**
   - 使用强密码（至少 12 位，包含大小写字母、数字、特殊字符）
   - 不要在命令行历史中记录密码
   - 定期更换管理员密码

3. **证书验证**
   - 首次连接会提示证书接受
   - 生产环境应使用 CA 签名证书
   - 定期更新 SSL 证书

4. **访问控制**
   - 仅在授权网络中使用
   - 限制服务器监听地址（使用防火墙）
   - 不要在公网暴露服务

5. **审计日志**
   - 所有操作都会记录
   - 定期检查日志文件
   - 保护日志文件不被篡改

6. **合法使用**
   - 仅用于合法授权的远程管理
   - 遵守相关法律法规
   - 对使用行为承担全部责任

## 系统要求
- Python 3.7+
- PyInstaller（打包客户端）
- Windows/Linux/macOS（客户端支持多平台）

## 快速开始

### 1. 启动服务端
```bash
python server.py --admin-password your_password
```

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
# 输入服务器地址
# 输入密码
```

## 许可证
仅供合法授权使用

## 作者
帅丘