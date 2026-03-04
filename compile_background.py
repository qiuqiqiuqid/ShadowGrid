import subprocess
import os
import sys
from pathlib import Path

def compile_background_client():
    """编译后台静默版客户端"""
    print("开始编译后台静默版ShadowGrid客户端...")
    
    # 检查Client.py文件是否存在
    client_file = Path("Client.py")
    if not client_file.exists():
        print(f"错误: 找不到 {client_file.absolute()}")
        return False
    
    # 创建spec文件用于后台不显示窗口的编译
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# 收集必要的DLLs和其他资源
datas, binaries, hiddenimports = collect_all('requests')
hiddenimports.extend(['ssl', 'urllib', 'websocket', 'json', 'base64', 'subprocess'])

block_cipher = None

a = Analysis(
    ['Client.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas',
        'pygame', 'pyglet', 'pyqt5', 'pyside2', 'pyside6', 
        'kivy', 'glfw', 'pyopengl', 'wx', 'pywebview', 'flask', 
        'jupyter', 'notebook', 'boeh', 'seaborn', 'plotly',
        'requests_oauthlib', 'google', 'firebase', 'sentry_sdk',
        'azure', 'boto3', 'celery', 'redis', 'sqlalchemy',
        'peewee', 'django', 'flask_sqlalchemy', 'fastapi', 'uvicorn',
        'unittest', 'pydoc', 'doctest', 'pdb'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='shadowgrid-client-silent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 关键：设置为False隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='shadowgrid-client-silent',
)
'''
    
    # 写入SPEC文件
    spec_file = "client_background.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("后台静默版SPEC文件创建完成，开始编译...")
    
    # 只运行pyinstaller命令，无需额外参数（因为在spec文件中已定义所有参数）
    cmd = ['pyinstaller', spec_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("后台静默版客户端编译成功!")
        print(result.stdout)
        
        # 检查生成的文件大小
        dist_dir = Path("dist")
        client_exe = dist_dir / "shadowgrid-client-silent.exe"
        if client_exe.exists():
            size_mb = client_exe.stat().st_size / (1024 * 1024)
            print(f"后台静默版客户端可执行文件大小: {size_mb:.2f} MB")
        else:
            print("警告: 未找到编译后的后台静默版客户端可执行文件")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"编译失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

if __name__ == "__main__":
    print("ShadowGrid 后台静默版编译程序")
    print("================================")
    print("注意：此版本仅为教学/学习目的设计")
    print("请确保您仅在合法授权的环境下使用此软件")
    print()
    
    if compile_background_client():
        print("\n后台静默版客户端创建成功!")
        print("生成的文件位于 ./dist/shadowgrid-client-silent.exe")
        print("\n该程序将在后台运行而不会显示控制台窗口")
    else:
        print("\n编译失败")
        exit(1)