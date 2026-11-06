# Building desktop applications

These instructions apply to current source, not the published v1.3.5 binaries.
Build macOS Intel, macOS Apple Silicon and Windows x64 separately on their native
platforms. A build on one target does not validate another target.

## Prepare the interpreter

Use a dedicated, patched 64-bit CPython with working tkinter and **Tcl/Tk 8.6**.
Do not replace your development environment. Tk 9 is not compatible with the
current TkDND package. Check the actual runtime, not just the Python version:

```sh
python -c "import sys, ssl, platform; print(sys.version); print(platform.machine()); print(ssl.OPENSSL_VERSION)"
python -c "import tkinter; r=tkinter.Tk(); print(r.tk.call('info', 'patchlevel'), r.tk.call('package', 'provide', 'Tk')); r.destroy()"
```

The Intel development build was exercised with CPython 3.11.18, Tcl/Tk 8.6.18
(Aqua), OpenSSL 3.5.9 LTS, py2app 0.28.10 and setuptools 84.2.1, on macOS 26.7.2
with Xcode 26.6 / SDK 26.5. Python 3.11 security releases are
[source-only](https://www.python.org/downloads/release/python-31118/); an old
3.11 installer does not supply the same fixes. This is a tested build lane,
not a requirement to use Python 3.11 for every source installation.

For a custom macOS interpreter, build a framework Python in a private prefix.
Select Tcl/Tk explicitly with `TCLTK_CFLAGS` / `TCLTK_LIBS` and OpenSSL with
`--with-openssl`, following the [CPython configuration documentation](https://docs.python.org/3.11/using/configure.html).
Inspect installation destinations before installing, including companion apps.
Record source checksums, configure arguments, compiler/SDK, deployment targets,
and actual `_tkinter`/SSL linkage. Avoid unintentionally linking Homebrew libraries
that require a newer OS than the intended target. A deployment-target flag alone
does not establish compatibility with that OS.

Windows needs its own verified Python/Tcl/Tk input. The Windows dependency graph
has been resolved and audited, but a native Windows build has not yet been
validated. Choosing the latest Python installer alone does not guarantee Tk 8.6.

## Install build dependencies

Work from a clean source copy containing only project files. Create a new virtual
environment with the selected interpreter, activate it, then install the build
requirements. On Windows, activate `.build-env\Scripts\activate`; on macOS use
`source .build-env/bin/activate`.

```sh
python -m venv .build-env
# Activate .build-env before continuing.
python -m pip install pip==26.3
python -m pip install -r requirements-build.txt
python -m pip check
python -m pip freeze > build-environment.txt
```

Pip 26.3 is the reviewed bootstrap version for this checkpoint. The Intel
validation also used `uv` 0.13.6 with a `--without-pip` venv and a fully hashed
requirements snapshot; it did not copy the base interpreter's bootstrap packages.

`requirements-build.txt` pins the reviewed desktop tools and includes runtime
requirements. Transitive runtime ranges can still resolve differently later;
preserve a fully resolved, hashed requirements snapshot and downloaded inputs
when reproducing a particular build. Also record the bootstrap/build tools used
to install source distributions. Audit the resolved build graph separately from
runtime-only dependencies. Do not copy historical wheels from `whl/` by default.

The Windows pins use PyInstaller 6.22.3, hooks-contrib 2026.9 and
pyinstaller-versionfile 3.1.0. They exceed the 6.22.1 fix for
[GHSA-9fxf-4qw3-ghmr](https://github.com/pyinstaller/pyinstaller/security/advisories/GHSA-9fxf-4qw3-ghmr).
Updating tools does not patch previously published executables or establish that
every historical advisory is exploitable through this application.

## Build

Use a new, empty output directory for each build. Paths below are examples;
replace them with absolute paths outside the source copy.

macOS:

```sh
python setup.py py2app --preflight --output-dir /absolute/path/desktop-01
python setup.py py2app --output-dir /absolute/path/desktop-01
```

Windows:

```powershell
python setup.py --preflight --output-dir C:\builds\desktop-01
python setup.py --output-dir C:\builds\desktop-01
```

Preflight prints selected inputs without writing files. The build writes
`build-inputs.json`, intermediate files and `dist/` under the output directory.
It does not update dependencies, invoke Poetry or rewrite version source. The
versions in `pyproject.toml` and `sd_prompt_reader/__version__.py` must agree.
The manifest records interpreter/platform/package versions and source/resource
hashes. macOS also records actual Tcl/Tk patchlevels and script hashes in
`tcl-tk-inputs.json`, copies those script libraries into the app, and generates a
bundle-relative bootstrap under the output directory. Keep native-toolchain
provenance alongside these records.

macOS produces `dist/SD Prompt Reader.app`. The Windows spec produces two one-file
executables: `SD Prompt Reader.exe` for the GUI and `SD Prompt Reader CLI.exe`
for the CLI. CustomTkinter data and version resources come from the active build
environment/output directory, rather than a developer's hardcoded venv path.

## Validate the output

Move the application away from its source/output tree. Check it with the build
interpreter and environment unavailable, using generated images only:

- Start the GUI and inspect icons, themes, fonts and TkDND initialization.
- Open PNG, JPEG and WebP images; test native picker, explicit app-target opening,
  and drag/drop with spaces, Unicode and braces in paths. The single-image
  reader opens the first file from a dropped list. Check normal window closing.
- Copy raw metadata, export, edit/save and clear; reopen outputs and check metadata,
  pixels and transparency. Check visible errors when an output cannot be written.
- Exercise CLI help, complete/partial reads, `--raw` recovery, export, write and
  clear with captured/redirected streams. Check failure exit codes.
- Inspect architecture, linked libraries and signatures. Rebuild from a fresh
  source/output copy and compare recorded inputs; successful repeat builds do not
  imply byte-identical output.

For the macOS bundle CLI:

```sh
"/path/SD Prompt Reader.app/Contents/MacOS/SD Prompt Reader" --help
"/path/SD Prompt Reader.app/Contents/MacOS/SD Prompt Reader" -i example.png
```

On Windows, invoke `"SD Prompt Reader CLI.exe" --help` or use `&` before the
quoted executable path in PowerShell. The GUI executable does not depend on stdin
being a terminal. On macOS, an explicit CLI option selects the CLI; an image
argument selects the GUI.

The current Intel TkDND binary has a macOS **12.0** minimum load-command version,
so this build cannot retain earlier macOS compatibility claims. Its Python/Tk
10.15 build flags do not lower that requirement. The actual oldest supported OS
still needs native testing. Extra ARM resources/universal extension wheels do
not make an Intel application universal.

Build success, native interaction, downloaded-package installation, Developer ID
signing/notarization and release publication are separate checks. The local Intel
candidate is unsigned and is not a notarized release. Native Windows and Apple
Silicon artifacts, physical desktop interactions, normal window closing and
oldest-OS behavior require
their own evidence before distribution.

## Native CI and local candidate pipeline

`.github/workflows/desktop-build.yml` is manually triggered. It selects Windows
x64 (`windows-2022`), Intel macOS (`macos-26-intel`), Apple Silicon macOS
(`macos-26`), or all three. Jobs run independently. The workflow must exist on the
default branch before its manual trigger is available; adding it locally does
not register or run it on GitHub.

The preparation Python is distinct from the privately built application Python.
`tools/desktop/build_macos.sh` builds the pinned framework/Tcl/Tk/OpenSSL inputs
for either native Mac architecture. `tools/desktop/build_windows.ps1` builds the
Windows runtime from pinned inputs in `windows-inputs.json`. Both require a fresh
private prefix, verify downloads and record actual native versions/linkage. They
do not replace the host interpreter or require a custom PyInstaller bootloader.

With Python 3.11+ and uv 0.13.6 available, the same orchestration runs locally:

```sh
python tools/desktop/build.py --target macos-x86_64 --stage toolchain --work-dir /absolute/fresh/toolchain-check
python tools/desktop/build.py --target macos-x86_64 --stage candidate --work-dir /absolute/fresh/candidate-check
```

Use `macos-arm64` on Apple Silicon or `windows-x64` on Windows. On Windows, use an
absolute Windows output path. macOS private compilation paths must not contain
whitespace. `--preflight` checks native selection and fresh paths without writing
outputs. `--python` plus `--runtime-receipt` explicitly reuses a previously
prepared interpreter for local iteration; its external installation is not
renamed. Fresh builds hide their owned runtime during standalone checks.

Toolchain mode checks the prepared runtime, TkDND, package consistency and scoped
advisories. Candidate mode additionally requires the selected native input review,
builds twice, relocates and verifies the artifacts with source/build environments
unavailable, then creates a development archive. The summary records exact scope,
failures, source hashes and whether an explicitly reused runtime stayed available.

Dependency resolution and installation use hashed target requirements. Source
builds may use only the exact, wheel-only setuptools backend pinned in
`requirements-build.txt`, with its own required hashes; that same version must
also pass the target dependency audit. An unexpected backend requirement fails
the build rather than installing an unreviewed build dependency.

Only passed candidate archives can be retained when `retain_candidate` is selected
in Actions. They expire after seven days and contain the app/two EXEs, sanitized
provenance, checksums and [manual checks](../tools/desktop/MANUAL_CHECK.md).
macOS tar archives preserve executable permissions and symlinks. Existing private
`tests/`, images and extracted metadata are not used or uploaded; fresh checks
generate synthetic data at runtime. Nothing creates a tag or GitHub Release.

Download retained archives from the Actions run's Artifacts section, verify their
checksums and test on the corresponding platform before release. Signed-in users
with repository read access can download these artifacts; they are not private
distribution. Native Windows/ARM execution and physical checks must be recorded
on those targets; local syntax/input validation alone does not establish them.
