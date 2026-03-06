# -*- mode: python ; coding: utf-8 -*-

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
