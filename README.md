# ShadowGrid - 暗影矩阵

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org)
[![Remote Control](https://img.shields.io/badge/status-beta-green)](https://img.shields.io/badge/status-beta-green)

一个轻量级、安全的远程控制系统，用于合法授权的远程管理与运维监控。  
让您的远程管理工作变得 "不那么可怕" —— 至少比敲黑乎乎的终端要友好一点 😎

> ⚠️ **法律声明**: 本项目仅供合法授权的本地网络管理使用。请勿将其用于非法目的（我们不想上新闻）。开发者不对滥用行为负责。

## 🚀 简介：这是什么？

大家好，我是一个名叫 ShadowGrid 的"小管家"。顾名思义，我就像一个暗影矩阵——低调地潜伏在后台，默默帮你管理那些"远方的朋友"。无论你是想偷偷看看同事的桌面（开玩笑的），还是需要管理分布在各地的服务器，我都乐意效劳。

想象一下：你在办公室，却能操作千里之外的电脑，就像拥有"超能力"一样。但请注意，这不是魔法（遗憾的是），而是技术的力量。

## 🎯 新功能亮点

### 1. 进程管理 (`ps`, `kill`)
- 想知道远程机器正在跑哪些程序？`ps` 命令帮你看一遍
- 某个程序跑飞了拖慢系统？`kill` 命令让它说拜拜
- 像在本地操作一样流畅，再也不用担心远程卡死的问题

### 2. 系统持久化 (`persist`)
- 客户端不再是个"随用随走"的过客
- 通过 `persist` 命令，它可以成为系统不可或缺的一部分
- 系统每次启动都会自动召唤它（只要您允许的话）

### 3. 本地配置记忆 (`config` & `history`)
- 自动记住上次的服务器地址，下次启动秒连
- 密码可以安全保存，选择性记住登录凭据
- 命令历史记录，再也不用重复输入长命令
- 最近设备自动记录，一键回连

## 🔧 现有功能保持不变

| 功能 | 描述 | 使用场景 |
|------|------|----------|
| 🔒 加密通信 | HTTPS + WebSocket Secure (WSS) | 保证数据传输安全 |
| 💻 命令执行 | 远程执行 Shell 命令 | 各种系统管理操作 |
| 📁 文件管理 | 上传/下载/删除/移动/查找文件 | 文件资料传输 |
| 📸 屏幕截图 | 远程桌面实时截图 | 可视化远程诊断 |
| 📂 目录浏览 | 浏览远程文件系统 | 云端文件管理器替代 |

## 📋 主要操作命令

### 一般管理命令
```bash
# 初次启动
python admin.py

# 首次使用会提示输入服务器地址和密码
# 如果已保存过配置，可以直接使用上次设定

# 设备管理
list                 # 显示所有已连接设备
use <编号>           # 选择特定设备（如果保存过最近设备，会优先显示）
back                 # 返回设备列表
help                 # 查看所有命令的帮助
```

### 命令历史功能
```bash
# 查看近期执行过的命令
history

# 清空历史记录
history -c

# 执行上一次命令（实验性支持）
!!
```

### 设备远程命令
```bash
# 看看远程目录里有什么宝贝（不建议搜寻隐私文件哦！）
ls
ls C:\Windows\System32  # 这个目录可能有点吓人

# 优雅地更换当前目录
cd Documents

# 查看文件内容，就像在咖啡馆翻书一样轻松
cat readme.txt
```

### 进程管理功能
```bash
# 查看所有正在运行的进程
ps
process    # 同样的命令，换汤不换药

# 发现了一个捣蛋的进程？果断干掉它
kill 1234  # 1234是进程ID，别错杀无辜（比如系统进程）
terminate 1234  # kill 命令的另一个别名
```

### 系统持久化管理
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

## ⚙️ 本地配置 - 让一切变得简单

首次成功连接后，系统将在 `~/.shadowgrid/config.ini` 创建配置文件，自动保存：

- 服务器地址（可选）
- 登录密码（可选，取决于是否选择保存）
- 最后使用的客户端
- 配置项偏好

### 配置技巧 - 成为我们的一份子

所有组件都在8444端口和谐共处：
- 服务端: `https://your-server:8444`
- WebSocket: `wss://your-server:8444/ws` - 这是"悄悄话专线"
- 管理端：连接同上 - 不喜欢热闹的高并发

> 如需改端口（比如8444已经被某程序霸占），请编辑 `server.py` 和 `client.py` 中的 `SERVER_PORT` 变量。不过请记住，8444 是官方黄金端口号，选它总没错。

## 🔐 安全秘籍 - 保护你爱的人

### 给管理员的重要提醒
1. **通信加密** - 所有流量穿了"隐身衣"（HTTPS/WSS）
2. **密码强度** - 建议用 "自行车密码破解难度" 的密码，如 `MyP@ssw0rd!2026$ecure`
3. **合法使用** - 仅用于合法授权的网络管理，不要尝试挑战法律底线
4. **谨慎保存密码** - 使用本地配置功能时要评估设备安全性
5. **常规升级** - 定期换密码和证书，就像定期洗澡一样重要

### 防火墙配置（让"外星人"进来）
```bash
# Windows - 永远不要关闭安全意识
netsh advfirewall firewall add rule name="ShadowGrid" dir=in action=allow protocol=TCP localport=8444

# Linux - 简单粗暴
ufw allow 8444/tcp
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

## 📦 打包发布 - 让它独自旅行

要用PyInstaller把客户端打包成独立程序（这样就不用到处安装Python了）：

```bash
pyinstaller shadowgrid-agent.spec
```

打包好的文件在 `dist/shadowgrid-agent.exe`，把它放到任意地方运行。就像把一个微型管理员塞进一个文件里。

## 🎯 未来规划：下一步要做什么

- [x] 进程管理（已完成！）  
- [x] 持久化安装（已完成！）  
- [x] 本地配置与命令历史（已完成！）  
- [ ] 图形化界面（可能需要聘请UI设计师）  
- [ ] 多语言支持（中文、English等）  
- [ ] 插件系统（允许社区贡献功能）  
- [ ] 消息推送（类似微信通知的功能）  
- [ ] 自愈特性（即使网络中断也能自我恢复）

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
- Fork后自己玩耍
- 点个star以表示赞赏（免费又有效）

---

<div align="center">

**请务必只用于合法授权的目的，文明使用这个小工具**

_"代码改变世界，但前提是你用得对"_ © 2026

</div>
