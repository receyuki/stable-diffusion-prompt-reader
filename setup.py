"""
Create executables file for macOS and Windows
Usage:
    macOS:
        python setup.py py2app
    windows:
        python setup.py
"""
import platform

from sd_prompt_reader.__version__ import VERSION

if platform.system() == "Windows":
    import pyinstaller_versionfile

    pyinstaller_versionfile.create_versionfile(
        output_file="file_version_info.txt",
        version=VERSION,
        file_description="SD Prompt Reader",
        internal_name="SD Prompt Reader",
        legal_copyright="Copyright © 2023 receyuki All rights reserved.",
        original_filename="SD Prompt Reader.exe",
        product_name="SD Prompt Reader",
        translations=[1033, 1200]
    )

    import PyInstaller.__main__

    PyInstaller.__main__.run([
        "--clean",
        "win.spec"
    ])

elif platform.system() == "Darwin":
    from pathlib import Path
    from setuptools import setup
    import tkinter as tk
    import shutil
    import os

    APP = ['main.py']
    DATA_FILES = []
    OPTIONS = {
        'iconfile': 'resources/icon.icns',
        'plist': {
            'CFBundleName': 'SD Prompt Reader',
            'CFBundleDisplayName': 'SD Prompt Reader',
            'CFBundleVersion': VERSION,
            'CFBundleIdentifier': 'com.receyuki.sd-prompt-reader',
            'NSHumanReadableCopyright': 'Copyright © 2023 receyuki All rights reserved.',
        },
        'includes': ['pyperclip', 'PIL', 'tkinter', 'tkinterdnd2', 'os', 'customtkinter', 'plyer', 'pyobjus',
                     'plyer.platforms.macosx.notification', 'tcl8', 'tcl8.6', 'charset_normalizer.md__mypyc',
                     'PIL.WebPImagePlugin', 'sd_prompt_reader'],
        'packages': ['resources']
    }

    setup(
        name='SD Prompt Reader',
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

    root = tk.Tk()
    root.overrideredirect(True)
    root.withdraw()
    tcl_dir = Path(root.tk.exprstring('$tcl_library'))
    tk_dir = Path(root.tk.exprstring('$tk_library'))
    root.destroy()

    os.makedirs("./dist/SD Prompt Reader.app/Contents/lib", exist_ok=True)
    print(f"Copying TK from: {tk_dir}")
    shutil.copytree(tk_dir, f"./dist/SD Prompt Reader.app/Contents/lib/{tk_dir.parts[-1]}")
    print(f"Copying TCL from: {tcl_dir}")
    shutil.copytree(tcl_dir, f"./dist/SD Prompt Reader.app/Contents/lib/{tcl_dir.parts[-1]}")
