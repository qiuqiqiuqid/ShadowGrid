import subprocess
import os
import sys
from pathlib import Path

def compile_client():
    """编译精简版客户端"""
    print("开始编译精简版ShadowGrid客户端...")
    
    # 检查Client.py文件是否存在
    client_file = Path("Client.py")
    if not client_file.exists():
        print(f"错误: 找不到 {client_file.absolute()}")
        return False
    
    # 创建spec文件用于定制编译
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Client.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
        'peewee', 'django', 'flask_sqlalchemy', 'fastapi', 'uvicorn'
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
    name='shadowgrid-client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保持控制台用于调试
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
    name='shadowgrid-client',
)
'''
    
    # 写入SPEC文件
    spec_file = "client_minimal.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("SPEC文件创建完成，开始编译...")
    
    # 注意：因为已经提供了.spec文件，我们只需运行 pyinstaller client_minimal.spec
    cmd = ['pyinstaller', spec_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("客户端编译成功!")
        print(result.stdout)
        
        # 检查生成的文件大小
        dist_dir = Path("dist")
        client_exe = dist_dir / "shadowgrid-client.exe"
        if client_exe.exists():
            size_mb = client_exe.stat().st_size / (1024 * 1024)
            print(f"客户端可执行文件大小: {size_mb:.2f} MB")
        else:
            print("警告: 未找到编译后的客户端可执行文件")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"编译失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def compile_server():
    """编译精简版服务端"""
    print("\n开始编译精简版ShadowGrid服务端...")
    
    # 检查server.py文件是否存在
    server_file = Path("server.py")
    if not server_file.exists():
        print(f"错误: 找不到 {server_file.absolute()}")
        return False
    
    # 创建SPEC文件
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['fastapi', 'uvicorn', 'ssl', 'argparse'],
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
        'peewee', 'django', 'flask_sqlalchemy'
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
    name='shadowgrid-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='shadowgrid-server',
)
'''
    
    spec_file = "server_minimal.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("服务器SPEC文件创建完成，开始编译...")
    
    cmd = ['pyinstaller', spec_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("服务器编译成功!")
        print(result.stdout)
        
        # 检查生成的文件大小
        dist_dir = Path("dist")
        server_exe = dist_dir / "shadowgrid-server.exe"
        if server_exe.exists():
            size_mb = server_exe.stat().st_size / (1024 * 1024)
            print(f"服务器可执行文件大小: {size_mb:.2f} MB")
        else:
            print("警告: 未找到编译后的服务器可执行文件")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"编译失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def compile_admin():
    """编译精简版管理端"""
    print("\n开始编译精简版ShadowGrid管理端...")
    
    # 检查admin.py文件是否存在
    admin_file = Path("admin.py")
    if not admin_file.exists():
        print(f"错误: 找不到 {admin_file.absolute()}")
        return False
    
    # 创建SPEC文件
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['admin.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['readline', 'configparser', 'urllib.request'],
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
        'PIL', 'websocket', 'ImageGrab', 'ssl', 'socket'
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
    name='shadowgrid-admin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='shadowgrid-admin',
)
'''
    
    spec_file = "admin_minimal.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("管理端SPEC文件创建完成，开始编译...")
    
    cmd = ['pyinstaller', spec_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("管理端编译成功!")
        print(result.stdout)
        
        # 检查生成的文件大小
        dist_dir = Path("dist")
        admin_exe = dist_dir / "shadowgrid-admin.exe"
        if admin_exe.exists():
            size_mb = admin_exe.stat().st_size / (1024 * 1024)
            print(f"管理端可执行文件大小: {size_mb:.2f} MB")
        else:
            print("警告: 未找到编译后的管理端可执行文件")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"编译失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

if __name__ == "__main__":
    print("ShadowGrid 编译程序")
    print("=====================")
    
    success_count = 0
    total_count = 3
    
    if compile_client():
        success_count += 1
        
    if compile_server():
        success_count += 1
    
    if compile_admin():
        success_count += 1
    
    print(f"\n编译完成! 成功编译了 {success_count}/{total_count} 个组件")
    print("编译后的文件位于 ./dist/ 目录下")
    
    if success_count == total_count:
        print("\n所有可执行文件已生成:")
        print("- dist/shadowgrid-client.exe (客户端)")
        print("- dist/shadowgrid-server.exe (服务端)") 
        print("- dist/shadowgrid-admin.exe (管理端)")
        print("\n注意: 这些是用于学习的合法远程管理工具")
    else:
        print(f"\n只有 {success_count}/{total_count} 个组件编译成功")
        exit(1)