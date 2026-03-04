# ShadowGrid 编译说明

## 编译要求

要编译ShadowGrid，您需要：

1. Python 3.7+
2. PyInstaller (`pip install pyinstaller`)
3. 项目源码

## 编译不同版本

### 标准版本
```
pyinstaller --onefile -n shadowgrid-client Client.py
pyinstaller --onefile -n shadowgrid-server server.py  
pyinstaller --onefile -n shadowgrid-admin admin.py
```

### 静默后台版本 (无控制台窗口)
```
pyinstaller --onefile --windowed -n shadowgrid-client-silent Client.py
```

## 编译输出

所有编译后的文件将放置在 `dist/` 目录下。