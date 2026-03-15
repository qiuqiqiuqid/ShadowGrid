# ShadowGrid v1.2.2 Release Notes

## 📋 发布信息

- **版本号**: v1.2.2
- **发布日期**: 2026-03-15
- **类型**: Bug 修复版本
- **前置版本**: v1.2.1

---

## 🐛 Bug 修复

### 关键修复

#### 1. 修复 UnboundLocalError: cannot access local variable 'time'

**问题描述**:
- 在使用 `use <编号>` 命令连接设备后，程序崩溃
- 错误信息：`UnboundLocalError: cannot access local variable 'time' where it is not associated with a value`
- 错误位置：`admin.py` 第 845 行 `time.sleep(0.5)`

**根本原因**:
- `time` 模块已在文件顶部（第 6 行）全局导入
- 但在 `interaction_loop` 函数内部的第 1071 行和 1144 行有 `import time, hashlib`
- Python 将函数内的 `import time` 视为局部变量定义
- 导致函数开头的 `time.sleep()` 调用时，`time` 还未绑定

**解决方案**:
```diff
# 第 1071 行
- import time, hashlib
+ import hashlib

# 第 1144 行  
- import time, hashlib
+ import hashlib
```

---

#### 2. 删除重复的 stream_upload_file 函数定义

**问题描述**:
- `stream_upload_file` 函数在 `admin.py` 中被定义了两次
- 第 494 行：完整版本（包含 MD5 完整性校验）
- 第 718 行：简化版本（无完整性校验）

**解决方案**:
- 保留第 494 行的完整版本（带完整性校验）
- 删除第 718-804 行的重复定义
- 精简代码 104 行

---

## 📊 代码统计变化

| 文件 | 修复前行数 | 修复后行数 | 变化 |
|------|-----------|-----------|------|
| admin.py | 1817 | 1713 | -104 行 |

---

## ✅ 验证结果

### 语法检查
```
✓ server.py - OK
✓ client.py - OK
✓ admin.py - OK
```

### 模块导入测试
```
✓ import server - OK
✓ import client - OK
✓ import admin - OK
```

### 功能验证
- ✓ 文件下载功能正常
- ✓ 文件上传功能正常
- ✓ 进度条动画正常显示
- ✓ MD5 完整性校验正常工作

---

## 📦 安装与编译

### 环境要求
- Python 3.7+
- Windows / Linux / macOS

### 安装依赖
```bash
pip install -r requirements.txt
```

### 编译说明

#### 普通版本
```bash
# 客户端
pyinstaller --onefile -n shadowgrid-client client.py

# 服务端
pyinstaller --onefile -n shadowgrid-server server.py

# 管理端
pyinstaller --onefile -n shadowgrid-admin admin.py
```

#### 后台静默版本
```bash
# 后台运行客户端（无控制台窗口）
pyinstaller --onefile --windowed -n shadowgrid-client-silent client.py
```

---

## 🚀 使用说明

### 启动服务端
```bash
python server.py --admin-password your_password
```

### 启动客户端
```bash
python client.py
```

### 启动管理端
```bash
python admin.py
```

---

## 📄 相关文档

- [README.md](../README.md) - 项目简介和快速开始
- [CHANGELOG.md](../CHANGELOG.md) - 完整版本变更日志
- [COMMANDS.md](../COMMANDS.md) - 命令使用手册
- [SERVER_API.md](../SERVER_API.md) - 服务端 API 文档
- [CLIENT_PROTOCOL.md](../CLIENT_PROTOCOL.md) - 客户端协议文档

---

## 🔗 链接

- **GitHub Release**: https://github.com/qiuqiqiuqid/ShadowGrid/releases/tag/v1.2.2
- **源码仓库**: https://github.com/qiuqiqiuqid/ShadowGrid
- **问题反馈**: https://github.com/qiuqiqiuqid/ShadowGrid/issues

---

## ⚠️ 重要提醒

**本项目不提供预编译的二进制文件**。出于安全和合法考虑，所有使用者必须自行编译程序，不能直接使用他人提供的二进制版本。

---

## 📜 许可证

GPL-3.0 License

---

## 👨‍💻 作者

帅丘

---

*最后更新：2026-03-15*
