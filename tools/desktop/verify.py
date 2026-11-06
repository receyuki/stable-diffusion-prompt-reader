#!/usr/bin/env python3
"""Exercise a native desktop runtime or relocated application (stdlib bootstrap)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import struct
import subprocess
import sys
import tempfile
import time
import zlib

TARGETS = {
    "macos-x86_64": ("Darwin", "x86_64"),
    "macos-arm64": ("Darwin", "arm64"),
    "windows-x64": ("Windows", "AMD64"),
}
EXES = ("SD Prompt Reader.exe", "SD Prompt Reader CLI.exe")
PROCESS_LOG = []


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="kind", required=True)
    for name in ("runtime", "artifact"):
        command = commands.add_parser(name)
        command.add_argument("--target", choices=TARGETS, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument(
            "--python" if name == "runtime" else "--artifact", type=Path, required=True
        )
        if name == "artifact":
            command.add_argument(
                "--expected-version",
                required=True,
                help="Authoritative source version from build-inputs.json",
            )
        if name == "runtime":
            command.add_argument(
                "--runtime-receipt",
                type=Path,
                help="Explicit native input/optional-module receipt",
            )
    return result


def clean_env():
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("PYTHON", "TCL", "TK", "DYLD_"))
        and k
        not in ("VIRTUAL_ENV", "LD_LIBRARY_PATH", "RESOURCEPATH", "_PY2APP_LAUNCHED_")
    }
    env["PYTHONNOUSERSITE"] = "1"
    env["PATH"] = (
        os.pathsep.join(
            (str(Path(os.environ["SystemRoot"]) / "System32"), os.environ["SystemRoot"])
        )
        if os.name == "nt"
        else "/usr/bin:/bin:/usr/sbin:/sbin"
    )
    return env


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def artifact_identity(artifact, target):
    """Content, relative layout, permissions and symlink targets bind a report."""
    paths = (
        sorted(artifact.rglob("*"))
        if target.startswith("macos")
        else [artifact / n for n in EXES]
    )
    records = []
    for path in paths:
        rel = path.relative_to(artifact).as_posix()
        if path.is_symlink():
            if target == "windows-x64" or os.path.isabs(os.readlink(path)):
                raise ValueError("Artifact requires portable relative symlinks: " + rel)
            if not path.resolve().is_relative_to(artifact.resolve()):
                raise ValueError("Artifact symlink escapes application: " + rel)
            records.append({"path": rel, "symlink": os.readlink(path)})
        elif path.is_file():
            records.append(
                {
                    "path": rel,
                    "sha256": digest(path),
                    "mode": path.stat().st_mode & 0o777,
                }
            )
        elif not path.is_dir():
            raise ValueError("Unsupported special artifact file: " + rel)
    if not records:
        raise ValueError("Artifact contains no files")
    encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return {
        "name": artifact.name,
        "path": str(artifact),
        "identity_sha256": hashlib.sha256(encoded).hexdigest(),
        "files": records,
    }


def unchanged_artifact(artifact, target, before):
    after = artifact_identity(artifact, target)
    assert (
        after["identity_sha256"] == before["identity_sha256"]
    ), "Artifact changed during verification"
    return {"identity_sha256": after["identity_sha256"], "unchanged": True}


def verify_execution_manifest(data):
    """Check a bounded PE manifest without permitting DTDs or entity loading."""
    from xml.parsers import expat

    if not 0 < len(data) <= 2 * 1024 * 1024:
        raise ValueError("Invalid manifest size")
    encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    text = data.decode(encoding).rstrip("\0")
    levels = []

    def reject_entities(*_):
        raise ValueError("Manifest DTDs and entities are forbidden")

    def collect_level(name, attributes):
        if name == "urn:schemas-microsoft-com:asm.v3}requestedExecutionLevel":
            levels.append(attributes)

    parser = expat.ParserCreate(namespace_separator="}")
    parser.StartDoctypeDeclHandler = reject_entities
    parser.EntityDeclHandler = reject_entities
    parser.ExternalEntityRefHandler = reject_entities
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.StartElementHandler = collect_level
    try:
        parser.Parse(text, True)
    except expat.ExpatError as error:
        raise ValueError("Invalid execution manifest XML") from error
    assert (
        len(levels) == 1
        and levels[0].get("level") == "asInvoker"
        and levels[0].get("uiAccess") == "false"
    ), "Unexpected EXE execution manifest"


def windows_metadata(path, base_version):
    """Read PE resources through data-only native APIs; never run the executable."""
    if os.name != "nt":
        raise ValueError(
            "Windows executable resources require native Windows validation"
        )
    import ctypes
    from ctypes import wintypes

    version = ctypes.WinDLL("version", use_last_error=True)
    version.GetFileVersionInfoSizeW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    version.GetFileVersionInfoW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    version.VerQueryValueW.argtypes = [
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.UINT),
    ]
    size = version.GetFileVersionInfoSizeW(str(path), None)
    assert size, "Missing EXE version resource: " + path.name
    buffer = ctypes.create_string_buffer(size)
    assert version.GetFileVersionInfoW(
        str(path), 0, size, buffer
    ), "Cannot read EXE version resource"

    def query(key):
        pointer, length = ctypes.c_void_p(), wintypes.UINT()
        assert version.VerQueryValueW(
            buffer, key, ctypes.byref(pointer), ctypes.byref(length)
        ), ("Missing version field: " + key)
        assert length.value and pointer.value, "Empty version field: " + key
        return pointer, length.value

    pointer, length = query("\\")
    assert length >= 52, "Truncated VS_FIXEDFILEINFO"
    fixed = struct.unpack("<13I", ctypes.string_at(pointer, 52))
    assert fixed[0] == 0xFEEF04BD, "Invalid VS_FIXEDFILEINFO signature"
    numbers = [int(part) for part in base_version.split(".")]
    numbers += [0] * (4 - len(numbers))
    expected = tuple(numbers)
    assert (
        tuple((part >> shift) & 0xFFFF for part in fixed[2:4] for shift in (16, 0))
        == expected
    ), "EXE FileVersion mismatch"
    assert (
        tuple((part >> shift) & 0xFFFF for part in fixed[4:6] for shift in (16, 0))
        == expected
    ), "EXE ProductVersion mismatch"
    fields = {}
    for name in (
        "FileVersion",
        "ProductVersion",
        "FileDescription",
        "ProductName",
        "InternalName",
        "OriginalFilename",
    ):
        pointer, length = query("\\StringFileInfo\\040904B0\\" + name)
        fields[name] = ctypes.wstring_at(pointer, length).rstrip("\0")
    for name in ("FileVersion", "ProductVersion"):
        assert fields[name] == ".".join(map(str, expected)), (
            "EXE version string mismatch: " + name
        )
    for name in ("FileDescription", "ProductName", "InternalName"):
        assert fields[name] == "SD Prompt Reader", "EXE identity mismatch: " + name
    # setup.py intentionally shares one version resource between both EXEs.
    assert (
        fields["OriginalFilename"] == "SD Prompt Reader.exe"
    ), "EXE OriginalFilename mismatch"

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
    kernel.LoadLibraryExW.restype = wintypes.HMODULE
    kernel.FreeLibrary.argtypes = [wintypes.HMODULE]
    kernel.FindResourceW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p]
    kernel.FindResourceW.restype = wintypes.HANDLE
    kernel.SizeofResource.argtypes = [wintypes.HMODULE, wintypes.HANDLE]
    kernel.SizeofResource.restype = wintypes.DWORD
    kernel.LoadResource.argtypes = [wintypes.HMODULE, wintypes.HANDLE]
    kernel.LoadResource.restype = wintypes.HANDLE
    kernel.LockResource.argtypes = [wintypes.HANDLE]
    kernel.LockResource.restype = ctypes.c_void_p
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMODULE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.LPARAM,
    )
    kernel.EnumResourceNamesW.argtypes = [
        wintypes.HMODULE,
        ctypes.c_void_p,
        callback_type,
        wintypes.LPARAM,
    ]
    handle = kernel.LoadLibraryExW(
        str(path), None, 0x2 | 0x20
    )  # DATAFILE | IMAGE_RESOURCE
    assert handle, "Cannot load EXE resources as data"
    resources = {}
    try:
        for kind in (24, 14, 3):  # RT_MANIFEST, RT_GROUP_ICON, RT_ICON
            entries = []
            errors = []

            def collect(module, resource_type, name, _):
                resource = kernel.FindResourceW(module, name, resource_type)
                size = kernel.SizeofResource(module, resource)
                loaded = kernel.LoadResource(module, resource)
                address = kernel.LockResource(loaded)
                if not resource or not address or not 0 < size <= 2 * 1024 * 1024:
                    errors.append("Invalid or oversized PE resource")
                    return False
                entries.append(ctypes.string_at(address, size))
                return True

            assert kernel.EnumResourceNamesW(
                handle, ctypes.c_void_p(kind), callback_type(collect), 0
            ), "Missing PE resource type " + str(kind)
            assert entries and not errors, "Unreadable PE resources: " + str(errors)
            resources[kind] = entries
    finally:
        kernel.FreeLibrary(handle)
    for manifest in resources[24]:
        verify_execution_manifest(manifest)
    return {
        **fields,
        "resource_counts": {
            str(kind): len(entries) for kind, entries in resources.items()
        },
        "manifest_sha256": [hashlib.sha256(data).hexdigest() for data in resources[24]],
        "resource_read_mode": "native data-only APIs",
    }


def artifact_metadata(artifact, target, expected_version):
    match = re.fullmatch(
        r"(\d+(?:\.\d+){1,3})(?:(?:a|b|rc)\d+|\.post\d+|\.dev\d+)?", expected_version
    )
    assert match, "Unsupported authoritative source version"
    base_version = match[1]
    if target == "windows-x64":
        return {
            "expected_version": expected_version,
            "executables": {
                name: windows_metadata(artifact / name, base_version) for name in EXES
            },
        }
    with (artifact / "Contents/Info.plist").open("rb") as stream:
        data = plistlib.load(stream)
    expected = {
        "CFBundleName": "SD Prompt Reader",
        "CFBundleDisplayName": "SD Prompt Reader",
        "CFBundleIdentifier": "com.receyuki.sd-prompt-reader",
        "CFBundleExecutable": "SD Prompt Reader",
        "CFBundleVersion": expected_version,
        "CFBundleShortVersionString": base_version,
    }
    for key, value in expected.items():
        assert data.get(key) == value, "Bundle metadata mismatch: " + key
    assert (
        artifact / "Contents/MacOS" / expected["CFBundleExecutable"]
    ).is_file(), "Bundle executable missing"
    expected_documents = [
        {
            "CFBundleTypeExtensions": ["png", "jpg", "jpeg", "webp"],
            "CFBundleTypeName": "Image File",
            "CFBundleTypeRole": "Viewer",
        }
    ]
    assert (
        data.get("CFBundleDocumentTypes") == expected_documents
    ), "Bundle document types mismatch"
    icon = data.get("CFBundleIconFile")
    assert (
        isinstance(icon, str) and Path(icon).name == icon and icon.endswith(".icns")
    ), "Invalid bundle icon name"
    assert (artifact / "Contents/Resources" / icon).is_file(), "Bundle icon missing"
    return {
        **expected,
        "CFBundleDocumentTypes": data["CFBundleDocumentTypes"],
        "CFBundleIconFile": icon,
    }


def run(command, cwd, env, timeout=90):
    try:
        child = subprocess.run(
            list(map(str, command)),
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
        result = {
            "returncode": child.returncode,
            "stdout": child.stdout,
            "stderr": child.stderr,
        }
        PROCESS_LOG.append({"executable": Path(command[0]).name, **result})
        return result
    except subprocess.TimeoutExpired as error:
        result = {
            "returncode": -1,
            "stdout": str(error.stdout or ""),
            "stderr": "Timed out: " + str(error.stderr or ""),
        }
        PROCESS_LOG.append({"executable": Path(command[0]).name, **result})
        return result


# This probe is authored here, rather than imported from the private regression suite.
RUNTIME_PROBE = r"""
import sys, json, platform, ssl, hashlib, zlib, ctypes, tkinter, importlib.util
from pathlib import Path
root = tkinter.Tk()
root.withdraw()
from tkinterdnd2 import TkinterDnD
version = TkinterDnD._require(root)
assert version, 'TkDND did not initialize'
assert hashlib.sha256(b'abc').hexdigest() == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
optional = {}
for name in ('bz2', 'lzma', 'sqlite3'):
    try:
        module = __import__(name)
    except ImportError:
        optional[name] = 'absent'
    else:
        if name == 'sqlite3':
            with module.connect(':memory:') as database:
                assert database.execute('select 6 * 7').fetchone()[0] == 42
        else:
            assert module.decompress(module.compress(b'native-operation')) == b'native-operation'
        optional[name] = 'operation-passed'
