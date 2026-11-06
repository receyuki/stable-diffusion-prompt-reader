"""Build desktop applications from a prepared native Python environment.

macOS:  python setup.py py2app --output-dir /path/to/fresh-output
Windows: python setup.py --output-dir C:\\path\\to\\fresh-output
Dependency installation belongs to environment preparation, never to this command.
Use an isolated source copy and a fresh output directory for each build.
"""

__author__ = "receyuki"
__filename__ = "setup.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import argparse
import ast
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import struct
import sys
import tomllib

ROOT = Path(__file__).resolve().parent


def get_version():
    from packaging.version import Version

    with (ROOT / "pyproject.toml").open("rb") as file:
        version = tomllib.load(file)["tool"]["poetry"]["version"]
    runtime = ast.parse((ROOT / "sd_prompt_reader/__version__.py").read_text())
    versions = [
        ast.literal_eval(node.value)
        for node in runtime.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in node.targets
        )
    ]
    if versions != [version]:
        raise ValueError(
            "pyproject.toml and sd_prompt_reader/__version__.py versions differ; update source before building"
        )
    return Version(version)


def build_mac(version, output, architecture):
    import tkinter
    from setuptools import setup

    root = tkinter.Tk()
    try:
        root.withdraw()
        tcl_library = Path(str(root.tk.call("info", "library"))).resolve()
        tk_library = Path(str(root.tk.call("set", "tk_library"))).resolve()
        tcl_patchlevel = str(root.tk.call("info", "patchlevel"))
        tk_patchlevel = str(root.tk.call("package", "provide", "Tk"))
    finally:
        root.destroy()
    if not all(level.startswith("8.6.") for level in (tcl_patchlevel, tk_patchlevel)):
        raise ValueError("The active Tcl and Tk runtimes must both be 8.6")
    if (
        not (tcl_library / "init.tcl").is_file()
        or not (tk_library / "tk.tcl").is_file()
    ):
        raise ValueError(
            "The active Tcl/Tk script libraries must contain init.tcl and tk.tcl"
        )
    libraries = [tcl_library, tk_library]
    # Tcl's module search uses the sibling tcl<major> directory when present.
    modules = tcl_library.parent / f"tcl{tcl_patchlevel.split('.')[0]}"
    if modules.is_dir():
        libraries.append(modules)

    prescript = output / "bootstrap-tk.py"
    prescript.write_text(
        "def _sdpr_boot_tkinter():\n"
        "    import os\n"
        "    resources = os.environ['RESOURCEPATH']\n"
        f"    os.environ['TCL_LIBRARY'] = os.path.join(resources, 'lib', {tcl_library.name!r})\n"
        f"    os.environ['TK_LIBRARY'] = os.path.join(resources, 'lib', {tk_library.name!r})\n"
        "_sdpr_boot_tkinter()\n",
        encoding="utf-8",
    )
    native_inputs = {
        "tcl_patchlevel": tcl_patchlevel,
        "tk_patchlevel": tk_patchlevel,
        "script_libraries": [str(path) for path in libraries],
        "prescript_sha256": hashlib.sha256(prescript.read_bytes()).hexdigest(),
        "script_sha256": {
            f"{library.name}/{path.relative_to(library).as_posix()}": hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for library in libraries
            for path in sorted(library.rglob("*"))
            if path.is_file()
        },
    }
    (output / "tcl-tk-inputs.json").write_text(
        json.dumps(native_inputs, indent=2, sort_keys=True) + "\n"
    )

    setup(
        name="SD Prompt Reader",
        version=str(version),
        app=[{"script": str(ROOT / "main.py"), "prescripts": [str(prescript)]}],
        packages=[],
        py_modules=[],
        script_args=["py2app"],
        options={
            "build": {"build_base": str(output / "temp")},
            "py2app": {
                "bdist_base": str(output / "work"),
                "dist_dir": str(output / "dist"),
                "arch": architecture,
                "resources": [("lib", [str(path) for path in libraries])],
                "iconfile": str(ROOT / "sd_prompt_reader/resources/icon.icns"),
                "plist": {
                    "CFBundleName": "SD Prompt Reader",
                    "CFBundleDisplayName": "SD Prompt Reader",
                    "CFBundleVersion": str(version),
                    "CFBundleShortVersionString": version.base_version,
                    "CFBundleIdentifier": "com.receyuki.sd-prompt-reader",
                    "NSHumanReadableCopyright": "Copyright © 2023 receyuki All rights reserved.",
                    "CFBundleDocumentTypes": [
                        {
                            "CFBundleTypeExtensions": ["png", "jpg", "jpeg", "webp"],
                            "CFBundleTypeName": "Image File",
                            "CFBundleTypeRole": "Viewer",
                        }
                    ],
                },
                "includes": ["PIL.WebPImagePlugin"],
                "packages": ["sd_prompt_reader", "customtkinter", "tkinterdnd2"],
            },
        },
    )


