"""Extract pinned, data-only source tarballs into a new directory."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import sys
import tarfile


def safe_parts(name):
    parts = PurePosixPath(name).parts
    if not parts or name.startswith("/") or PureWindowsPath(name).drive:
        raise ValueError(f"Unsafe archive path: {name!r}")
    for part in parts:
        reserved = part.split(".")[0].upper()
        if (
            part in (".", "..")
            or part.endswith((".", " "))
            or any(ord(char) < 32 or char in '<>:"\\|?*' for char in part)
            or reserved in {"CON", "PRN", "AUX", "NUL"}
            or re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", reserved)
        ):
            raise ValueError(f"Unsafe archive path: {name!r}")
    return parts


def checked_members(archive):
    entries = []
    paths = {}
    roots = set()
    for member in archive.getmembers():
        if not (member.isdir() or member.isreg()):
            raise ValueError(f"Unsupported archive entry: {member.name!r}")
        parts = safe_parts(member.name)
        roots.add(parts[0])
        if len(parts) == 1:
            if not member.isdir():
                raise ValueError("Archive root must be a directory")
            continue
        relative = Path(*parts[1:])
        key = relative.as_posix().casefold()
        if key in paths:
            raise ValueError(f"Duplicate archive path: {member.name!r}")
        paths[key] = member.isdir()
        entries.append((member, relative))
    if len(roots) != 1 or not entries:
        raise ValueError("Archive must contain exactly one populated source root")
    for member, relative in entries:
        for parent in relative.parents:
            if paths.get(parent.as_posix().casefold()) is False:
                raise ValueError(f"File used as a directory: {member.name!r}")
    return roots.pop(), entries


def extract(archive_path, output, expected):
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError("Expected SHA256 must contain 64 hexadecimal characters")
    # Keep the verified file descriptor open through extraction.
    with archive_path.open("rb") as source:
        digest = hashlib.sha256()
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
        if digest.hexdigest() != expected.lower():
            raise ValueError("Source archive SHA256 mismatch")
        source.seek(0)
        with tarfile.open(fileobj=source, mode="r:*") as archive:
            root, entries = checked_members(archive)
            output.mkdir(parents=True, exist_ok=False)
            try:
                for member, relative in entries:
                    destination = output / relative
                    destination.resolve().relative_to(output.resolve())
                    if member.isdir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as reader:
                        with destination.open("xb") as writer:
                            shutil.copyfileobj(reader, writer)
                    destination.chmod(0o755 if member.mode & 0o111 else 0o644)
            except Exception:
                shutil.rmtree(output)
                raise
    return {"archive_root": root, "files": sum(m.isreg() for m, _ in entries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        report = extract(args.archive, args.output_dir, args.sha256)
    except (OSError, ValueError, tarfile.TarError) as error:
        print(f"Extraction failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
