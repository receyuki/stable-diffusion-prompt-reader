__author__ = "receyuki"
__filename__ = "setup.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""
Create executables file for macOS and Windows
Usage:
    macOS:
        python setup.py py2app
    windows:
        python setup.py
"""
import platform
import toml
from pathlib import Path
from packaging import version
import os


# from sd_prompt_reader.__version__ import VERSION


def get_version():
    path = Path(__file__).resolve().parents[0] / "pyproject.toml"
    pyproject = toml.loads(open(str(path)).read())
    return version.parse(pyproject["tool"]["poetry"]["version"])


def prepend_to_file(filename, line):
    with open(filename, "r+") as file:
        content = file.read()
        file.seek(0)
        file.write(line + "\n" + content)


VERSION = get_version().base_version
version_file = Path(__file__).resolve().parents[0] / "sd_prompt_reader/__version__.py"
with open(version_file, "w") as file:
    file.write('VERSION = "' + str(get_version()) + '"\n')

if platform.system() == "Windows":
    import pyinstaller_versionfile

    pyinstaller_versionfile.create_versionfile(
        output_file="file_version_info.txt",
        version=get_version().base_version,
        file_description="SD Prompt Reader",
        internal_name="SD Prompt Reader",
        legal_copyright="Copyright © 2023 receyuki All rights reserved.",
        original_filename="SD Prompt Reader.exe",
        product_name="SD Prompt Reader",
        translations=[1033, 1200],
    )

    import PyInstaller.__main__

    PyInstaller.__main__.run(["--clean", "win.spec"])

elif platform.system() == "Darwin":
    from pathlib import Path
    from setuptools import setup
    import tkinter as tk
    import shutil
    import os

    APP = ["main.py"]
    DATA_FILES = []
    CFBundleDocumentTypes = [
        dict(
            CFBundleTypeExtensions=["png", "jpg", "jpeg", "webp"],
            CFBundleTypeName="Image File",
            CFBundleTypeRole="Viewer",
        ),
    ]
    OPTIONS = {
        "iconfile": "sd_prompt_reader/resources/icon.icns",
        "plist": {
            "CFBundleName": "SD Prompt Reader",
            "CFBundleDisplayName": "SD Prompt Reader",
            "CFBundleVersion": str(get_version()),
            "CFBundleShortVersionString": get_version().base_version,
            "CFBundleIdentifier": "com.receyuki.sd-prompt-reader",
            "NSHumanReadableCopyright": "Copyright © 2023 receyuki All rights reserved.",
            "CFBundleDocumentTypes": CFBundleDocumentTypes,
        },
        "includes": [
            "pyperclip",
            "PIL",
            "tkinter",
            "tkinterdnd2",
            "os",
            "customtkinter",
            "plyer",
            "pyobjus",
            "plyer.platforms.macosx.notification",
            "tcl8",
            "tcl8.6",
            "charset_normalizer.md__mypyc",
            "PIL.WebPImagePlugin",
            "sd_prompt_reader",
        ],
        "packages": ["sd_prompt_reader.resources"],
    }

    setup(
        name="SD Prompt Reader",
        app=APP,
        data_files=DATA_FILES,
        options={"py2app": OPTIONS},
        setup_requires=["py2app"],
    )

    root = tk.Tk()
    root.overrideredirect(True)
    root.withdraw()
    tcl_dir = Path(root.tk.exprstring("$tcl_library"))
    tk_dir = Path(root.tk.exprstring("$tk_library"))
    root.destroy()

    os.makedirs("./dist/SD Prompt Reader.app/Contents/lib", exist_ok=True)
    print(f"Copying TK from: {tk_dir}")
    shutil.copytree(
        tk_dir, f"./dist/SD Prompt Reader.app/Contents/lib/{tk_dir.parts[-1]}"
    )
    print(f"Copying TCL from: {tcl_dir}")
    shutil.copytree(
        tcl_dir, f"./dist/SD Prompt Reader.app/Contents/lib/{tcl_dir.parts[-1]}"
    )

    shutil.copy(
        "__error__.sh", "./dist/SD Prompt Reader.app/Contents/Resources/__error__.sh"
    )

    # Update poetry dependencies
    skip_packages = ["pyinstaller", "pyinstaller-hooks-contrib", "py2app"]

    with open("requirements.txt", "r") as file:
        lines = file.readlines()

    for line in lines:
        skip = any(skip_package in line for skip_package in skip_packages)
        if not skip:
            if "; sys_platform == 'darwin'" in line:
                package_name = line.split(";")[0].strip()
                command = f"poetry add {package_name} --platform darwin"
            else:
                package_details = line.split(";")[0].strip()
                command = f"poetry add {package_details}"
            os.system(command)
            print(f"Added: {line.strip()}")
        else:
            print(f"Skipped: {line.strip()}")

    print("Dependencies have been processed.")
