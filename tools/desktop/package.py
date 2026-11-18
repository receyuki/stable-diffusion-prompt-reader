#!/usr/bin/env python3
"""Package a passed desktop artifact using a strict, reviewed whitelist."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile

TARGETS = ("macos-x86_64", "macos-arm64", "windows-x64")
EXES = ("SD Prompt Reader.exe", "SD Prompt Reader CLI.exe")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--artifact", type=Path, required=True)
    result.add_argument("--target", choices=TARGETS, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--revision", required=True)
    result.add_argument(
        "--verification",
        type=Path,
        required=True,
        help="Passed artifact verification JSON",
    )
    result.add_argument(
        "--manifest",
        type=Path,
        action="append",
        default=[],
        help="Explicit JSON provenance input (repeatable)",
    )
    result.add_argument(
        "--report",
        type=Path,
        required=True,
        help="New package receipt outside the archive",
    )
    return result


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def identity(artifact, target):
    records = []
    paths = (
        sorted(artifact.rglob("*"))
        if target.startswith("macos")
        else [artifact / n for n in EXES]
    )
    for path in paths:
        relative = path.relative_to(artifact).as_posix()
        if path.is_symlink():
            if target == "windows-x64" or os.path.isabs(os.readlink(path)):
                raise ValueError("Artifact requires portable relative symlinks")
            if not path.resolve().is_relative_to(artifact.resolve()):
                raise ValueError("Artifact symlink escapes app")
            records.append({"path": relative, "symlink": os.readlink(path)})
        elif path.is_file():
            records.append(
                {
                    "path": relative,
                    "sha256": digest(path),
                    "mode": path.stat().st_mode & 0o777,
                }
            )
        elif not path.is_dir():
            raise ValueError("Unsupported special artifact file")
    if not records:
        raise ValueError("Empty artifact")
    return (
        hashlib.sha256(
            json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        records,
    )


def sanitize(value):
    """Keep useful facts while dropping logs, arbitrary strings and local paths."""
    if isinstance(value, dict):
        return {
            k: sanitize(v)
            for k, v in value.items()
            if k
            not in (
                "stdout",
                "stderr",
                "module_origins",
                "command",
                "error",
            )
        }
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        # Native dependency install names are useful but machine prefixes are not.
        if value.startswith("/") or re.search(
            r"[A-Za-z]:[\\/]|(?:^|[\s=\"\'])/(?!/)", value
        ):
            return "[local path omitted]"
    return value


def validate_package_paths(args):
    if not all(
        p.is_absolute()
        for p in (
            args.artifact,
            args.output_dir,
            args.report,
            args.verification,
            *args.manifest,
        )
    ):
        raise ValueError("All input/output paths must be absolute")
    artifact, output = args.artifact.resolve(), args.output_dir.resolve()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.revision):
        raise ValueError("--revision must be the full 40-character source SHA")
    if not artifact.is_dir():
        raise ValueError("Artifact directory missing")
    if (
        output.exists()
        or output.is_relative_to(artifact)
        or artifact.is_relative_to(output)
    ):
        raise ValueError("Output directory must be fresh and outside artifact")
    if not output.parent.is_dir():
        raise ValueError("Output parent must exist")
    if args.report.resolve().is_relative_to(artifact):
        raise ValueError("Package report must be outside the input artifact")
    if args.report.exists() or not args.report.parent.is_dir():
        raise ValueError("Package report must be a new file with an existing parent")
    return artifact, output


def verified_artifact(args, artifact):
    report = json.loads(args.verification.read_text(encoding="utf-8"))
    actual, files = identity(artifact, args.target)
    if (
        report.get("schema_version") != 1
        or report.get("kind") != "artifact"
        or report.get("status") != "passed"
        or report.get("target") != args.target
        or report.get("artifact", {}).get("identity_sha256") != actual
    ):
        raise ValueError(
            "Passed target-matched artifact verification report required; artifact must be unchanged"
        )
    required = {"artifact-metadata", "artifact-unchanged"}
    if not required.issubset({c.get("name") for c in report.get("checks", [])}):
        raise ValueError(
            "Verification must include artifact metadata and unchanged-content gates"
        )
    if not report.get("checks") or any(
        c.get("status") != "passed" for c in report["checks"]
    ):
        raise ValueError("Verification checks must all pass")
    if args.target.startswith("macos") and artifact.suffix != ".app":
        raise ValueError("macOS artifact must be an .app directory")
    for name in EXES if args.target == "windows-x64" else ():
        if not (artifact / name).is_file():
            raise ValueError("Both independent Windows executables required")
    return report, actual, files


def write_archive(archive, artifact, manifest, report, manual):
    with tempfile.TemporaryDirectory(prefix="sdpr-package-") as folder:
        metadata = Path(folder)
        (metadata / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (metadata / "validation.json").write_text(
            json.dumps(sanitize(report), indent=2) + "\n"
        )
        shutil.copyfile(manual, metadata / "MANUAL_CHECK.md")
        payload = (
            [(artifact, artifact.name)]
            if manifest["target"].startswith("macos")
            else [(artifact / name, name) for name in EXES]
        )
        checksums = []
        for entry in manifest["artifact_files"]:
            if "sha256" in entry:
                prefix = (
                    artifact.name + "/"
                    if manifest["target"].startswith("macos")
                    else ""
                )
                checksums.append(entry["sha256"] + "  " + prefix + entry["path"])
        checksums.extend(
            digest(metadata / name) + "  " + name
            for name in ("manifest.json", "validation.json", "MANUAL_CHECK.md")
        )
        (metadata / "SHA256SUMS").write_text("\n".join(checksums) + "\n")
        payload += [
            (metadata / name, name)
            for name in (
                "manifest.json",
                "validation.json",
                "MANUAL_CHECK.md",
                "SHA256SUMS",
            )
        ]
        if archive.name.endswith(".tar.gz"):
            with tarfile.open(archive, "w:gz", dereference=False) as stream:

                def clean_owner(info):
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    return info

                for source, name in payload:
                    stream.add(source, arcname=name, filter=clean_owner)
        else:
            with zipfile.ZipFile(
                archive, "w", compression=zipfile.ZIP_DEFLATED
            ) as stream:
                for source, name in payload:
                    stream.write(source, name)


def main():
    args = parser().parse_args()
    try:
        artifact, output = validate_package_paths(args)
        report, actual, files = verified_artifact(args, artifact)
        provenance = [
            {
                "name": p.name,
                "sha256": digest(p),
                "data": sanitize(json.loads(p.read_text())),
            }
            for p in args.manifest
        ]
        manual = Path(__file__).with_name("MANUAL_CHECK.md")
        if not manual.is_file():
            raise ValueError("Manual checklist missing")
        output.mkdir()
        suffix = ".tar.gz" if args.target.startswith("macos") else ".zip"
        archive = output / (
            "SDPR-dev-" + args.target + "-" + args.revision[:12] + suffix
        )
        manifest = {
            "schema_version": 1,
            "development_candidate": True,
            "target": args.target,
            "source_revision": args.revision.lower(),
            "artifact_identity_sha256": actual,
            "artifact_files": files,
            "provenance": sanitize(provenance),
        }
        write_archive(archive, artifact, manifest, report, manual)
        receipt = {
            "schema_version": 1,
            "target": args.target,
            "source_revision": args.revision.lower(),
            "archive": str(archive),
            "filename": archive.name,
            "sha256": digest(archive),
            "size": archive.stat().st_size,
            "artifact_identity_sha256": actual,
        }
        (output / "package-report.json").write_text(
            json.dumps(receipt, indent=2) + "\n"
        )
        args.report.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print("Packaging failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
