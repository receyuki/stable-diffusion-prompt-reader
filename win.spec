# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


ROOT = Path(SPECPATH)
VERSION_FILE = os.environ.get("SDPR_VERSION_FILE", str(ROOT / "file_version_info.txt"))
DATAS = [
    (str(ROOT / "sd_prompt_reader/resources"), "sd_prompt_reader/resources"),
] + collect_data_files("customtkinter")


def build_executable(script, name, icon, console):
    analysis = Analysis(
        [str(ROOT / script)],
        pathex=[str(ROOT)],
        binaries=[],
        datas=DATAS,
        hiddenimports=["sd_prompt_reader"],
        hookspath=[str(ROOT)],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )
    pyz = PYZ(analysis.pure)
    # Passing binaries and data to EXE preserves the two standalone one-file outputs.
    return EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=console,
        disable_windowed_traceback=False,
        icon=str(ROOT / "sd_prompt_reader/resources" / icon),
        version=VERSION_FILE,
    )


exe_gui = build_executable(
    "gui_main.py", "SD Prompt Reader", "icon-gui.ico", console=False
)
exe_cli = build_executable(
    "cli_main.py", "SD Prompt Reader CLI", "icon-cli.ico", console=True
)
