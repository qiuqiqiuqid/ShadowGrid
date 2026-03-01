# ShadowGrid - 暗影矩阵

## 简介
专业的远程管理和渗透测试工具，支持加密通信、命令行管理、实时文件操作。

## 功能特点
- 加密通信（HTTPS/WSS）
- 命令行交互式管理
- 文件管理（上传/下载/删除/移动）
- 远程代码执行
- 实时屏幕截图
- 自定义命令

## 系统要求
- Python 3.7+
- PyInstaller（打包客户端）

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