def build_windows(version, output):
    import pyinstaller_versionfile
    import PyInstaller.__main__

    work = output / "work"
    work.mkdir()
    version_file = work / "file_version_info.txt"
    pyinstaller_versionfile.create_versionfile(
        output_file=str(version_file),
        version=version.base_version,
        file_description="SD Prompt Reader",
        internal_name="SD Prompt Reader",
        legal_copyright="Copyright © 2023 receyuki All rights reserved.",
        original_filename="SD Prompt Reader.exe",
        product_name="SD Prompt Reader",
        translations=[1033, 1200],
    )
    previous = os.environ.get("SDPR_VERSION_FILE")
    try:
        os.environ["SDPR_VERSION_FILE"] = str(version_file)
        PyInstaller.__main__.run(
            [
                "--clean",
                "--noconfirm",
                "--workpath",
                str(work),
                "--distpath",
                str(output / "dist"),
                str(ROOT / "win.spec"),
            ]
        )
    finally:
        if previous is None:
            os.environ.pop("SDPR_VERSION_FILE", None)
        else:
            os.environ["SDPR_VERSION_FILE"] = previous


def build_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["py2app"])
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Check selected inputs and print their manifest without building or writing files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "build" / "desktop",
        help="Fresh output directory (default: build/desktop beside setup.py).",
    )
    args = parser.parse_args(argv)
    target = platform.system()
    if target not in {"Darwin", "Windows"}:
        parser.error("Build on native macOS or Windows")
    if target == "Darwin" and args.command != "py2app":
        parser.error("macOS builds require the py2app command")
    if target == "Windows" and args.command is not None:
        parser.error("Windows builds use setup.py without a command")
    architecture = platform.machine()
    supported = {"x86_64", "arm64"} if target == "Darwin" else {"AMD64", "x86_64"}
    if architecture not in supported or struct.calcsize("P") != 8:
        parser.error(
            "Use a native 64-bit x86_64/arm64 macOS or x64 Windows interpreter"
        )
    return parser, args, target, architecture


def source_inputs():
    source_files = {
        ROOT / name
        for name in (
            "setup.py",
            "main.py",
            "gui_main.py",
            "cli_main.py",
            "win.spec",
            "hook-tkinterdnd2.py",
            "pyproject.toml",
            "requirements.txt",
            "requirements-build.txt",
            "poetry.lock",
        )
        if (ROOT / name).is_file()
    }
    source_files.update(
        path
        for path in (ROOT / "sd_prompt_reader").rglob("*")
        if path.is_file()
        and path.suffix not in {".pyc", ".pyo"}
        and not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(ROOT).parts
        )
    )
    return source_files


def describe_inputs(version, architecture, argv):
    import tkinter

    source_files = source_inputs()
    inputs = {
        "version": str(version),
        "source": str(ROOT),
        "command": sys.argv if argv is None else [str(ROOT / "setup.py"), *argv],
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "architecture": architecture,
        "tcl_version": tkinter.TclVersion,
        "tk_version": tkinter.TkVersion,
        "packages": {
            dist.metadata["Name"]: dist.version for dist in metadata.distributions()
        },
        "input_sha256": {
            path.relative_to(ROOT)
            .as_posix(): hashlib.sha256(path.read_bytes())
            .hexdigest()
            for path in sorted(source_files)
        },
    }
    return inputs


def main(argv=None):
    parser, args, target, architecture = build_arguments(argv)
    try:
        version = get_version()
        import tkinter

        if tkinter.TkVersion != 8.6 or tkinter.TclVersion != 8.6:
            raise ValueError(
                "Desktop builds require Tcl/Tk 8.6; verify runtime patchlevels and TkDND separately"
            )
        output = args.output_dir.resolve()
        if output == ROOT or output in ROOT.parents:
            raise ValueError(
                "Output must not be the source directory or one of its parents"
            )
        if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "build"):
            raise ValueError("Outputs inside the source tree must be under build/")
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise ValueError(
                "Output directory must be fresh and empty; choose a new path"
            )
    except (OSError, ValueError, ImportError) as error:
        parser.error(str(error))

    inputs = describe_inputs(version, architecture, argv)
    if args.preflight:
        print(json.dumps(inputs, indent=2, sort_keys=True))
        return
    output.mkdir(parents=True, exist_ok=True)
    (output / "build-inputs.json").write_text(
        json.dumps(inputs, indent=2, sort_keys=True) + "\n"
    )
    previous = Path.cwd()
    try:
        os.chdir(ROOT)
        if target == "Darwin":
            build_mac(version, output, architecture)
        else:
            build_windows(version, output)
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    main()
