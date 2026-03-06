# -*- mode: python ; coding: utf-8 -*-

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
