"""Prepare and validate native desktop development candidates without publishing."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile

TARGETS = ("windows-x64", "macos-x86_64", "macos-arm64")
ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--target", choices=TARGETS, required=True)
    result.add_argument(
        "--stage", choices=("toolchain", "candidate"), default="toolchain"
    )
    result.add_argument("--work-dir", type=Path, required=True)
    result.add_argument("--source", type=Path, default=ROOT)
    result.add_argument(
        "--python", type=Path, help="Reuse an explicitly recorded native interpreter."
    )
    result.add_argument("--runtime-receipt", type=Path)
    result.add_argument(
        "--revision", help="Source commit SHA; otherwise read from Git."
    )
    result.add_argument("--uv", default="uv", help="Reviewed uv 0.13.6 executable.")
    result.add_argument(
        "--preflight",
        action="store_true",
        help="Check native selection and fresh paths without writing files.",
    )
    return result


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def validate(args):
    if sys.version_info < (3, 11):
        raise ValueError("Build preparation requires Python 3.11 or newer")
    if not args.work_dir.is_absolute():
        raise ValueError("Work directory must be an absolute path")
    native = (platform.system(), platform.machine())
    expected = {
        "macos-x86_64": ("Darwin", {"x86_64"}),
        "macos-arm64": ("Darwin", {"arm64"}),
        "windows-x64": ("Windows", {"AMD64", "x86_64"}),
    }[args.target]
    if (
        native[0] != expected[0]
        or native[1] not in expected[1]
        or struct.calcsize("P") != 8
    ):
        raise ValueError(
            f"{args.target} requires a matching native 64-bit host; found {native}"
        )
    if (
        args.target.startswith("macos-")
        and not args.python
        and any(c.isspace() for c in str(args.work_dir))
    ):
        raise ValueError("Private macOS toolchain paths must not contain whitespace")
    source = args.source.resolve(strict=True)
    output = args.work_dir.resolve()
    if (
        source == output
        or source.is_relative_to(output)
        or output.is_relative_to(source)
    ):
        raise ValueError(
            "Work directory must be outside the source tree and its ancestors"
        )
    forbidden = [Path(sys.base_prefix).resolve()]
    if os.name == "nt":
        forbidden += [
            Path(value).resolve()
            for key in ("ProgramFiles", "ProgramFiles(x86)", "SystemRoot")
            if (value := os.environ.get(key))
        ]
    else:
        forbidden += [
            Path(value).resolve()
            for value in (
                "/System",
                "/Library",
                "/usr",
                "/opt",
                "/Applications",
                "/etc",
                "/dev",
                "/bin",
                "/sbin",
            )
        ]
        var = Path("/private/var")
        if output.is_relative_to(var) and not output.is_relative_to(
            Path(tempfile.gettempdir()).resolve()
        ):
            raise ValueError("Work directory must not be under a system data prefix")
    if any(
        output.is_relative_to(path) or path.is_relative_to(output) for path in forbidden
    ):
        raise ValueError(
            "Work directory must not overlap a global interpreter or system prefix"
        )
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Work directory must be fresh and empty")
    if bool(args.python) != bool(args.runtime_receipt):
        raise ValueError("--python and --runtime-receipt must be supplied together")
    revision = args.revision
    if revision is None:
        revision = subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
        ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError(
            "Source revision must be a full 40-character lowercase Git SHA"
        )
    if args.python:
        interpreter = args.python.resolve(strict=True)
        receipt = json.loads(args.runtime_receipt.read_text(encoding="utf-8"))
        if (
            receipt.get("target") != args.target
            or Path(receipt["python"]).resolve() != interpreter
        ):
            raise ValueError(
                "Runtime receipt must describe the supplied interpreter and target"
            )
    return source, output, revision


def run(command, log, *, cwd=None, env=None):
    print(f"Running {log.stem}", flush=True)
    with log.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps([str(part) for part in command]) + "\n")
        stream.flush()
        result = subprocess.run(
            [str(part) for part in command],
            cwd=cwd,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    if result.returncode:
        raise RuntimeError(f"{log.stem} failed (exit {result.returncode}); see {log}")


def environment(work):
    result = dict(os.environ)
    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "TCL_LIBRARY",
        "TK_LIBRARY",
        "DYLD_LIBRARY_PATH",
        "DYLD_FRAMEWORK_PATH",
    ):
        result.pop(key, None)
    result.update(
        PYTHONDONTWRITEBYTECODE="1",
        UV_CACHE_DIR=str(work / "uv-cache"),
        UV_PYTHON_DOWNLOADS="never",
    )
    return result


def source_files(source):
    names = (
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
        "README.md",
        "LICENSE",
        "file_version_info.txt",
    )
    files = [source / name for name in names]
    package = source / "sd_prompt_reader"
    for path in package.rglob("*"):
        if any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(package).parts
        ):
            continue
        if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
            if not path.resolve().is_relative_to(package.resolve()):
                raise ValueError(
                    f"Package input escapes source tree: {path.relative_to(source)}"
                )
            files.append(path)
    if not package.is_dir() or any(not path.is_file() for path in files):
        raise ValueError("Source tree lacks required desktop build inputs")
    return files


def snapshot(source, destination, files):
    destination.mkdir()
    for path in files:
        copied = destination / path.relative_to(source)
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copied)


@contextmanager
def hidden_paths(paths):
    """Hide only caller-owned build paths, restoring them even on check failure."""
    pairs = [(path, path.with_name(path.name + ".unavailable")) for path in paths]
    if any(not path.exists() or hidden.exists() for path, hidden in pairs):
        raise ValueError(
            "Standalone check requires existing private paths and unused backup names"
        )
    moved = []
    try:
        for path, hidden in pairs:
            path.rename(hidden)
            moved.append((path, hidden))
        yield
    finally:
        for path, hidden in reversed(moved):
            hidden.rename(path)


def venv_python(directory):
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def resolve_requirements(uv, python, source, work, logs, env):
    """Resolve the sole reviewed backend from wheels before any sdist metadata."""
    requirements = source / "requirements-build.txt"
    pins = [
        match[1]
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if (match := re.fullmatch(r"setuptools==(\d+(?:\.\d+)+)", line.strip()))
    ]
    if len(pins) != 1:
        raise ValueError("Exactly one reviewed setuptools== version is required")
    backend_input = work / "backend-requirements.in"
    backend_input.write_text("setuptools==" + pins[0] + "\n", encoding="utf-8")
    backend_lock = work / "backend-requirements.lock"
    run(
        [
            uv,
            "pip",
            "compile",
            backend_input,
            "--python",
            python,
            "--no-build",
            "--no-deps",
            "--generate-hashes",
            "--no-python-downloads",
            "--output-file",
            backend_lock,
        ],
        logs / "resolve-backend.log",
        env=env,
    )
    lock = work / "requirements.lock"
    run(
        [
            uv,
            "pip",
            "compile",
            requirements,
            "--python",
            python,
            "--generate-hashes",
            "--no-python-downloads",
            "--only-binary",
            "setuptools",
            "--build-constraints",
            backend_lock,
            "--require-build-hashes",
            "--output-file",
            lock,
        ],
        logs / "resolve.log",
        env=env,
    )
    return lock, backend_lock, pins[0]


def backend_audit_binding(pin, report):
    """The wheel-only seed must be present and clean in the audited target graph."""
    matches = [
        item
        for item in json.loads(report.read_text(encoding="utf-8"))["dependencies"]
        if item["name"].lower() == "setuptools"
    ]
    if (
        len(matches) != 1
        or matches[0].get("version") != pin
        or matches[0].get("vulns")
        or matches[0].get("skip_reason")
    ):
        raise ValueError(
            "Reviewed backend must match a clean audited target distribution"
        )
    return {"setuptools": pin}


def sync_requirements(uv, python, lock, log, env, backend_lock):
    """Allow only the reviewed wheel-only backend in isolated source builds."""
    run(
        [
            uv,
            "pip",
            "sync",
            "--python",
            python,
            "--require-hashes",
            "--only-binary",
            "setuptools",
            "--build-constraints",
            backend_lock,
            "--require-build-hashes",
            lock,
        ],
        log,
        env=env,
    )


def audit(uv, lock, work, logs, env):
    tools_env = work / "audit-env"
    run(
        [uv, "venv", "--python", sys.executable, "--no-python-downloads", tools_env],
        logs / "audit-env.log",
        env=env,
    )
    python = venv_python(tools_env)
    run(
        [uv, "pip", "install", "--python", python, "pip-audit==2.10.1"],
        logs / "audit-tools.log",
        env=env,
    )
    report = work / "package-audit.json"
    run(
        [
            python,
            "-m",
            "pip_audit",
            "-r",
            lock,
            "--no-deps",
            "--disable-pip",
            "--strict",
            "--require-hashes",
            "--cache-dir",
            work / "audit-cache",
            "--progress-spinner",
            "off",
            "--format",
            "json",
            "--output",
            report,
        ],
        logs / "package-audit.log",
        env=env,
    )
    data = json.loads(report.read_text(encoding="utf-8"))
    if any(
        item.get("vulns") or item.get("skip_reason") for item in data["dependencies"]
    ):
        raise RuntimeError("Package audit contains findings or skipped distributions")
    return report


def execute(args, source, work, revision):
    work.mkdir(parents=True, exist_ok=True)
    logs = work / "logs"
    logs.mkdir()
    env = environment(work)
    summary = {
        "schema_version": 1,
        "target": args.target,
        "stage": args.stage,
        "revision": revision,
        "publishes": False,
        "status": "running",
    }
    summary_path = work / "summary.json"
    try:
        version = subprocess.check_output(
            [args.uv, "--version"], text=True, env=env
        ).strip()
        if not version.startswith("uv 0.13.6 "):
            raise ValueError(f"Expected reviewed uv 0.13.6; found {version}")
        summary["uv"] = version
        files = source_files(source)
        hashes = {path.relative_to(source).as_posix(): digest(path) for path in files}
        provenance = work / "source-inputs.json"
        git_state = subprocess.run(
            [
                "git",
                "-C",
                str(source),
                "status",
                "--porcelain",
                "--untracked-files=normal",
            ],
            text=True,
            capture_output=True,
        )
        write_json(
            provenance,
            {
                "revision": revision,
                "working_tree_dirty": (
                    bool(git_state.stdout) if git_state.returncode == 0 else None
                ),
                "sha256": hashes,
                "helper_sha256": {
                    p.name: digest(p)
                    for p in TOOLS.iterdir()
                    if p.is_file() and not p.name.startswith(".")
                },
            },
        )
        source_copy = work / "source"
        snapshot(source, source_copy, files)
        runtime_receipt = work / "runtime.json"
        if args.python:
            shutil.copy2(args.runtime_receipt, runtime_receipt)
            summary["runtime_origin"] = "explicitly reused interpreter"
        else:
            runtime_root = work / "runtime-build"
            if args.target.startswith("macos-"):
                command = [
                    "bash",
                    TOOLS / "build_macos.sh",
                    "--root",
                    runtime_root,
                    "--target",
                    args.target,
                    "--receipt",
                    runtime_receipt,
                ]
            else:
                command = [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    TOOLS / "build_windows.ps1",
                    "-Root",
                    runtime_root,
                    "-Target",
                    args.target,
                    "-Receipt",
                    runtime_receipt,
                ]
            run(command, logs / "native-toolchain.log", env=env)
            summary["runtime_origin"] = "fresh native build"
        native = json.loads(runtime_receipt.read_text(encoding="utf-8"))
        if native.get("target") != args.target or native.get("schema_version") != 1:
            raise ValueError("Native builder returned a mismatched receipt")
        python = Path(native["python"]).resolve(strict=True)
        build_env = work / "build-env"
        run(
            [args.uv, "venv", "--python", python, "--no-python-downloads", build_env],
            logs / "build-env.log",
            env=env,
        )
        python = venv_python(build_env)
        lock, backend_lock, backend_pin = resolve_requirements(
            args.uv, python, source_copy, work, logs, env
        )
        sync_requirements(
            args.uv, python, lock, logs / "install.log", env, backend_lock
        )
        run(
            [args.uv, "pip", "check", "--python", python],
            logs / "dependencies.log",
            env=env,
        )
        runtime_check = work / "runtime-check.json"
        run(
            [
                sys.executable,
                TOOLS / "verify.py",
                "runtime",
                "--python",
                python,
                "--target",
                args.target,
                "--output",
                runtime_check,
                "--runtime-receipt",
                runtime_receipt,
            ],
            logs / "runtime-check.log",
            env=env,
        )
        package_audit = audit(args.uv, lock, work, logs, env)
        backend_binding = backend_audit_binding(backend_pin, package_audit)
        build_dependency_controls = work / "build-dependency-controls.json"
        write_json(
            build_dependency_controls,
            {
                "requirements_lock_sha256": digest(lock),
                "isolated_build_constraints_sha256": digest(backend_lock),
                "resolver_build_constraints_sha256": digest(backend_lock),
                "backend_requirement_source": "requirements-build.txt exact setuptools pin",
                "backend_requirements": backend_binding,
                "backend_seed_wheel_only": True,
                "require_build_hashes": True,
                "audit_report_sha256": digest(package_audit),
                "installation_log_sha256": digest(logs / "install.log"),
                "audited_target_distributions": {
                    item["name"]: item["version"]
                    for item in json.loads(package_audit.read_text(encoding="utf-8"))[
                        "dependencies"
                    ]
                },
                "audit_scope": "Every distribution in the target lock, including the exact wheel-only setuptools seed; unlisted or unhashed backend requirements fail closed during resolution and installation",
            },
        )
        summary["build_dependency_controls"] = str(build_dependency_controls)
        summary["native_review"] = native.get(
            "native_review",
            {"status": "pending", "notes": ["No native review receipt"]},
        )
        summary["runtime_check"] = str(runtime_check)
        if args.stage == "candidate":
            if summary["native_review"].get("status") != "approved":
                raise RuntimeError(
                    "Native input review is pending; candidate stage is blocked"
                )
            reports, artifacts = [], []
            build_inputs = []
            for number in (1, 2):
                output = work / f"build-{number}"
                command = [python, source_copy / "setup.py"]
                if args.target.startswith("macos-"):
                    command.append("py2app")
                run(
                    [*command, "--output-dir", output],
                    logs / f"bundle-{number}.log",
                    env=env,
                )
                build_inputs.append(
                    json.loads(
                        (output / "build-inputs.json").read_text(encoding="utf-8")
                    )
                )
                relocated = work / f"relocated-{number}"
                relocated.mkdir()
                artifact = (
                    relocated / "SD Prompt Reader.app"
                    if args.target.startswith("macos-")
                    else relocated / "dist"
                )
                built = (
                    output / "dist/SD Prompt Reader.app"
                    if args.target.startswith("macos-")
                    else output / "dist"
                )
                shutil.move(str(built), artifact)
                artifacts.append(artifact)
            offline = [source_copy, build_env]
            if not args.python:
                offline.append(work / "runtime-build")
            summary["standalone_environment"] = {
                "source_and_build_environment_hidden": True,
                "native_runtime_hidden": not bool(args.python),
                "reused_runtime_note": (
                    "Explicitly reused external runtime is not renamed; native closure/origins are still checked"
                    if args.python
                    else None
                ),
            }
            with hidden_paths(offline):
                for number, artifact in enumerate(artifacts, 1):
                    report = work / f"artifact-check-{number}.json"
                    run(
                        [
                            sys.executable,
                            TOOLS / "verify.py",
                            "artifact",
                            "--artifact",
                            artifact,
                            "--target",
                            args.target,
                            "--expected-version",
                            build_inputs[number - 1]["version"],
                            "--output",
                            report,
                        ],
                        logs / f"artifact-check-{number}.log",
                        env=env,
                    )
                    reports.append(report)
            if (
                build_inputs[0]["input_sha256"] != build_inputs[1]["input_sha256"]
                or build_inputs[0]["packages"] != build_inputs[1]["packages"]
            ):
                raise RuntimeError("Repeat builds used different source/package inputs")
            if any(
                digest(source_copy / name) != value for name, value in hashes.items()
            ):
                raise RuntimeError("Bundling modified source inputs")
            package_report = work / "package-report.json"
            command = [
                sys.executable,
                TOOLS / "package.py",
                "--artifact",
                artifacts[-1],
                "--target",
                args.target,
                "--output-dir",
                work / "candidate",
                "--revision",
                revision,
                "--verification",
                reports[-1],
                "--report",
                package_report,
            ]
            for manifest in (
                provenance,
                runtime_receipt,
                runtime_check,
                package_audit,
                build_dependency_controls,
                reports[0],
                work / "build-2/build-inputs.json",
            ):
                command.extend(["--manifest", manifest])
            run(command, logs / "package.log", env=env)
            summary["package"] = json.loads(package_report.read_text(encoding="utf-8"))
            summary["artifact_checks"] = [str(path) for path in reports]
        summary["status"] = "passed"
        summary["validation_scope"] = (
            "native toolchain feasibility"
            if args.stage == "toolchain"
            else "native automated development candidate; manual/distribution checks separate"
        )
    except Exception as error:
        summary["status"] = "failed"
        summary["error"] = str(error)
        raise
    finally:
        write_json(summary_path, summary)
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main():
    cli = parser()
    args = cli.parse_args()
    try:
        source, output, revision = validate(args)
        if args.preflight:
            print(
                json.dumps(
                    {
                        "target": args.target,
                        "stage": args.stage,
                        "source": str(source),
                        "work_dir": str(output),
                        "revision": revision,
                        "publishes": False,
                    },
                    indent=2,
                )
            )
            return
        summary = execute(args, source, output, revision)
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output and summary.get("package"):
            archive = summary["package"].get("archive") or summary["package"].get(
                "path"
            )
            if isinstance(archive, dict):
                archive = archive["path"]
            if not isinstance(archive, str) or "\n" in archive or "\r" in archive:
                raise ValueError("Packager did not return a safe archive path")
            with Path(github_output).open("a", encoding="utf-8") as stream:
                stream.write(f"archive={archive}\n")
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as error:
        cli.exit(1, f"Build failed: {error}\n")


if __name__ == "__main__":
    main()