assert zlib.decompress(zlib.compress(b'native-operation')) == b'native-operation'
context = ssl.create_default_context()
assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
# Public throwaway localhost certificate/key: only used to prove rejection of an
# untrusted certificate on loopback. They are not credentials or trust anchors.
import socket, threading, tempfile
CERT = '-----BEGIN CERTIFICATE-----\nMIICwzCCAaugAwIBAgIJAJgQ6L/HjyPiMA0GCSqGSIb3DQEBCwUAMBQxEjAQBgNV\nBAMMCWxvY2FsaG9zdDAeFw0yNjExMDYwMzE0NTdaFw0zNjExMDMwMzE0NTdaMBQx\nEjAQBgNVBAMMCWxvY2FsaG9zdDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC\nggEBAMaYwThuLZgbtFJAWKeTjJ1vXHZvGU5+S2e7tw1GuAHsQT2PFRYEfpcqCLqa\nXvKev0uIhMYVn4+3ea8w4w8D8UAKxY1ES1KQYVGtEyHfPElvVaSo3Af8h7og6cZ9\nFO8XDmkTKj1refhQnagwrErGL4O5Hv5L8zfE5z2cdVGnn018Hp5QofPW0k26zOQI\nPpbT8jzsI4jPrtsKYJIfWv3UymQ46pvRiGnQr745MsT4h6K6yf64C7wf1rY01WUX\n/7zMfvQgUPo+qzVWaY5InAlr7MlpvVv3J/Wi9K0+5azurQW7nCkxjp8FoOQkmObJ\n5ZGMWTRvT+562531NX06G8eYR00CAwEAAaMYMBYwFAYDVR0RBA0wC4IJbG9jYWxo\nb3N0MA0GCSqGSIb3DQEBCwUAA4IBAQASVG+pVth7UmxMKu/YgcE4TcyLllw+ICy2\n8pqPL+Wung/46Macn5quFi1/eDwgSJ/sGULg+nvapjrhw9p7SLQ87Kr+J68u9+vo\n7hUJH6qmuxSGBVVUnge+gQ+iv7sfQYaA80EPSWDk5KUSAxUxeQnXW2PAkXmFza5D\npFCBMxH3cjoOdpdh/oTs0dH6w38K5Rf1Lfoka8ztUTU9RnB4J9CVYAV413fO2qji\nngYwjAVbDODkB3D/zm4ODagMXjRylRC/sH7vA9bz40EFMzRVzfOblUDvIrx4f5Tq\nQaV4khxB42/TWjYYq0zXTxLklExUxb7RwpxT6Bq9sYeDO7di0y4/\n-----END CERTIFICATE-----\n'
KEY = '-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDGmME4bi2YG7RS\nQFink4ydb1x2bxlOfktnu7cNRrgB7EE9jxUWBH6XKgi6ml7ynr9LiITGFZ+Pt3mv\nMOMPA/FACsWNREtSkGFRrRMh3zxJb1WkqNwH/Ie6IOnGfRTvFw5pEyo9a3n4UJ2o\nMKxKxi+DuR7+S/M3xOc9nHVRp59NfB6eUKHz1tJNuszkCD6W0/I87COIz67bCmCS\nH1r91MpkOOqb0Yhp0K++OTLE+Ieiusn+uAu8H9a2NNVlF/+8zH70IFD6Pqs1VmmO\nSJwJa+zJab1b9yf1ovStPuWs7q0Fu5wpMY6fBaDkJJjmyeWRjFk0b0/uetud9TV9\nOhvHmEdNAgMBAAECggEBALbS8S2t4DNjbcE6k2LRpmVYm1o8NKPaCDjayk1iiQrc\nH8M38UVvpcorXBXM/xODqL80Uma4iUeYtGDfNGgiTPmT8QF3mY/McorqNe68v5cq\n80C+YrDHfXuPySZ9B8SDCTUZ+4zHYGWEcV7gT/wWLq+owCuCZ8kzb118p1QgZ7q/\nopG6Kvz7rECfFnrKaes38sWk1L30Ogm05BibmmOvbb7G7Y01xHCeuLEVCYPlzwEe\nUeX7MCKvLljKxMkaJgU5hJUtApTh0VtT8kIAKLs39ClWHLfacWEpU6Pu8ybd0W/A\ncuU+KbDCCrCDljngphbBveHVIdtI1f2VFoIXGmb/E4ECgYEA/m54QsNkHcSzLiEq\n7hoL+lQFQaBr9vCND2ByBpsv623EZY84MobdUsiIr1NLOFiyXPv9/zSh29mT7hew\nFcO7w5hjIcWJLtEG/eQyGuqyyW/cjptBcinezooos50wdNrDU4jUj08MZtQU1Xjr\nUaasJE+dGtLi/q8himecg35j46kCgYEAx9IrYezrTu9lLYLSkVEAH2671FWwnzq5\naPdtiIdU1p6m+nL7QuJGeR5MR0E0p7Rt8asb2pq9+tP3uruDPmo92tB84Cw4ijya\n/lWsEtnG59Z+x/DDYovaMXPZWiS3nZ/RujNte31XxHKc2KOPHIz3Xyhk0cO2v33t\nkX42Oo2zTQUCgYEA15jokzpa5da+NsKoTCcKK09zPM8hbZkdDwCc3vg1vPvAxoZ8\nCmS5uuJu4JJmVRLj4WMvMkh5N4DBl6m+7lJ0EyRYLE/lFSTPFel+g8yJP6Rocvcg\nmAre4Im2P61dWEff6DM0W1OSoLfqB5J1ZTUk/YfxCr/U1he1BkESIWLCZjECgYAF\n/cI5PG5NvpXNCIghvUkAqERPeIZEL/GROSH6nvwnNziQd9QazEgKp6Ln3AelI57M\nSTIbmtopZCOgYLDttSfHoMqtugWz9186Uv1Gz2rMVr0UZ56kHMddBjk1H7a1ri4O\npC4bLsXr6PfU8wp+c6eTHdXwCCs5kKAH5b3ggZEntQKBgC0y0hYPylljxFViveHt\nVDURlizjUi38UwHmRcpbFhh41StfKhko7OgC8QzSjH04P6zUD3vtId3oGJnxZA/s\n24Z9PSL4ZrxxTdPRFWokbxF3HMwUM+jKfdjKf9n2KZzg62MFIgOKxES4q31w8odw\npkF1hWH34/GY6RcMx8phuh1k\n-----END PRIVATE KEY-----\n'
with tempfile.TemporaryDirectory(prefix='sdpr-tls-') as directory:
    cert, key = Path(directory)/'cert.pem', Path(directory)/'key.pem'
    cert.write_text(CERT); key.write_text(KEY)
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert, key)
    listener = socket.socket(); listener.bind(('127.0.0.1', 0)); listener.listen(1)
    address = listener.getsockname()
    def serve():
        connection, _ = listener.accept()
        try:
            with server_context.wrap_socket(connection, server_side=True) as secured:
                secured.recv(1)
        except ssl.SSLError:
            pass  # Expected when client rejects the untrusted certificate.
        finally:
            connection.close(); listener.close()
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    try:
        with socket.create_connection(address, timeout=10) as connection:
            context.wrap_socket(connection, server_hostname='localhost')
    except ssl.SSLCertVerificationError:
        pass
    else:
        raise AssertionError('TLS accepted an untrusted certificate')
    thread.join(timeout=10)
    assert not thread.is_alive(), 'Local TLS server did not finish'
