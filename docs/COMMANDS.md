# ShadowGrid 命令文档

## 快速开始

ShadowGrid 提供三种使用方式：
1. **admin.py** - 交互式命令行管理工具（推荐）
2. **client.py** - 直接运行客户端
3. **shadowgrid-agent.exe** - 打包后的可执行文件

## 交互式命令（admin.py）

### 管理工具命令

| 命令 | 说明 |
|------|------|
| `list` | 列出所有已连接的设备 |
| `use <编号>` | 选择设备（通过编号） |
| `back` | 返回设备列表 |
| `clear` | 清屏 |
| `history` | 查看命令历史 |
| `history -c` | 清空命令历史 |
| `!!` | 执行上一条命令（实验性） |
| `compgen <命令片段>` | 命令自动补全 |
| `settings` | 查看可配置项列表 |
| `settings <项>` | 查看特定配置值 |
| `settings current` | 查看所有当前配置 |
| `settings reset` | 重置所有配置 |
| `settings clear_hist` | 清空命令历史 |
| `help` | 显示帮助 |
| `quit` | 退出程序 |

### 设备远程命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `ls [路径]` | 可选路径 | 列出目录内容 |
| `cd <目录>` | 目录路径 | 切换目录 |
| `pwd` | 无 | 显示当前目录 |
| `cat <文件>` | 文件路径 | 查看文件内容 |
| `dl <文件> [目录]` | 文件和可选保存目录 | 下载文件 |
| `ud <文件> [目录]` | 本地文件和可选远程目录 | 上传文件 |
| `rm <路径> [-r]` | 路径和可选递归参数 | 删除文件/目录 |
| `mv <源> <目标>` | 源路径和目标路径 | 移动/重命名 |
| `file <路径>` | 文件路径 | 查看文件类型 |
| `find <模式> [-t 类型]` | 搜索模式和可选类型 | 查找文件 |
| `ps` | 无 | 获取进程列表 |
| `process` | 无 | 同 ps 命令 |
| `kill <PID>` | 进程ID | 结束进程 |
| `terminate <PID>` | 进程ID | 同 kill 命令 |
| `persist install` | [路径] | 在系统中持久化客户端 |
| `persist remove` | 无 | 移除持久化设置 |
| `install auto` | 无 | 等同 persist install |
| `shell <命令>` | Shell 命令 | 执行系统命令 |
| `screenshot` | 无 | 截取远程屏幕 |
| `echo <文本>` | 文本 | 回显测试 |
| `time` | 无 | 获取远程时间 |
| `test` | 无 | 测试连接 |
| `back` | 无 | 返回设备列表 |

### 交互示例

```bash
# 运行管理工具
python admin.py

# 查看设备列表
srt > list

# 选择第一个设备
srt > use 1

# 进入设备交互模式
desktop:~ > ls

# 查看指定目录
desktop:~ > ls C:\Users

# 切换目录
desktop:~ > cd Documents

# 查看文件内容
desktop:Documents > cat readme.txt

# 下载文件到指定目录
desktop:Documents > dl report.pdf C:\Downloads

# 上传文件到远程
desktop:~ > ud backup.zip /tmp

# 执行系统命令
desktop:~ > shell ipconfig

# 截取屏幕
desktop:~ > screenshot

# 进程管理
desktop:~ > ps                    # 查看所有进程
desktop:~ > kill 1234             # 终止PID 1234进程

# 持久化管理
desktop:~ > persist install       # 在系统中持久化
desktop:~ > persist remove        # 移除持久化设置

# 返回设备列表
desktop:~ > back

# 命令历史功能
srt > history                     # 查看历史
srt > history -c                  # 清空历史

# 配置管理
srt > settings                    # 查看可配置项
srt > settings current            # 查看当前配置
srt > settings reset              # 重置配置
```

## 文件操作命令详解

### ls / dir
列出目录内容，支持指定路径。

```bash
ls              # 列出当前目录
ls /etc         # 列出 Linux 目录
ls C:\Users     # 列出 Windows 目录
```

输出格式：目录名带 `/`，文件正常显示。

### cd
切换当前工作目录。

```bash
cd /tmp
cd Documents
cd ..
```

### pwd
显示当前工作目录路径。

```bash
pwd
```

### cat
显示文件内容（Base64 编码传输，自动解码显示）。

```bash
cat config.txt
cat /etc/passwd
cat C:\Windows\System32\drivers\etc\hosts
```

### dl
下载远程文件到本地。

