# 版本变更日志 (Changelog)

所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
并遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [1.1.0] - 2026-03-15

### 新功能
- 后台静默版本编译 - 新增后台运行模式，无控制台窗口
- 进程管理 - 新增ps/kill命令用于系统进程管理
- 系统持久化 - 新增persist命令设置客户端系统自启
- 本地配置管理 - 新增配置系统保存服务器信息、密码等
- 命令历史记录 - 新增上下方向键浏览历史命令功能
- 命令智能补全 - 新增compgen命令自动补全功能
- 配置管理命令 - 新增settings命令管理配置
- 新增MV、UD、CP、RM命令 - 文件操作功能补全
- 新增CD、PWD、TERMINATE命令 - 与文档完全对齐
- 添加客户端状态验证机制 - 解决虚假掉线问题

### 改进
- SSL证书生成 - 修复在无OpenSSL环境下的SSL证书生成
- 错误处理 - 改进错误处理机制和用户体验
- 编译优化 - 优化PyInstaller编译流程，减小程序体积
- 客户端-服务端通信 - 修复os/base64/shutil模块变量访问错误
- 管理客户端连接状态 - 增加结果等待超时时间，改进掉线检测

### 修复
- 修复readline兼容性问题
- 修复cryptography库导入问题
- 解决日期时间API弃用警告
- 修复命令结果处理机制
- 修复配置保存和加载问题
- 解决模块内部导入导致的变量访问错误 (os/base64/shutil)
- 修复客户端错误识别为掉线的问题
- 修复语法错误和作用域冲突问题
- 修复所有文档中列出但未实现的命令功能
- 修复多种命令执行过程中的模块访问问题

## [1.0.0] - 2026-03-05

### 新功能
- 初始发布版本 - 基础命令行远程控制系统
- 文件操作功能 - 支持ls/cd/pwd/cat/download/upload等功能
- 网络通信体系 - 基于HTTP和WebSocket的安全通信
- 客户端-服务端架构 - 支持多设备同时管理
- 加密传输 - HTTPS/WSS协议保障数据安全
- 屏幕截图 - 截取远程桌面功能
- 配置管理 - 支持用户认证配置

[Unreleased]: https://github.com/qiuqiqiuqid/ShadowGrid/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/qiuqiqiuqid/ShadowGrid/releases/tag/v1.1.0
[1.0.0]: https://github.com/qiuqiqiuqid/ShadowGrid/releases/tag/v1.0.0