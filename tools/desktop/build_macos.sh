#!/bin/bash
# Build a private native CPython framework and its pinned Tcl/Tk/OpenSSL inputs.
set -euo pipefail
usage() {
    echo 'Usage: bash tools/desktop/build_macos.sh --root ABS --target macos-x86_64|macos-arm64 --receipt ABS'
    echo 'Requires a new root, an existing receipt parent outside it, Xcode and a native macOS host.'
}
fail() { echo "build_macos: $*" >&2; exit 1; }
root= target= receipt=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --root|--target|--receipt)
            [ "$#" -ge 2 ] || fail "missing value for $1"
            case "$1" in --root) root=$2;; --target) target=$2;; --receipt) receipt=$2;; esac
            shift 2 ;;
        *) fail "unknown argument: $1" ;;
    esac
done
[ -n "$root" ] && [ -n "$target" ] && [ -n "$receipt" ] || { usage >&2; exit 1; }
case "$target" in
    macos-x86_64) arch=x86_64; minimum=10.15; openssl_target=darwin64-x86_64-cc ;;
    macos-arm64) arch=arm64; minimum=13.0; openssl_target=darwin64-arm64-cc ;;
    *) fail "unsupported target: $target" ;;
esac
[ "$(uname -s)" = Darwin ] || fail 'requires native macOS'
[ "$(uname -m)" = "$arch" ] || fail "native CPU must be $arch (no cross-compilation or Rosetta)"
# sysctl catches a translated Intel shell on Apple Silicon even if uname says x86_64.
[ "$(/usr/sbin/sysctl -in sysctl.proc_translated 2>/dev/null || true)" != 1 ] || fail 'Rosetta is not a native build'
case "$root:$receipt" in /*:/*) ;; *) fail 'root and receipt must be absolute paths' ;; esac
# Resolve parent symlinks before comparing ownership boundaries. Parent creation is
# deliberately the caller's responsibility; a failed preflight makes no files.
[ -d "$(dirname "$root")" ] && [ -d "$(dirname "$receipt")" ] || fail 'output parents must exist'
root="$(cd "$(dirname "$root")" && pwd -P)/$(basename "$root")"
receipt="$(cd "$(dirname "$receipt")" && pwd -P)/$(basename "$receipt")"
case "$root$receipt" in *[[:space:]]*) fail 'build paths must not contain whitespace' ;; esac
case "$root" in */.|*/..|/|/private|/private/tmp|/tmp|/Users|/Volumes|/usr|/usr/*|/opt|/opt/*|/System|/System/*|/Library|/Library/*|/Applications|/Applications/*|/bin|/sbin|/etc|/var) fail 'root is a global prefix' ;; esac
case "$root" in
    /private/*)
        case "$root" in
            /private/tmp/*|/private/var/folders/*) ;;
            *) fail 'root is a global prefix' ;;
        esac ;;
    /dev/*|/bin/*|/sbin/*|/cores/*|/Network/*) fail 'root is a global prefix' ;;
esac
source_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
case "$source_root/" in "$root/"*) fail 'root must not contain the source tree' ;; esac
case "$root/" in "$source_root/"*) fail 'root must be outside the source tree' ;; esac
case "$receipt/" in "$source_root/"*) fail 'receipt must be outside source' ;; esac
case "$receipt/" in "$root/"*) fail 'receipt must be outside root' ;; esac
[ ! -e "$root" ] && [ ! -L "$root" ] || fail 'requires a new root; existing trees are never reused'
[ ! -e "$receipt" ] && [ ! -L "$receipt" ] || fail 'receipt already exists'
/usr/bin/xcode-select -p >/dev/null || fail 'Xcode command-line tools required'
sdk=$(/usr/bin/xcrun --show-sdk-path)
[ -d "$sdk/usr/include" ] || fail 'macOS SDK headers not found'
[ -r /etc/ssl/cert.pem ] || fail 'system TLS certificate bundle not found'
umask 022
mkdir "$root"
mkdir "$root/downloads" "$root/src" "$root/build" "$root/native" "$root/logs"
# Immutable official source identities, reviewed in the native toolchain plan.
python_url=https://www.python.org/ftp/python/3.11.18/Python-3.11.18.tar.xz
python_sha=9120e0a653868f6e3698d36cdd99e5a58903ec9469e448f21d98f7b16d8fa290
tcl_commit=515167c897a7c8066abfbd71e8fe7bd8bf3569de
tcl_url=https://codeload.github.com/tcltk/tcl/tar.gz/$tcl_commit
tcl_sha=a505b3e801896e2273be4d922ef46179ee3c4f8d77823d9a53a64bddd1965978
tk_commit=6dbe68819aac4a22f6f7a143133ce26c5e8d2b05
tk_url=https://codeload.github.com/tcltk/tk/tar.gz/$tk_commit
tk_sha=f968d5c3b3e16ede93d4cd8fbb0ba552f2ba8cdc4a2942d68528f8036ec127c6
openssl_url=https://github.com/openssl/openssl/releases/download/openssl-3.5.9/openssl-3.5.9.tar.gz
openssl_sha=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a
fetch() {
    local name=$1 url=$2 expected=$3 archive="$root/downloads/$1"
    echo "Fetching $name"
    curl --fail --location --retry 2 --proto '=https' --tlsv1.2 --output "$archive.part" "$url"
    local actual
    actual=$(/usr/bin/shasum -a 256 "$archive.part")
    [ "${actual%% *}" = "$expected" ] || fail "SHA256 mismatch for $name"
    mv "$archive.part" "$archive"
}
fetch Python-3.11.18.tar.xz "$python_url" "$python_sha"
fetch tcl.tar.gz "$tcl_url" "$tcl_sha"
fetch tk.tar.gz "$tk_url" "$tk_sha"
fetch openssl-3.5.9.tar.gz "$openssl_url" "$openssl_sha"
# From here all compilation uses Apple tools and an explicit SDK, without
# inherited Python, Tcl, compiler, pkg-config, Homebrew or DYLD discovery.
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
build_env() {
    env -i PATH="$PATH" HOME="${HOME:-/}" LANG=C \
        CC=/usr/bin/clang MACOSX_DEPLOYMENT_TARGET="$minimum" SDKROOT="$sdk" \
        CFLAGS="-O2 -arch $arch -mmacosx-version-min=$minimum -isysroot $sdk -I$sdk/usr/include" \
        CPPFLAGS="-I$sdk/usr/include -I$sdk/usr/include/ffi" \
        LDFLAGS="-arch $arch -mmacosx-version-min=$minimum -isysroot $sdk -L$sdk/usr/lib" \
        "$@"
}
run_logged() {
    local name=$1
    shift
    echo "Building $name (log: $root/logs/$name.log)"
    "$@" >"$root/logs/$name.log" 2>&1 || {
        tail -40 "$root/logs/$name.log" >&2
        fail "$name failed"
    }
}
for archive in "$root/downloads/"*; do tar -xf "$archive" -C "$root/src"; done
tcltk="$root/native/tcltk"
openssl="$root/native/openssl"
mkdir "$root/build/tcl" "$root/build/tk"
cd "$root/build/tcl"
run_logged tcl-configure build_env "$root/src/tcl-$tcl_commit/unix/configure" \
    --prefix="$tcltk" --enable-threads --enable-shared --enable-64bit
run_logged tcl-build build_env make -j4
run_logged tcl-install-plan build_env make -n install
run_logged tcl-install build_env make install
cd "$root/build/tk"
run_logged tk-configure build_env "$root/src/tk-$tk_commit/unix/configure" \
    --prefix="$tcltk" --with-tcl="$tcltk/lib" --enable-threads --enable-shared --enable-64bit --enable-aqua
run_logged tk-build build_env make -j4
run_logged tk-install-plan build_env make -n install
run_logged tk-install build_env make install
cd "$root/src/openssl-3.5.9"
run_logged openssl-configure build_env /usr/bin/perl ./Configure "$openssl_target" \
    no-shared no-tests --prefix="$openssl" --openssldir="$openssl/ssl" "-mmacosx-version-min=$minimum"
run_logged openssl-build build_env make -j4
run_logged openssl-install-plan build_env make -n install_sw
run_logged openssl-install build_env make install_sw
mkdir -p "$openssl/ssl"
cp /etc/ssl/cert.pem "$openssl/ssl/cert.pem"
cd "$root/src/Python-3.11.18"
# Deliberately omit unused optional modules rather than discover third-party libs.
cat > Modules/Setup.local <<'EOF'
*disabled*
_lzma
_gdbm
_dbm
EOF
run_logged python-configure build_env env \
    TCLTK_CFLAGS="-I$tcltk/include" TCLTK_LIBS="-L$tcltk/lib -ltk8.6 -ltcl8.6" \
    LIBSQLITE3_CFLAGS="-I$sdk/usr/include" LIBSQLITE3_LIBS="$sdk/usr/lib/libsqlite3.tbd" \
    BZIP2_CFLAGS="-I$sdk/usr/include" BZIP2_LIBS="$sdk/usr/lib/libbz2.tbd" \
    ZLIB_CFLAGS="-I$sdk/usr/include" ZLIB_LIBS="$sdk/usr/lib/libz.tbd" \
    LIBFFI_INCLUDEDIR="$sdk/usr/include/ffi" \
    ./configure --enable-framework="$root/python/runtime/Library/Frameworks" \
    --with-openssl="$openssl" --with-openssl-rpath=no --with-pkg-config=no \
    --with-readline=editline --with-system-ffi --with-ensurepip=no
run_logged python-build build_env make -j4
run_logged python-install-plan build_env make -n install
run_logged python-install build_env make install
python="$root/python/runtime/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
# Receipt comes from the produced interpreter, after actual runtime operations and
# Mach-O closure checks. A GUI-session failure is a failed build, never a Tk pass.
echo 'Checking installed runtime, TkAqua and native dependency closure'
env -i PATH="$PATH" HOME="${HOME:-/}" LANG=C PYTHONDONTWRITEBYTECODE=1 \
    "$python" - "$root" "$target" "$arch" "$receipt" "$minimum" \
    "$python_url" "$python_sha" "$tcl_url" "$tcl_sha" "$tk_url" "$tk_sha" \
    "$openssl_url" "$openssl_sha" <<'PY' >"$root/logs/runtime-validation.log" 2>&1
import bz2
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sqlite3
import ssl
import struct
import subprocess
import sys
import tkinter
import urllib.request
import zlib

root, target, arch, receipt, minimum, *sources = sys.argv[1:]
root = Path(root).resolve()
assert platform.python_version() == '3.11.18', sys.version
assert platform.machine() == arch and struct.calcsize('P') == 8, platform.machine()
assert ssl.OPENSSL_VERSION.startswith('OpenSSL 3.5.9 '), ssl.OPENSSL_VERSION
assert hashlib.sha256(b'abc').hexdigest() == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
assert bz2.decompress(bz2.compress(b'native build')) == b'native build'
assert zlib.decompress(zlib.compress(b'native build')) == b'native build'
assert sqlite3.connect(':memory:').execute('select 6 * 7').fetchone() == (42,)
assert ctypes.CDLL(None).abs(-37) == 37
import readline
assert 'libedit' in readline.__doc__
for name in ('_lzma', '_gdbm', '_dbm', 'pip', 'setuptools'):
    assert importlib.util.find_spec(name) is None, name
with urllib.request.urlopen('https://pypi.org/pypi/pip/json', timeout=45) as response:
    assert response.status == 200, response.status
window = tkinter.Tk()
try:
    window.withdraw()
    window.update()
    tcl_version = str(window.tk.call('info', 'patchlevel'))
    tk_version = str(window.tk.call('package', 'present', 'Tk'))
    window_system = str(window.tk.call('tk', 'windowingsystem'))
    assert tcl_version == tk_version == '8.6.18', (tcl_version, tk_version)
    assert window_system == 'aqua', window_system
    for variable in ('tcl_library', 'tk_library'):
        assert Path(str(window.tk.getvar(variable))).resolve().is_relative_to(root)
finally:
    window.destroy()

# Inspect installed native inputs only, keeping downloaded/build-tree objects out
# of the runtime closure. Symlink aliases share the same already-checked object.
magic = {b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe'}
audit = []
seen = set()
for prefix in (root / 'python/runtime', root / 'native'):
    for path in sorted(prefix.rglob('*')):
        if not path.is_file() or path.resolve() in seen:
            continue
        seen.add(path.resolve())
        with path.open('rb') as stream:
            if stream.read(4) not in magic:
                continue
        architectures = subprocess.check_output(['/usr/bin/lipo', '-archs', str(path)], text=True).split()
        assert architectures == [arch], (path, architectures)
        links = subprocess.check_output(['/usr/bin/otool', '-L', str(path)], text=True)
        dependencies = []
        for line in links.splitlines()[1:]:
            linked = line.strip().split(' (', 1)[0]
            dependencies.append(linked)
            if linked.startswith(('/usr/lib/', '/System/Library/')):
                continue
            if linked.startswith('@loader_path/'):
                resolved = (path.parent / linked.removeprefix('@loader_path/')).resolve()
            else:
                resolved = Path(linked).resolve()
                assert linked.startswith('/'), (path, linked)
            assert resolved.is_relative_to(root) and resolved.exists(), (path, linked)
        audit.append({'path': str(path.relative_to(root)), 'architectures': architectures,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'dependencies': dependencies})
assert len(audit) > 70, len(audit)
(root / 'logs/native-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
inputs = {}
for index, name in enumerate(('cpython', 'tcl', 'tk', 'openssl')):
    inputs[name] = {'url': sources[index * 2], 'sha256': sources[index * 2 + 1]}
inputs['cpython']['version'] = '3.11.18'
inputs['tcl']['version'] = inputs['tk']['version'] = '8.6.18'
inputs['openssl']['version'] = '3.5.9'
result = {
    'schema_version': 1, 'target': target, 'python': str(Path(sys.executable).resolve()),
    'python_version': platform.python_version(), 'architecture': arch,
    'tcl_version': tcl_version, 'tk_version': tk_version,
    'openssl_version': ssl.OPENSSL_VERSION, 'inputs': inputs,
    'native_review': {
        'status': 'approved',
        'notes': [
            'Development candidate scope: reviewed immutable CPython, Tcl, Tk and OpenSSL source identities.',
            'Actual installed versions, native architecture and installed Mach-O dependency closure passed.',
            'Apple SDK/system runtime libraries are not bundled vendor inputs; no OS-wide security certification.',
            'Upstream full test suites, oldest OS operation and physical application GUI interaction are untested.',
        ],
    },
    'host': {'macos': platform.mac_ver()[0], 'xcode': subprocess.check_output(['/usr/bin/xcodebuild', '-version'], text=True).strip(),
             'sdk': subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-version'], text=True).strip()},
    'deployment_target': minimum, 'window_system': window_system,
    'omitted_optional_modules': ['_lzma', '_gdbm', '_dbm'],
    'ensurepip': False, 'native_objects_checked': len(audit),
    'system_runtime': {'sqlite': sqlite3.sqlite_version, 'zlib': zlib.ZLIB_RUNTIME_VERSION},
    'validation': {'tk_initialization': 'passed', 'certificate_verified_https': 'passed',
                   'native_closure': 'passed', 'full_upstream_test_suites': 'not_run'},
}
with Path(receipt).open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result, indent=2))
PY
echo "Runtime ready: $python"
echo "Receipt: $receipt"