```bash
dl report.pdf                    # 下载到默认目录
dl report.pdf C:\Downloads       # 指定保存目录
dl /var/log/syslog /tmp          # 下载 Linux 日志
```

### ud
上传本地文件到远程。

```bash
ud backup.zip                    # 上传到当前目录
ud backup.zip /tmp               # 上传到指定目录
ud script.py .                   # 上传到远程当前目录
```

### rm
删除文件或目录。

```bash
rm temp.txt              # 删除文件
rm old_project -r        # 递归删除目录
rm /tmp/cache -r         # Linux 删除目录
```

### mv
移动或重命名文件/目录。

```bash
mv old.txt new.txt       # 重命名
mv file.txt /tmp         # 移动到 /tmp
mv demo/old demo/new     # 移动并重命名
```

### file
查看文件类型，支持识别：
- text (txt, md, csv, json, xml, ini, log)
- executable (exe, bat, cmd, sh, bin, dll, so, dylib)
- image (jpg, jpeg, png, gif, bmp, svg, ico)
- pdf
- audio (mp3, wav, flac, aac)
- video (mp4, avi, mkv, mov)
- archive (zip, tar, gz, 7z, rar)
- directory
- shortcut

```bash
file document.pdf
file script.py
file archive.zip
```

### find
查找文件，支持通配符和类型过滤。

```bash
find *.log               # 查找所有 log 文件
find secret -t f         # 查找名为 secret 的文件
find tmp -t d            # 查找名为 tmp 的目录
find *.py -t f           # 查找所有 Python 文件
```

### ps / process
获取远程机器上正在运行的进程列表。

```bash
ps                      # 显示所有进程
process                 # 同 ps 命令
```

输出格式：PID、名称、用户名、状态

### kill / terminate
结束指定进程。

```bash
kill 1234               # 终止进程ID 1234
terminate 5678          # 终止进程ID 5678
```

### persist / install
管理系统持久化，使客户端在重启后自动启动。

```bash
persist install        # 在Windows服务启动项或Linux systemd中注册
persist install /opt/shadowgrid   # 指定位置安装
persist remove         # 移除持久化注册
install auto           # 自动安装持久化
```

### shell
执行系统命令，返回命令输出。

```bash
shell ipconfig           # Windows 网络配置
shell df -h             # Linux 磁盘使用
shell ps aux            # Linux 进程列表
```

### screenshot
截取远程桌面屏幕，自动保存截图。

```bash
screenshot
```

截图保存在 `screenshots/` 目录，文件名格式：
```
{client_id}_{timestamp}_shot.png
```

### echo / time / test
这三个是调试命令，用于测试连接。

```bash
echo Hello World         # 回显文本
time                     # 获取远程时间
test                     # 测试连接
```

### command history
通过上下方向键、history命令管理命令历史

```bash
history                 # 显示最近的命令历史
history -c              # 清空命令历史
!!                      # 重新执行上一条命令（实验性）
compgen <partial_cmd>  # 智能命令补全
```

### configuration
通过settings命令管理系统配置

```bash
settings               # 查看配置选项
settings current       # 查看当前配置
settings reset         # 重置所有配置
settings clear_hist    # 清空历史记录
settings server_url    # 查看服务器地址
settings last_client_id # 查看你上次连接的设备ID
```

## 错误处理

常见错误信息：

| 错误 | 说明 |
|------|------|
| `Invalid path` | 路径超出安全范围或不存在 |
| `File not found` | 指定文件不存在 |
| `Directory not found` | 指定目录不存在 |
| `Path traversal detected` | 检测到路径遍历攻击 |
| `Need base64_data and save_as` | 上传缺少必要参数 |
| `PID must be a valid integer` | 进程ID必须是有效整数 |
| `No process with PID X` | 指定进程不存在 |
| `Access denied to kill process` | 权限不足，无法结束进程 |

## 技术细节

### 命令传输流程

```
Admin → Server (HTTP POST /command/{id})
Server → Client (WebSocket)
Client → Server (WebSocket result)
Server → Admin (HTTP GET /results/{id})
```

### 路径安全检查

为防止路径遍历攻击，客户端会检查：
- 相对路径会转换为绝对路径
- 路径必须在允许范围内
- 跨盘符路径在 Windows 上受限

### 数据传输

- 文件内容使用 Base64 编码
- 文本文件自动解码显示
- 二进制文件保存为原始格式

## 相关文档

- [README.md](../README.md) - 项目简介和快速开始
- [CHANGELOG.md](../CHANGELOG.md) - 版本更新记录
