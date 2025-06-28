# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ntp_monitor_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/backend', 'backend'),
        ('data/frontend', 'frontend'),
        ('data/config', 'config'),
        ('data/instance', 'instance'),
        ('data/requirements.txt', '.'),
        ('data/README.md', '.'),
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'socketio',
        'eventlet.hubs.epolls',
        'eventlet.hubs.kqueue', 
        'eventlet.hubs.selects',
        'flask_login',
        'flask_sqlalchemy',
        'flask_migrate',
        'ntplib',
        'email.mime.text',
        'email.mime.multipart',
        'smtplib',
        'sqlite3',
        'threading',
        'multiprocessing',
        'concurrent.futures',
        'datetime',
        'json',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='NTP_Monitor_Enterprise',
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
    icon='resources/icon.ico',
    version_file='resources/version_info.txt'
)