modules = {}
for name in ('_ssl', '_hashlib', '_tkinter', 'zlib', 'tkinterdnd2'):
    module = __import__(name); modules[name] = str(Path(module.__file__).resolve())
loaded = []
if sys.platform == 'darwin':
    native = ctypes.CDLL(None)
    native._dyld_image_count.restype = ctypes.c_uint32
    native._dyld_get_image_name.argtypes = [ctypes.c_uint32]
    native._dyld_get_image_name.restype = ctypes.c_char_p
    loaded = [native._dyld_get_image_name(i).decode() for i in range(native._dyld_image_count())]
else:
    from ctypes import wintypes
    handles = (wintypes.HMODULE * 2048)(); needed = wintypes.DWORD()
    native = ctypes.windll.kernel32
    native.GetCurrentProcess.restype = wintypes.HANDLE
    native.K32EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    native.K32GetModuleFileNameExW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    process = native.GetCurrentProcess()
    assert native.K32EnumProcessModules(process, handles, ctypes.sizeof(handles), ctypes.byref(needed))
    for handle in handles[:needed.value//ctypes.sizeof(wintypes.HMODULE)]:
        buffer = ctypes.create_unicode_buffer(32768)
        assert native.K32GetModuleFileNameExW(process, handle, buffer, len(buffer))
        loaded.append(buffer.value)
result = dict(python_version=platform.python_version(), architecture=platform.machine(), bits=ctypes.sizeof(ctypes.c_void_p)*8,
              tcl_version=root.tk.call('info', 'patchlevel'), tk_version=root.tk.call('package', 'provide', 'Tk'),
              tk_window_system=root.tk.call('tk', 'windowingsystem'), tkdnd_version=version, openssl_version=ssl.OPENSSL_VERSION,
              module_origins=modules, loaded_libraries=loaded, optional_modules=optional, ssl_default_verification=True, native_operations=True)
root.update(); root.destroy()
result['module_origins'] = {name: str(Path(module.__file__).resolve()) for name, module in tuple(sys.modules.items()) if getattr(module, '__file__', None) and not str(module.__file__).startswith('<')}
print('SDPR_RESULT=' + json.dumps(result))
"""


def embedded(artifact):
    resources = artifact / "Contents/Resources"
    bootstrap = (
        "SDPR_BUNDLED=True; import sys; sys.dont_write_bytecode=True; sys.path[:0] = "
        + repr(
            [
                str(resources / "lib/python311.zip"),
                str(resources / "lib/python3.11"),
                str(resources / "lib/python3.11/lib-dynload"),
                str(resources),
            ]
        )
        + ";\n"
    )
    env = clean_env()
    env["PYTHONHOME"] = str(resources)
    env["RESOURCEPATH"] = str(resources)
    env["TCL_LIBRARY"] = str(resources / "lib/tcl8.6")
    env["TK_LIBRARY"] = str(resources / "lib/tk8.6")
    return [artifact / "Contents/MacOS/python", "-B", "-S", "-c"], bootstrap, env


def result_json(result):
    if result["returncode"]:
        raise ValueError("Child failed: " + result["stderr"][-6000:])
    lines = [
        line[12:]
        for line in result["stdout"].splitlines()
        if line.startswith("SDPR_RESULT=")
    ]
    if len(lines) != 1:
        raise ValueError("Child produced no unique result receipt")
    return json.loads(lines[0])


def versions(facts, target):
    expected = TARGETS[target][1]
    assert facts["python_version"] == "3.11.18", "Requires Python 3.11.18"
    assert (
        facts["architecture"].lower() == expected.lower() and facts["bits"] == 64
    ), "Wrong native architecture"
    assert (
        facts["tcl_version"] == facts["tk_version"] == "8.6.18"
    ), "Requires actual Tcl/Tk 8.6.18"
    assert facts["openssl_version"].startswith(
        "OpenSSL 3.5.9 "
    ), "Requires actual OpenSSL 3.5.9"
    assert facts["tk_window_system"] == (
        "aqua" if target.startswith("macos") else "win32"
    ), "Wrong Tk window system"


def loaded_native(facts, target, artifact=None):
    records = []
    for library in facts["loaded_libraries"]:
        path = Path(library).resolve()
        if target.startswith("macos"):
            if library.startswith(("/usr/lib/", "/System/Library/")):
                continue  # May be supplied by the dyld shared cache.
            assert path.is_file(), "Loaded native library is missing: " + library
            assert not library.startswith(
                ("/opt/", "/usr/local/", "/Library/Frameworks/")
            ), ("Unexpected global native dependency: " + library)
            architecture = subprocess.check_output(
                ["/usr/bin/lipo", "-archs", str(path)], text=True
            ).strip()
            assert TARGETS[target][1] in architecture.split(), (
                "Loaded library has wrong CPU: " + library
            )
        else:
            system = Path(os.environ["SystemRoot"]).resolve()
            if path.is_relative_to(system):
                continue
            pe_imports(path)
            architecture = "AMD64"
        if artifact is not None:
            assert path.is_relative_to(artifact.resolve()), (
                "Bundle loaded an external library: " + library
            )
        records.append({"library": str(path), "architecture": architecture})
    assert records, "No non-system native modules were observed"
    return records


def macho_files(root):
    magic = (
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
    )
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            with path.open("rb") as stream:
                if stream.read(4) in magic:
                    yield path


def native_links(root, target):
    """Inspect every retained Mach-O, including dynamically loaded TkDND."""
    if target == "windows-x64":
        # One-file imports are inspected after actual GUI extraction below.
        for name in EXES:
            with (root / name).open("rb") as stream:
                assert stream.read(2) == b"MZ", "Invalid PE signature"
                stream.seek(0x3C)
                offset = struct.unpack("<I", stream.read(4))[0]
                stream.seek(offset)
                assert stream.read(4) == b"PE\0\0"
                assert (
                    struct.unpack("<H", stream.read(2))[0] == 0x8664
                ), "EXE is not AMD64"
        return {"pe_architecture": "AMD64", "closure": "checked-during-gui-extraction"}
    binaries = list(macho_files(root))
    assert binaries, "No Mach-O files found"
    failures = []
    records = []
    expected = TARGETS[target][1]
    executable = root / "Contents/MacOS"
    for path in binaries:
        arch = subprocess.check_output(
            ["/usr/bin/lipo", "-archs", str(path)], text=True
        ).strip()
        if expected not in arch.split():
            # TkDND ships optional binaries for both Macs. The runtime probe
            # separately requires the selected native library to load.
            relative = path.relative_to(root).as_posix()
            inactive = "/tkinterdnd2/tkdnd/osx-" in relative
            assert inactive, "Wrong Mach-O architecture: " + relative
            records.append(
                {"path": relative, "architecture": arch, "inactive_resource": True}
            )
            continue
        listing = subprocess.check_output(
            ["/usr/bin/otool", "-arch", expected, "-L", str(path)], text=True
        )
        commands = subprocess.check_output(
            ["/usr/bin/otool", "-arch", expected, "-l", str(path)], text=True
        ).splitlines()
        rpaths = [
            commands[i + 2].strip().split(" (offset")[0][5:]
            for i, line in enumerate(commands)
            if line.strip() == "cmd LC_RPATH"
        ]

        def expand(value):
            return value.replace("@loader_path", str(path.parent)).replace(
                "@executable_path", str(executable)
            )

        dependencies = []
        for line in listing.splitlines()[1:]:
            dep = line.strip().split(" (compatibility")[0]
            if not dep:
                continue
            if dep.startswith(("/usr/lib/", "/System/Library/")):
                continue
            if dep.startswith("@rpath/"):
                tail = dep[len("@rpath/") :]
                candidates = [Path(expand(r)) / tail for r in rpaths] + [
                    root / "Contents/Frameworks" / tail
                ]
            else:
                candidates = [Path(expand(dep))]
            matches = [
                p
                for p in candidates
                if p.exists() and p.resolve().is_relative_to(root.resolve())
            ]
            if not matches:
                failures.append(
                    {"binary": str(path.relative_to(root)), "dependency": dep}
                )
            dependencies.append(dep)
        records.append(
            {
                "path": str(path.relative_to(root)),
                "architecture": arch,
                "dependencies": dependencies,
            }
        )
    assert not failures, "Unresolved/external native links: " + json.dumps(failures)
    return {"closure": "passed", "binaries": records}


def png(path, metadata):
    """Generate a tiny RGBA PNG with independently specified metadata."""

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    data = b"\x89PNG\r\n\x1a\n" + chunk(
        b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 6, 0, 0, 0)
    )
    for key, value in metadata.items():
        data += chunk(b"tEXt", key.encode() + b"\0" + value.encode())
    data += chunk(
        b"IDAT", zlib.compress(b"\0\x10\x20\x30\x80\x40\x50\x60\xff")
    ) + chunk(b"IEND", b"")
    path.write_bytes(data)


def cli_checks(command, folder, env):
    raw = "a copper kite over water\nNegative prompt: haze\nSteps: 7, Sampler: Euler, CFG scale: 4, Seed: 19, Size: 2x1, Model: synthetic"
    source = folder / "synthetic {sample} unicode-\u732b.png"
    png(source, {"parameters": raw})
    partial = folder / "partial.png"
    png(partial, {"workflow": '{"ci_synthetic":true}'})
    cases = []

    def check(name, args, success=True, contains=None):
        value = run([*command, *args], folder, env)
        cases.append({"name": name, **value})
        assert value["returncode"] >= 0, (
            name + " timed out or was terminated: " + json.dumps(value)
        )
        assert (value["returncode"] == 0) == success, name + ": " + json.dumps(value)
        if contains is not None:
            assert contains in value["stdout"], name + " output mismatch"
        return value

    check("help", ["--help"], contains="--input-path")
    check("read", ["-i", source], contains=raw)
    exported = folder / "export.json"
    check("json-export", ["-i", source, "-o", exported, "-f", "JSON"])
    data = json.loads(exported.read_text())
    assert (
        data["positive"] == "a copper kite over water"
        and data["negative"] == "haze"
        and str(data["seed"]) == "19"
    )
    text = folder / "export.txt"
    check("text-export", ["-i", source, "-o", text])
    assert text.read_text() == raw
    edited = folder / "edited.png"
    check(
        "write",
        [
            "-w",
            "-i",
            source,
            "-o",
            edited,
            "-p",
            "a silver balloon",
            "-n",
            "rain",
            "-s",
            "Steps: 3, Seed: 23, Size: 2x1",
        ],
    )
    check(
        "read-written",
        ["-i", edited],
        contains="a silver balloon\nNegative prompt: rain\nSteps: 3, Seed: 23, Size: 2x1",
    )
    cleared = folder / "cleared.png"
    check("clear", ["-c", "-i", source, "-o", cleared])
    check("read-cleared", ["-i", cleared], success=False)
    check("partial-read", ["-i", partial], success=False)
    check("raw-recovery", ["-i", partial, "--raw"], contains='{"ci_synthetic":true}')
    check("missing-input", ["-i", folder / "absent.png"], success=False)
    check("bad-raw-mode", ["-c", "--raw", "-i", source], success=False)
    blocker = folder / "blocker"
    blocker.write_text("not a directory")
    check("export-failure", ["-i", source, "-o", blocker / "out.txt"], success=False)
    check(
        "write-failure",
        ["-w", "-i", source, "-o", blocker / "out.png", "-p", "failure"],
        success=False,
    )
    return cases, source, edited, cleared


GUI_PROBE = r"""
import json, sys, traceback
from pathlib import Path
from PIL import Image
import PIL
from sd_prompt_reader.app import App
source, edited, cleared = map(Path, sys.argv[1:4])
# Metadata edits must retain the independently specified pixel/alpha values.
for path in (source, edited, cleared):
    with Image.open(path) as image:
        assert image.mode == 'RGBA' and image.size == (2, 1)
        assert list(image.getdata()) == [(16,32,48,128),(64,80,96,255)]
with Image.open(cleared) as image:
    assert not image.info, 'Clear retained ordinary metadata'
app = App()
errors = []
app.report_callback_exception = lambda *error: errors.append(''.join(traceback.format_exception(*error)))
app.display_info(str(source), is_selected=True)
app.update()
assert app.readable and app.image_data.positive == 'a copper kite over water'
assert app.tk.call('package', 'provide', 'tkdnd')
assert app.winfo_viewable(), 'App never became viewable'
# Invoke Tk's registered normal WM close callback through the Tcl interpreter.
handler = app.protocol('WM_DELETE_WINDOW')
assert handler, 'No WM_DELETE_WINDOW handler'
app.after(200, lambda: app.tk.eval(handler))
app.mainloop()
assert not errors, errors
import PIL, tkinterdnd2, sd_prompt_reader.app, customtkinter
origins = {name: str(Path(module.__file__).resolve()) for name, module in tuple(sys.modules.items()) if getattr(module, '__file__', None) and not str(module.__file__).startswith('<')}
print('SDPR_RESULT=' + json.dumps(dict(viewable=True, image_loaded=True, normal_wm_close=True, pixels_preserved=True, module_origins=origins, pillow_version=PIL.__version__, pillow_native_versions={name: getattr(Image.core,name) for name in dir(Image.core) if name.endswith('_version') and isinstance(getattr(Image.core,name), str)})))
"""


def pe_imports(path):
    """Read ordinary and delay PE imports without an extra bootstrap package."""
    data = path.read_bytes()
    assert data[:2] == b"MZ", "Not a PE file: " + path.name
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[offset : offset + 4] == b"PE\0\0"
    machine, count = struct.unpack_from("<HH", data, offset + 4)
    assert machine == 0x8664, "Non-AMD64 native file: " + path.name
    size = struct.unpack_from("<H", data, offset + 20)[0]
    optional = offset + 24
    assert struct.unpack_from("<H", data, optional)[0] == 0x20B, "Expected PE32+"
    sections = []
    for n in range(count):
        section = optional + size + n * 40
        virtual_size, virtual_address, raw_size, raw = struct.unpack_from(
            "<IIII", data, section + 8
        )
        sections.append((virtual_address, max(virtual_size, raw_size), raw))

    def file_offset(rva):
        for base, length, raw in sections:
            if base <= rva < base + length:
                return raw + rva - base
        raise ValueError("Unmapped PE RVA")

    def string(rva):
        start = file_offset(rva)
        return data[start : data.index(b"\0", start)].decode("ascii")

    imports = []
    directory = optional + 112
    rva, _ = struct.unpack_from("<II", data, directory + 8)
    if rva:
        position = file_offset(rva)
        while any(data[position : position + 20]):
            imports.append(string(struct.unpack_from("<I", data, position + 12)[0]))
            position += 20
    delayed, _ = struct.unpack_from("<II", data, directory + 13 * 8)
    if delayed:
        position = file_offset(delayed)
        while any(data[position : position + 32]):
            attributes, name = struct.unpack_from("<II", data, position)
            assert attributes & 1, "Unsupported absolute delay-import descriptor"
            imports.append(string(name))
            position += 32
    return imports


def windows_closure(extraction):
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    assert ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
    system = Path(buffer.value)
    natives = [
        p
        for p in extraction.rglob("*")
        if p.suffix.lower() in (".dll", ".pyd", ".exe")
        and not any(part in ("win-x86", "win-arm64") for part in p.parts)
    ]
    assert natives, "One-file EXE produced no inspectable native payload"
    available = {p.name.lower() for p in natives}
    records = []
    for path in natives:
        imports = pe_imports(path)
        missing = [
            name
            for name in imports
            if name.lower() not in available
            and not name.lower().startswith(("api-ms-win-", "ext-ms-win-"))
            and not (system / name).is_file()
        ]
        assert not missing, (
            "Unresolved native dependencies in " + path.name + ": " + ", ".join(missing)
        )
        records.append(
            {
                "path": path.relative_to(extraction).as_posix(),
                "imports": imports,
                "architecture": "AMD64",
            }
        )
    return {
        "closure": "passed",
        "binaries": records,
        "system_resolution": "Native Windows system directory and API sets",
    }


def png_contents(path):
    """Compare filtered RGBA pixels using PNG filters, independent of Pillow."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    cursor, packed, metadata = 8, b"", []
    width = height = None
    while cursor < len(data):
        size = struct.unpack_from(">I", data, cursor)[0]
        kind, block = (
            data[cursor + 4 : cursor + 8],
            data[cursor + 8 : cursor + 8 + size],
        )
        assert (zlib.crc32(kind + block) & 0xFFFFFFFF) == struct.unpack_from(
            ">I", data, cursor + 8 + size
        )[0]
        if kind == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(
                ">IIBBBBB", block
            )
            assert (width, height, depth, color, interlace) == (2, 1, 8, 6, 0)
        if kind == b"IDAT":
            packed += block
        if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            metadata.append(kind.decode())
        cursor += size + 12
    rows = zlib.decompress(packed)
    stride = 2 * 4
    assert len(rows) == stride + 1
    previous = bytearray(stride)
    for row in range(1):
        start = row * (stride + 1)
        mode, pixels = rows[start], bytearray(rows[start + 1 : start + 1 + stride])
        assert mode in range(5)
        for index in range(stride):
            left = pixels[index - 4] if index >= 4 else 0
            above = previous[index]
            corner = previous[index - 4] if index >= 4 else 0
            if mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            elif mode == 4:
                value = left + above - corner
                distances = (abs(value - left), abs(value - above), abs(value - corner))
                predictor = (left, above, corner)[distances.index(min(distances))]
            else:
                predictor = 0
            pixels[index] = (pixels[index] + predictor) & 255
        assert (
            bytes(pixels) == b"\x10\x20\x30\x80\x40\x50\x60\xff"
        ), "Pixel or alpha changed"
        previous = pixels
    return metadata


def windows_gui(executable, folder, env):
    """Use only windows owned by this invocation's PID (including one-file child)."""
    import ctypes
    from ctypes import wintypes

    kernel, user = ctypes.windll.kernel32, ctypes.windll.user32
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("size", wintypes.DWORD),
            ("usage", wintypes.DWORD),
            ("pid", wintypes.DWORD),
            ("heap", ctypes.c_size_t),
            ("module", wintypes.DWORD),
            ("threads", wintypes.DWORD),
            ("parent", wintypes.DWORD),
            ("priority", wintypes.LONG),
            ("flags", wintypes.DWORD),
            ("exe", wintypes.WCHAR * 260),
        ]

    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback, wintypes.LPARAM]
    user.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.PostMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    extraction = folder / "onefile-temp"
    extraction.mkdir()
    env = dict(env, TEMP=str(extraction), TMP=str(extraction))
    process = subprocess.Popen(
        [str(executable)],
        cwd=folder,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    windows = []
    owned = {process.pid}
    try:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline and process.poll() is None:
            snap = kernel.CreateToolhelp32Snapshot(2, 0)
            entry = ProcessEntry()
            entry.size = ctypes.sizeof(entry)
            pairs = []
            ok = kernel.Process32FirstW(snap, ctypes.byref(entry))
            while ok:
                pairs.append((entry.pid, entry.parent))
                ok = kernel.Process32NextW(snap, ctypes.byref(entry))
            kernel.CloseHandle(snap)
            for _ in range(len(pairs)):
                owned.update(pid for pid, parent in pairs if parent in owned)

            def visit(hwnd, _):
                pid = wintypes.DWORD()
                user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in owned and user.IsWindowVisible(hwnd):
                    title, kind = ctypes.create_unicode_buffer(
                        1024
                    ), ctypes.create_unicode_buffer(256)
                    user.GetWindowTextW(hwnd, title, len(title))
                    user.GetClassNameW(hwnd, kind, len(kind))
                    if title.value == "SD Prompt Reader" and kind.value.startswith(
                        "Tk"
                    ):
                        windows.append(hwnd)
                return True

            user.EnumWindows(callback(visit), 0)
            if windows:
                break
            time.sleep(0.2)
        assert windows, "GUI EXE produced no PID-owned visible window"
        closure = windows_closure(extraction)
        for hwnd in windows:
            user.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, "GUI EXE close failed: " + stderr
        return {
            "visible_window": True,
            "wm_close": True,
            "stdout": stdout,
            "stderr": stderr,
            "native_closure": closure,
        }
    finally:
        if process.poll() is None:
            for hwnd in windows:
                user.PostMessageW(hwnd, 0x0010, 0, 0)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                kernel.OpenProcess.argtypes = [
                    wintypes.DWORD,
                    wintypes.BOOL,
                    wintypes.DWORD,
                ]
                kernel.OpenProcess.restype = wintypes.HANDLE
                kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
                for pid in owned:
                    handle = kernel.OpenProcess(1, False, pid)
                    if handle:
                        kernel.TerminateProcess(handle, 1)
                        kernel.CloseHandle(handle)
                process.communicate(timeout=5)


def verify_artifact(args, report, gate, folder):
    artifact = args.artifact.resolve()
    assert artifact.is_dir(), "Artifact directory missing"
    assert (
        not args.target.startswith("macos") or artifact.suffix == ".app"
    ), "Expected .app directory"
    report["artifact"] = gate(
        "artifact-identity",
        lambda: artifact_identity(artifact, args.target),
    )
    report["metadata"] = gate(
        "artifact-metadata",
        lambda: artifact_metadata(artifact, args.target, args.expected_version),
    )
    report["native"] = gate(
        "native-architecture-links",
        lambda: native_links(artifact, args.target),
    )
    if args.target.startswith("macos"):
        command = [artifact / "Contents/MacOS/SD Prompt Reader"]
        probe, bootstrap, env = embedded(artifact)
        facts = gate(
            "bundled-runtime",
            lambda: result_json(run([*probe, bootstrap + RUNTIME_PROBE], folder, env)),
        )
        gate("bundled-versions", lambda: versions(facts, args.target))
        gate(
            "bundled-loaded-native",
            lambda: loaded_native(facts, args.target, artifact),
        )
        assert all(
            Path(p).resolve().is_relative_to(artifact.resolve())
            for p in facts["module_origins"].values()
        ), "Bundled runtime imported external module"
        report["runtime"] = facts
    else:
        command, env = [artifact / EXES[1]], clean_env()
    cases, source, edited, cleared = gate(
        "packaged-cli", lambda: cli_checks(command, folder, clean_env())
    )
    report["cli_cases"] = cases
    if args.target.startswith("macos"):
        gui = gate(
            "bundled-gui-widgets-close",
            lambda: result_json(
                run(
                    [
                        *probe,
                        bootstrap + GUI_PROBE,
                        source,
                        edited,
                        cleared,
                    ],
                    folder,
                    env,
                )
            ),
        )
        assert all(
            Path(p).resolve().is_relative_to(artifact.resolve())
            for p in gui["module_origins"].values()
        ), "GUI imported source fallback"
        report["limitations"].append(
            "GUI widgets/normal Tk close were exercised in the embedded interpreter; CLI used actual app launcher. Physical native GUI interactions remain manual."
        )
        report["gui"] = gui
    else:
        report["gui"] = gate(
            "gui-exe-visible-wm-close",
            lambda: windows_gui(artifact / EXES[0], folder, env),
        )
        for image in (source, edited, cleared):
            metadata = png_contents(image)
            if image == cleared:
                assert not metadata, "Clear retained ordinary metadata"
        report["limitations"].append(
            "Windows checks actual GUI/CLI EXEs and extracted DLL imports; source-module widget probes were not substituted for EXE behavior."
        )
    gate(
        "artifact-unchanged",
        lambda: unchanged_artifact(artifact, args.target, report["artifact"]),
    )


def main():
    args = parser().parse_args()
    if not __debug__:
        parser().error("Verification must run with Python assertions enabled")
    output = args.output.resolve()
    selected = args.python if args.kind == "runtime" else args.artifact
    if not selected.is_absolute() or not args.output.is_absolute():
        parser().error("Input and output paths must be absolute")
    if args.kind == "artifact" and output.is_relative_to(args.artifact.resolve()):
        parser().error("Report must be outside artifact")
    if output.exists():
        parser().error("--output must be a new file")
    if not output.parent.is_dir():
        parser().error("--output parent must already exist")
    report = {
        "schema_version": 1,
        "kind": args.kind,
        "target": args.target,
        "status": "failed",
        "checks": [],
        "processes": PROCESS_LOG,
        "limitations": [
            "Physical picker, drag/drop, clipboard, file-manager association, security/quarantine and oldest OS require manual checks."
        ],
    }

    def gate(name, operation):
        try:
            details = operation()
            report["checks"].append(
                {
                    "name": name,
                    "status": "passed",
                    "details": json.loads(json.dumps(details, default=str)),
                }
            )
            return details
        except Exception as error:
            report["checks"].append(
                {"name": name, "status": "failed", "details": str(error)}
            )
            raise

    try:

        def preflight():
            assert platform.system() == TARGETS[args.target][0], "Wrong native OS"
            assert (
                platform.machine().lower() == TARGETS[args.target][1].lower()
            ), "Wrong native CPU"
            return {"os": platform.platform(), "architecture": platform.machine()}

        gate("native-host", preflight)
        with tempfile.TemporaryDirectory(prefix="sdpr-verify-") as name:
            folder = Path(name)
            if args.kind == "runtime":
                python = args.python.absolute()
                assert python.is_file(), "Interpreter missing"
                result = run([python, "-I", "-c", RUNTIME_PROBE], folder, clean_env())
                report["runtime_process"] = result
                facts = gate("runtime-operations", lambda: result_json(result))
                gate("runtime-versions", lambda: versions(facts, args.target))
                gate(
                    "loaded-native-architecture",
                    lambda: loaded_native(facts, args.target),
                )
                required_optional = (
                    ("bz2", "sqlite3") if args.target.startswith("macos") else ()
                )
                assert all(
                    facts["optional_modules"][name] == "operation-passed"
                    for name in required_optional
                ), "Required native optional-module operation missing"
                report["runtime"] = facts
                if args.runtime_receipt:
                    receipt = json.loads(args.runtime_receipt.read_text())
                    assert (
                        receipt["target"] == args.target
                    ), "Native receipt target mismatch"
                    report["native_input_receipt"] = receipt
                report["limitations"].append(
                    "Local TLS rejects an untrusted certificate with SSLCertVerificationError; no remote HTTPS service was contacted."
                )
            else:
                verify_artifact(args, report, gate, folder)
        report["status"] = "passed"
    except Exception as error:
        report["error"] = str(error)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "passed":
        print(
            "Verification failed: " + report.get("error", "Unknown failure"),
            file=sys.stderr,
        )
    print(json.dumps({"status": report["status"], "report": str(output)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
