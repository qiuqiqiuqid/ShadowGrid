# ShadowGrid - 暗影矩阵

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org)
[![Remote Control](https://img.shields.io/badge/status-stable-green)](https://img.shields.io/badge/status-stable-green)

一个轻量级、安全的远程控制系统，用于合法授权的远程管理与运维监控。  
让您的远程管理工作变得 "不那么可怕" —— 至少比敲黑乎乎的终端要友好一点 😎

> ⚠️ **法律声明**: 本项目仅供合法授权的本地网络管理使用。请勿将其用于任何非法目的。开发者不对滥用行为负责。此软件仅供教育和研究目的。

## 🔒 重要提醒 (请务必仔细阅读)

本项目不提供预编译的二进制文件。出于安全和合法考虑，所有使用者必须自行编译程序，不能直接使用他人提供的二进制版本。用户需要按照下方的编译说明自行完成编译流程。

## 🚀 简介：这是什么？

大家好，我是一个名叫 ShadowGrid 的"小管家"。顾名思义，我就像一个暗影矩阵——低调地潜伏在后台，默默帮你管理那些"远方的朋友"。无论你是想偷偷看看同事的桌面（开玩笑的），还是需要管理分布在各地的服务器，我都乐意效劳。

想象一下：你在办公室，却能操作千里之外的电脑，就像拥有"超能力"一样。但请注意，这不是魔法（遗憾的是），而是技术的力量。

## 🎯 功能亮点

### 基础功能
- 🔐 **加密通信** - HTTPS + WebSocket Secure (WSS)
- 💻 **命令执行** - 远程执行 Shell 命令
- 📁 **文件管理** - 上传/下载/删除/移动/查找文件
- 📸 **屏幕截图** - 远程桌面实时截图
- 📂 **目录浏览** - 浏览远程文件系统

### 进程管理 (`ps`, `kill`)
- 想知道远程机器正在跑哪些程序？`ps` 命令帮你看一遍
- 某个程序跑飞了拖慢系统？`kill` 命令让它说拜拜
- 像在本地操作一样流畅，再也不用担心远程卡死的问题

### 系统持久化 (`persist`)
- 客户端不再是个"随用随走"的过客
- 通过 `persist` 命令，它可以成为系统不可或缺的一部分
- 系统每次启动都会自动召唤它（只要您允许的话）

### 本地配置与历史 (`config`, `history`)
- **自动记住配置** - 上次使用的服务器地址
- **记住密码功能** - 可选的安全密码记忆
- **命令历史** - 支持方向键浏览历史命令
- **命令补全** - 通过 `compgen` 智能补全命令

## 🔧 安装与编译说明 (必须自行编译)

### 环境准备
确保已安装Python 3.7+及以上版本。

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 程序使用说明
```bash
# 启动服务端
python server.py --admin-password your_password

# 启动客户端
python client.py

# 启动管理台
python admin.py
```

> **安全提醒**: 请使用安全且不易猜测的密码，建议使用强密码生成器。

### 3. 自己编译程序 (重要!)
**⚠️ 本项目不提供任何预先编译的二进制文件。出于网络安全和个人责任考虑，所有用户都需要自行编译。**

#### 普通精简版本编译：
```bash
# 使用PyInstaller编译精简版
pyinstaller --onefile -n shadowgrid-client Client.py  # 客户端
pyinstaller --onefile -n shadowgrid-server server.py  # 服务端
pyinstaller --onefile -n shadowgrid-admin admin.py    # 管理端
```

#### 后台静默版本编译 (不显示控制台窗口)：
```bash
# 编译在后台运行且不显示窗口的版本
pyinstaller --onefile --windowed -n shadowgrid-client-silent Client.py
```
> **重要**: 使用 `--windowed` 或 `console=False` 参数编译的版本将在后台运行而不会显示控制台窗口，这适用于生产环境的长期部署。

编译后的文件位于 `dist/` 目录。

## 📋 使用示例 - 让我们玩起来！

### 基本操作
```bash
# 看看远程目录里有什么宝贝（不建议搜寻隐私文件哦！）
ls
ls C:\  # 查看根目录

# 优雅地更换当前目录
cd Documents

# 查看文件内容，就像在咖啡馆翻书一样轻松
cat readme.txt
```

### 新增的进程管理功能
```bash
# 查看所有正在运行的进程
ps
process    # 同样的命令，换汤不换药

# 发现了一个捣蛋的进程？果断干掉它
kill 1234  # 1234是进程ID，别错杀无辜（比如系统进程）
terminate 1234  # kill 命令的另一个别名
```

### 持久化管理
```bash
# 让客户端开机自动启动，真正"扎根"在系统里
persist install
install auto  # 等效命令

# 改变注意要删除持久化设置？
persist remove
```

### 文件操作（生活必备技能）
```bash
# 把远程文件搬到本地
dl important_document.pdf
dl secret_recipe.docx ~/Downloads

# 把本地文件送过去（搬家小能手）
ud backup.zip
ud photo.jpg /home/user/shared
```

### 系统配置管理
```bash
# 查看当前配置
settings current

# 清除配置（包括密码）
settings reset

# 清除命令历史
settings clear_hist

# 查看特定配置项
settings server_url  # 服务器地址
settings last_client_id  # 最后连接的客户端
settings auto_remember_password  # 是否自动记住密码
```

### 命令历史功能
```bash
# 查看命令历史
history

# 清除历史记录
history -c

# 重新执行上一条命令
!!
```

### 更多高级操作
```bash
# 移动/重命名文件（重命名的艺术）
mv old_file.txt new_file.txt
mv file.txt C:\backup

# 查找文件（寻宝游戏）
find *.log
find secret* -t f    # 找文件
find tmp -t d        # 找目录

# 当然还有截图（偷窥...额，查看功能）
screenshot
```

> 隐藏彩蛋：如果你发现系统中有可疑进程，`ps` 命令可以帮助你找出真相。不过请注意：请勿随意杀死系统进程，否则后果自负。别拿菜刀切手指还怪刀子锋利。

## ⚙️ 配置技巧 - 成为我们的一份子

所有组件都在8444端口和谐共处：
- 服务端: `https://your-server:8444`
- WebSocket: `wss://your-server:8444/ws` - 这是"悄悄话专线"
- 管理端：连接同上 - 不喜欢热闹的高并发

> 如需改端口（比如8444已经被某程序霸占），请编辑 `server.py` 和 `client.py` 中的 `SERVER_PORT` 变量。不过请记住，8444 是官方黄金端口号，选它总没错。

## 🔐 安全秘籍 - 保护你爱的人

### 给管理员的重要提醒
1. **通信加密** - 所有流量穿了"隐身衣"（HTTPS/WSS）
2. **密码强度** - 建议用 "自行车密码破解难度" 的密码，如 `MyP@ssw0rd!2026$ecure`
3. **本地编译** - 必须自行编译，不得使用他人提供的二进制版
4. **合法使用** - 仅用于合法授权的网络管理，不要尝试挑战法律底线
5. **定期更换凭证** - 定期更改密码和证书
6. **防火墙设置** - 确保端口配置符合安全政策

### 防火墙配置（让"外星人"进来）
```bash
# Linux - 简单粗暴
ufw allow 8444/tcp

# macOS - 使用pfctl
echo 'pass in proto tcp from any to any port 8444' >> /etc/pf.conf

# Windows - PowerShell
New-NetFirewallRule -DisplayName "ShadowGrid" -Direction Inbound -Protocol TCP -LocalPort 8444 -Action Allow
```

## 📁 架构解析 - 慕课时刻

这里有一个简单易懂的数据流向图：

```
┌─────────────────┐
│   管理员       │    ← 你（人类）
│   (admin.py)    │    
└────────┬────────┘        警告：只对你信任的服务器执行操作
         │ HTTPS                （不然后果自负）    
         ▼
┌─────────────────┐
│   服务器        │    ← 控制中心（机器人）
│   (server.py)   │        
│   8444端口     │         通过WSS与代理聊天
└────────┬────────┘              
         │ WSS                  (WebSocket Security)         
         ▼
┌─────────────────┐
│  客户端代理     │    ← 目标机器上的卧底
│  (client.py)    │    
│/shadowgrid-agent│         随叫随到的小助手
└─────────────────┘            （希望它不要太听话）
```

> 注：整个过程就像打电话一样自然，只不过所有对话都加密了。客户端启动后会主动联系服务器报到，然后安安静静等待您的指令。感觉像个乖巧的"数字宠物"，是不是？

## 🏗️ 技术栈 - Geek时间

- FastAPI (用于服务端) - 快如闪电的现代化框架
- WebSocket - 实时双向通信的小精灵
- Python - 全栈主力（没有它搞不定的事）
- SSL/TLS - 专业加密团队护航
- psutil - 进程管理界的瑞士军刀
- ConfigParser - 配置管理神器
- Readline - 命令历史专家

## 📦 编译发布 - 打包说明

**重要提醒: 本项目不提供任何预编译版本。出于安全责任考虑，所有用户必须使用源代码自行编译：**

### 普通精简版编译:
```bash
pyinstaller --onefile --exclude-module tkinter \
  --exclude-module matplotlib --exclude-module pygame \
  -n shadowgrid-client Client.py
pyinstaller --onefile --exclude-module tkinter \
  --exclude-module matplotlib --exclude-module pygame \
  -n shadowgrid-server server.py
pyinstaller --onefile --exclude-module tkinter \
  --exclude-module matplotlib --exclude-module pygame \
  -n shadowgrid-admin admin.py
```

### 后台运行版编译 (静默无声):
```bash
pyinstaller --onefile --windowed --exclude-module tkinter \
  --exclude-module matplotlib --exclude-module pygame \
  -n shadowgrid-client-silent Client.py
```

编译完成后，所有文件位于 `dist/` 目录。

## 🎯 未来规划：下一步要做什么

- [x] 进程管理（已完成！）  
- [x] 持久化安装（已完成！）  
- [x] 本地配置与历史（已完成！）
- [x] SSL证书修复（已完成！）
- [x] 后台静默运行（已完成！）
- [ ] Web管理界面（待计划）  
- [ ] 多因素认证（待计划)
- [ ] 自动更新功能（待计划）

## 🤝 贡献代码 - 一起来造火箭

欢迎提交Issue和PR，让我们一起把它做得更好！  
不过请记住：代码即友谊，测试见真情。

## 📜 许可证

本项目采用 [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0) 许可。简单来说，你可以自由修改和使用这个项目，但如果你分发修改版，也必须保持开源。

```
ShadowGrid - An open-source remote administration tool for legitimate uses
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

## 📞 支持

如果这个项目帮到了您，或者您遇到什么问题，可以：
- 提交GitHub Issues（最推荐）
- Fork后自己研究和玩耍
- 点个star以表示赞赏（免费又有效）

---

<div align="center">

**请务必只用于合法授权的目的，文明使用这个小工具**  
**⚠️ 请自行编译，不提供预编译版本**  
_"代码改变世界，但前提是你用得对"_ © 2026

</div>

## 目录结构

```
ShadowGrid/
├── server.py          # FastAPI 服务端
├── client.py          # Python 客户端
├── admin.py           # Python 管理终端
├── requirements.txt   # Python 依赖
├── docs/              # 文档目录
│   ├── README.md
│   ├── COMMANDS.md
│   ├── SERVER_API.md
│   ├── CLIENT_PROTOCOL.md
│   ├── DEVELOPMENT.md
│   ├── COMPILE.md
│   └── CHANGELOG.md
├── build-tools/       # 构建工具目录
│   ├── admin_minimal.spec
│   ├── client_background.spec
│   ├── client_minimal.spec
│   ├── server_minimal.spec
│   ├── compile_background.py
│   └── compile_client.py  
├── templates/         # Web 模板
│   ├── index.html
│   └── login.html
├── screenshots/       # 截图文件夹
└── certs/             # 证书文件
    ├── cert.pem
    └── key.pem
```

现在文档和编译工具都有组织良好的分离结构，便于维护。
