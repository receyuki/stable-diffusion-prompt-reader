# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['sd_prompt_reader/main.py', 'sd_prompt_reader/image_data_reader.py', 'sd_prompt_reader/__version__.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'), ('venv/lib/site-packages/customtkinter', 'customtkinter')],
    hiddenimports=['collect_data_files'],
    hookspath=['.'],
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
    name='SD Prompt Reader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    windowed=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
    version='file_version_info.txt',
)
