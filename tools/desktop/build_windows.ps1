# Private native Windows toolchain. No installer, global package change or release.
[CmdletBinding()]
param(
    [string]$Root,
    [string]$Target = 'windows-x64',
    [string]$Receipt,
    [switch]$Help,
    [string]$CheckInputs
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($Help) {
    Write-Output @'
Build a private CPython 3.11.18 / Tcl-Tk 8.6.18 Windows x64 runtime.
  pwsh -File build_windows.ps1 -Root ABS -Target windows-x64 -Receipt ABS
  pwsh -File build_windows.ps1 -CheckInputs ABS_ARCHIVE_DIRECTORY
Root must be new or empty, outside the repository and global prefixes.
Receipt parent must already exist outside Root and the source repository. Requires native Windows AMD64,
PowerShell 7+, existing VS2022 x64 tools/SDK 10.0.22621.0 and bootstrap python.exe.
CheckInputs only reads pinned archives; it never downloads, extracts or compiles.
Native security review is recorded separately and can block candidate packaging.
'@
    exit 0
}
function Absolute-Path([string]$Value) {
    if (-not $Value -or -not [IO.Path]::IsPathFullyQualified($Value)) { throw 'An absolute path is required.' }
    $full = [IO.Path]::GetFullPath($Value).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ($full -match '[%&!^<>|"\r\n]') { throw 'Unsupported shell metacharacter in path.' }
    # Refuse symlink/junction ancestors before writes or external tools.
    $probe = $full
    while ($probe) {
        if (Test-Path -LiteralPath $probe) {
            if ((Get-Item -Force -LiteralPath $probe).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse-point path is not allowed: $probe" }
        }
        $parent = [IO.Path]::GetDirectoryName($probe)
        if ($parent -eq $probe) { break }; $probe = $parent
    }
    return $full
}
function Within([string]$Child, [string]$Parent) {
    return $Child.Equals($Parent, [StringComparison]::OrdinalIgnoreCase) -or $Child.StartsWith($Parent + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}
function Check-Archive([string]$Path, $InputRecord) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing pinned archive: $Path" }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $InputRecord.sha256) { throw "SHA256 mismatch for $($InputRecord.name): expected $($InputRecord.sha256), got $actual" }
}
function Write-ArchiveIdentity([string]$SourceDir, $InputRecord) {
    if ($InputRecord.url -notmatch '/tar.gz/([0-9a-f]{40})$') { throw 'Expected a commit-pinned Git archive.' }
    $revision = $Matches[1]
    $template = Join-Path $SourceDir 'win/gitmanifest.in'
    if ((Get-Content -Raw -LiteralPath $template) -cne 'git-') { throw 'Pinned Tcl/Tk Git identity template changed.' }
    $identity = Join-Path $SourceDir 'manifest.uuid'
    # Source archives lack .git; use their pinned upstream identity, not the
    # application's checkout or a fabricated local Git commit.
    $null = New-Item -ItemType File -Path $identity -Value "git-$revision`n" -ErrorAction Stop
    return @{revision=$revision;sha256=(Get-FileHash -LiteralPath $identity -Algorithm SHA256).Hash.ToLowerInvariant()}
}
try {
    $manifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'windows-inputs.json') | ConvertFrom-Json
    if ($CheckInputs) {
        if ($Root -or $Receipt -or $Target -ne 'windows-x64') { throw 'CheckInputs cannot be combined with build arguments.' }
        $archiveDir = Absolute-Path $CheckInputs
        foreach ($item in $manifest.archives) { Check-Archive (Join-Path $archiveDir $item.filename) $item }
        Write-Output 'All pinned archive SHA256 checks passed.'
        exit 0
    }
    if ($Target -ne 'windows-x64') { throw 'Target must be windows-x64.' }
    $Root = Absolute-Path $Root
    $Receipt = Absolute-Path $Receipt
    $source = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ((Within $Root $source) -or (Within $source $Root)) { throw 'Root must be outside the source repository and its ancestors.' }
    if (Within $HOME $Root) { throw 'Root cannot be the home directory or its ancestor.' }
    foreach ($prefix in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:SystemRoot)) {
        if ($prefix -and ((Within $Root $prefix) -or (Within $prefix $Root))) { throw 'Root cannot overlap a global prefix.' }
    }
    if (Within $Receipt $source) { throw 'Receipt must be outside the source repository.' }
    if ((Within $Receipt $Root) -or (Test-Path -LiteralPath $Receipt)) { throw 'Receipt must be a new file outside Root.' }
    if (-not (Test-Path -LiteralPath (Split-Path $Receipt -Parent) -PathType Container)) { throw 'Receipt parent must already exist.' }
    if ((Test-Path -LiteralPath $Root) -and ((-not (Test-Path -LiteralPath $Root -PathType Container)) -or @(Get-ChildItem -Force -LiteralPath $Root).Count)) { throw 'Root must be new or empty.' }
    if (-not $IsWindows -or [Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne 'X64' -or [Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture -ne 'X64') { throw 'Native Windows AMD64 host and process are required.' }
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or later is required.' }
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Existing VS2022 vswhere.exe is required.' }
    $vs = (& $vswhere -latest -version '[17.0,18.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $vs) { throw 'VS2022 x64 tools are unavailable.' }
    $devcmd = Join-Path $vs 'Common7/Tools/VsDevCmd.bat'
    $devStdout = [IO.Path]::GetTempFileName()
    $devStderr = [IO.Path]::GetTempFileName()
    try {
        # Start-Process takes one raw argument line. A leading CALL avoids cmd's
        # special first/last-quote handling of paths under Program Files.
        $devArguments = "/d /c call `"$devcmd`" -no_logo -host_arch=amd64 -arch=amd64 -winsdk=10.0.22621.0 >nul && set"
        $devProcess = Start-Process -FilePath $env:ComSpec -ArgumentList $devArguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $devStdout -RedirectStandardError $devStderr
        if ($devProcess.ExitCode -ne 0) { throw ("VS2022 x64 environment initialization failed: " + (Get-Content -Raw -LiteralPath $devStderr)) }
        # Environment output can contain runner credentials; consume it locally
        # without printing it or retaining it in build logs/artifacts.
        $devEnv = Get-Content -LiteralPath $devStdout
    } finally {
        Remove-Item -LiteralPath $devStdout,$devStderr -Force
    }
    foreach ($line in $devEnv) { if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process') } }
    if ($env:VSCMD_ARG_TGT_ARCH -ne 'x64' -or $env:WindowsSDKVersion.TrimEnd('\') -ne '10.0.22621.0') { throw 'Selected x64 SDK environment does not match 10.0.22621.0.' }
    $bootstrap = (Get-Command python.exe -CommandType Application | Select-Object -First 1).Source
    $bootstrapInfo = & $bootstrap -I -c 'import sys,struct,json; assert sys.version_info >= (3,10) and struct.calcsize("P")==8; print(json.dumps({"executable":sys.executable,"version":sys.version,"prefix":sys.prefix}))'
    if ($LASTEXITCODE -ne 0) { throw 'Existing 64-bit bootstrap Python >=3.10 is required.' }
    $bootstrapPrefix = ($bootstrapInfo | ConvertFrom-Json).prefix
    if ((Within $Root $bootstrapPrefix) -or (Within $bootstrapPrefix $Root)) { throw 'Root cannot overlap the bootstrap Python installation.' }
    foreach ($name in @('MSBuild.exe','cl.exe','nmake.exe','dumpbin.exe')) { $null = Get-Command $name -CommandType Application }
    $null = New-Item -ItemType Directory -Path $Root -Force
    $logs = New-Item -ItemType Directory -Path (Join-Path $Root 'logs')
    function Run([string]$Exe, [string[]]$Arguments, [string]$Log, [int[]]$Allowed = @(0)) {
        Write-Output "Running $Log"
        Add-Content -LiteralPath (Join-Path $logs 'commands.jsonl') -Value (@{executable=$Exe; arguments=$Arguments; cwd=(Get-Location).Path} | ConvertTo-Json -Compress)
        & $Exe @Arguments 2>&1 | Tee-Object -FilePath (Join-Path $logs $Log) | Out-Host
        if ($LASTEXITCODE -notin $Allowed) { throw "$Exe failed with exit $LASTEXITCODE (see $Log)." }
    }
    Run 'MSBuild.exe' @('-version','-nologo') 'msbuild.txt'
    Run 'cl.exe' @('/Bv') 'compiler.txt' @(0,2)
    Run 'nmake.exe' @('/?') 'nmake.txt'
    $bootstrapInfo | Set-Content -LiteralPath (Join-Path $logs 'bootstrap.json')
    @{ImageOS=$env:ImageOS; ImageVersion=$env:ImageVersion; OS=[Environment]::OSVersion.VersionString; VisualStudio=$vs; VCToolsVersion=$env:VCToolsVersion; SDK=$env:WindowsSDKVersion; dumpbin=(Get-Command dumpbin.exe -CommandType Application | Select-Object -First 1).Source} | ConvertTo-Json | Set-Content (Join-Path $logs 'host.json')
    $downloads = New-Item -ItemType Directory -Path (Join-Path $Root 'downloads')
    $src = New-Item -ItemType Directory -Path (Join-Path $Root 'src')
    $downloadOptions = @{TimeoutSec=120;MaximumRetryCount=2;RetryIntervalSec=3}
    $webParameters = (Get-Command Invoke-WebRequest -CommandType Cmdlet).Parameters
    if ($webParameters.ContainsKey('OperationTimeoutSeconds')) { $downloadOptions.OperationTimeoutSeconds = 180 }
    if ($webParameters.ContainsKey('ProgressAction')) { $downloadOptions.ProgressAction = 'SilentlyContinue' }
    foreach ($item in $manifest.archives) {
        $archive = Join-Path $downloads $item.filename
        Write-Output "Downloading $($item.name): $($item.filename)"
        Invoke-WebRequest -Uri $item.url -OutFile $archive @downloadOptions
        Check-Archive $archive $item
        Write-Output "Verified $($item.name); extracting pinned archive"
        $destination = Join-Path $src $item.name
        Run $bootstrap @((Join-Path $PSScriptRoot 'extract_sources.py'),'--archive',$archive,'--output-dir',$destination,'--sha256',$item.sha256) "extract-$($item.name).txt"
        Write-Output "Prepared $($item.name) source"
    }
    $cpython = Join-Path $src 'cpython'
    $tcl = Join-Path $src 'tcl'
    $tk = Join-Path $src 'tk'
    $sourceIdentities = @{}
    foreach ($name in @('tcl','tk')) {
        $record = @($manifest.archives | Where-Object { $_.name -eq $name })[0]
        $sourceIdentities[$name] = Write-ArchiveIdentity (Join-Path $src $name) $record
    }
    $tcltk = Join-Path $Root 'tcltk'
    $openssl = Join-Path $src 'openssl/amd64'
    $ffi = Join-Path $src 'libffi/amd64'
    $zlib = Join-Path $src 'zlib'
    $build = Join-Path $cpython 'PCbuild/amd64'
    $python = Join-Path $Root 'python/python.exe'
    foreach ($path in @((Join-Path $openssl 'libcrypto-3.dll'),(Join-Path $openssl 'libssl-3.dll'))) {
        $record = @($manifest.binary_checks | Where-Object { $_.filename -eq (Split-Path $path -Leaf) })[0]
        Check-Archive $path $record
    }
    $savedEnv = @{}
    foreach ($name in @('PYTHONHOME','PYTHONPATH','TCL_LIBRARY','TK_LIBRARY','PythonForBuild')) { $savedEnv[$name] = [Environment]::GetEnvironmentVariable($name); [Environment]::SetEnvironmentVariable($name,$null,'Process') }
    try {
        $env:PythonForBuild = $bootstrap
        Push-Location $zlib
        try {
            Run 'nmake.exe' @('/nologo','-f','win32/Makefile.msc','LOC=-D_FILE_OFFSET_BITS=64','all','test','testdll') 'zlib-build-tests.txt'
        } finally { Pop-Location }
        # Tcl's dynamic build consumes these exact headers, import library and
        # DLL. Do not retain its bundled zlib 1.3.2 binary in the runtime.
        foreach ($name in @('zlib.h','zconf.h')) { Copy-Item (Join-Path $zlib $name) (Join-Path $tcl "compat/zlib/$name") -Force }
        foreach ($name in @('zlib1.dll','zdll.lib')) { Copy-Item (Join-Path $zlib $name) (Join-Path $tcl "compat/zlib/win64/$name") -Force }
        Push-Location (Join-Path $tcl 'win')
        try {
            Run 'nmake.exe' @('/nologo','-f','makefile.vc','MACHINE=AMD64','OPTS=msvcrt','BUILDDIRTOP=SDPR_Release_AMD64','core','shell','dlls') 'tcl-build.txt'
            Run 'nmake.exe' @('/nologo','-f','makefile.vc','MACHINE=AMD64','OPTS=msvcrt','BUILDDIRTOP=SDPR_Release_AMD64',"INSTALLDIR=$tcltk",'install-binaries','install-libraries') 'tcl-install.txt'
        } finally { Pop-Location }
        Push-Location (Join-Path $tk 'win')
        try {
            $tkArgs = @('/nologo','-f','makefile.vc','MACHINE=AMD64','OPTS=msvcrt','BUILDDIRTOP=SDPR_Release_AMD64',"TCLDIR=$tcl",("TCLSH_NATIVE=" + (Join-Path $tcltk 'bin/tclsh86t.exe')))
            Run 'nmake.exe' ($tkArgs + @('all')) 'tk-build.txt'
            Run 'nmake.exe' ($tkArgs + @("INSTALLDIR=$tcltk",'install-binaries','install-libraries')) 'tk-install.txt'
        } finally { Pop-Location }
        foreach ($relative in @('bin/tcl86t.dll','bin/tk86t.dll','bin/zlib1.dll','lib/tcl86t.lib','lib/tk86t.lib')) { if (-not (Test-Path (Join-Path $tcltk $relative))) { throw "Missing Tcl/Tk build input $relative" } }
        $propsPath = Join-Path $Root 'desktop-inputs.props'
        $props = [ordered]@{TclVersion='8.6.18';TkVersion='8.6.18';tcltkDir="$tcltk\";opensslOutDir="$openssl\";opensslIncludeDir="$openssl\include";libffiOutDir="$ffi\";libffiIncludeDir="$ffi\include";zlibDir="$zlib\";ExternalsDir="$Root\externals\"}
        $xml = '<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003"><PropertyGroup>'
        foreach ($key in $props.Keys) { $xml += "<$key>" + [Security.SecurityElement]::Escape($props[$key]) + "</$key>" }
        $xml += '</PropertyGroup></Project>'
        $xml | Set-Content -LiteralPath $propsPath
        # The isolated project omits unused external modules, never the repository.
        $project = Join-Path $cpython 'PCbuild/pcbuild.proj'
        [xml]$projectXml = Get-Content -Raw -LiteralPath $project
        $optional = @($projectXml.Project.ItemGroup.ExternalModules | Where-Object { $_.Include -eq '_bz2;_lzma;_sqlite3' })
        if ($optional.Count -ne 1) { throw 'Pinned CPython optional-module project shape changed.' }
        $null = $optional[0].ParentNode.RemoveChild($optional[0])
        $projectXml.Save($project)
        $msArgs = @('/nologo','/p:Configuration=Release','/p:Platform=x64','/p:PlatformToolset=v143','/p:WindowsTargetPlatformVersion=10.0.22621.0',"/p:ExternalProps=$propsPath",'/p:IncludeExternals=true','/p:IncludeSSL=true','/p:IncludeTkinter=true','/p:IncludeCTypes=true','/p:IncludeTests=false')
        # Evaluate imported properties in the actual _tkinter project, then compare.
        $effective = & MSBuild.exe (Join-Path $cpython 'PCbuild/_tkinter.vcxproj') @msArgs '-getProperty:TclVersion,TkVersion,tcltkDir,opensslOutDir,opensslIncludeDir,libffiOutDir,libffiIncludeDir,zlibDir,ExternalsDir'
        if ($LASTEXITCODE -ne 0) { throw 'MSBuild property evaluation failed.' }
        $effective | Set-Content (Join-Path $logs 'effective-properties.json')
        $evaluated = ($effective | Out-String | ConvertFrom-Json).Properties
        foreach ($key in $props.Keys) { if ($evaluated.$key -ne $props[$key]) { throw "MSBuild ignored explicit property $key" } }
        Run 'MSBuild.exe' (@($project,'/t:Build','/m:2',"/bl:$logs/cpython.binlog") + $msArgs) 'cpython-build.txt'
        Copy-Item (Join-Path $tcltk 'bin/zlib1.dll') (Join-Path $build 'zlib1.dll')
        $env:TCL_LIBRARY = Join-Path $tcltk 'lib/tcl8.6'
        Run (Join-Path $build 'python.exe') @((Join-Path $cpython 'PC/layout'),'--source',$cpython,'--build',$build,'--arch','amd64','--copy',(Split-Path $python -Parent),'--include-stable','--include-tcltk','--include-venv','--include-dev','--include-distutils') 'layout.txt'
        $env:TCL_LIBRARY = $null
        $env:PythonForBuild = $null
        $probePath = Join-Path $Root 'runtime-probe.py'
        @'
import ctypes, hashlib, importlib.util, json, os, pathlib, platform, ssl, struct, sys, tkinter, urllib.request, zlib
assert platform.python_version() == '3.11.18'
assert struct.calcsize('P') == 8 and platform.machine() == 'AMD64'
assert ssl.OPENSSL_VERSION.startswith('OpenSSL 3.5.9 ')
assert zlib.ZLIB_VERSION == zlib.ZLIB_RUNTIME_VERSION == '1.4'
assert zlib.decompress(zlib.compress(b'sdpr-native')) == b'sdpr-native'
assert hashlib.sha256(b'abc').hexdigest() == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
callback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)(lambda value: value + 1)
assert callback(41) == 42
dll_zlib = ctypes.CDLL(str(pathlib.Path(sys.prefix) / 'DLLs' / 'zlib1.dll'))
dll_zlib.zlibVersion.restype = ctypes.c_char_p
assert dll_zlib.zlibVersion() == b'1.4'
optional = {name: importlib.util.find_spec(name) is not None for name in ('_bz2', '_lzma', '_sqlite3')}
assert not any(optional.values()), optional
root = tkinter.Tk()
root.withdraw()
try:
    tcl, tk = root.tk.call('info', 'patchlevel'), root.tk.call('package', 'provide', 'Tk')
    assert tcl == tk == '8.6.18'
    assert root.tk.call('tk', 'windowingsystem') == 'win32'
    assert root.tk.call('zlib', 'decompress', root.tk.call('zlib', 'compress', 'sdpr-tcl')) == b'sdpr-tcl'
finally:
    root.destroy()
context = ssl.create_default_context()
assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
with urllib.request.urlopen('https://pypi.org/simple/', context=context, timeout=30) as response:
    assert response.status == 200
# Enumerate actual loaded modules, including the dynamically loaded libffi and Tk.
from ctypes import wintypes
kernel, psapi = ctypes.WinDLL('kernel32', use_last_error=True), ctypes.WinDLL('psapi', use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
modules, needed = (wintypes.HMODULE * 1024)(), wintypes.DWORD()
process = kernel.GetCurrentProcess()
assert psapi.EnumProcessModules(process, modules, ctypes.sizeof(modules), ctypes.byref(needed))
assert needed.value <= ctypes.sizeof(modules)
loaded = []
for module in modules[:needed.value // ctypes.sizeof(wintypes.HMODULE)]:
    buffer = ctypes.create_unicode_buffer(32768)
    assert psapi.GetModuleFileNameExW(process, module, buffer, len(buffer))
    loaded.append(buffer.value)
prefix, system = pathlib.Path(sys.prefix).resolve(), pathlib.Path(os.environ['SystemRoot']).resolve()
for filename in loaded:
    path = pathlib.Path(filename).resolve()
    assert path.is_relative_to(prefix) or path.is_relative_to(system), ('DLL outside private runtime / Windows', filename)
for name in ('libffi-8.dll', 'libssl-3.dll', 'libcrypto-3.dll', 'tcl86t.dll', 'tk86t.dll', 'zlib1.dll'):
    assert any(pathlib.Path(path).name.lower() == name for path in loaded), ('required DLL not loaded', name)
print(json.dumps(dict(python=sys.executable, python_version=platform.python_version(), architecture=platform.machine(), tcl_version=tcl, tk_version=tk, openssl_version=ssl.OPENSSL_VERSION, zlib_version=zlib.ZLIB_RUNTIME_VERSION, optional_modules=optional, loaded_dlls=loaded, https_verified=True)))
'@ | Set-Content -LiteralPath $probePath
        $runtimeRaw = & $python -I $probePath
        if ($LASTEXITCODE -ne 0) { throw 'Produced native runtime probe failed.' }
        $runtimeRaw | Set-Content (Join-Path $logs 'runtime.json')
        $runtime = $runtimeRaw | Out-String | ConvertFrom-Json
        $inventory = @()
        foreach ($binary in Get-ChildItem (Split-Path $python -Parent) -Recurse -File | Where-Object { $_.Extension -in @('.exe','.dll','.pyd') }) {
            # Validate every produced PE machine, including venv launchers.
            $bytes = [IO.File]::ReadAllBytes($binary.FullName)
            if ($bytes.Length -lt 64 -or $bytes[0] -ne 0x4d -or $bytes[1] -ne 0x5a) { throw "Invalid PE: $binary" }
            $pe = [BitConverter]::ToInt32($bytes, 0x3c)
            if ($pe -lt 0 -or $pe + 6 -gt $bytes.Length -or [BitConverter]::ToUInt32($bytes,$pe) -ne 0x4550 -or [BitConverter]::ToUInt16($bytes,$pe+4) -ne 0x8664) { throw "Non-AMD64 PE: $binary" }
            $inventory += @{path=[IO.Path]::GetRelativePath((Split-Path $python -Parent),$binary.FullName);sha256=(Get-FileHash $binary.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
            Run 'dumpbin.exe' @('/dependents',$binary.FullName) ("imports-" + $inventory.Count + '.txt')
        }
        $inventory | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $logs 'binary-inventory.json')
        Run $python @('-I','-m','ensurepip','--upgrade') 'ensurepip.txt'
        $staging = @()
        foreach ($name in @('zlib.h','zconf.h','win64/zlib1.dll','win64/zdll.lib')) {
            $staging += @{path="tcl/compat/zlib/$name";sha256=(Get-FileHash (Join-Path $tcl "compat/zlib/$name") -Algorithm SHA256).Hash.ToLowerInvariant()}
        }
        $result = [ordered]@{schema_version=1;target=$Target;python=$runtime.python;python_version=$runtime.python_version;architecture=$runtime.architecture;tcl_version=$runtime.tcl_version;tk_version=$runtime.tk_version;openssl_version=$runtime.openssl_version;zlib_version=$runtime.zlib_version;inputs=$manifest;native_review=$manifest.native_review;optional_modules=$runtime.optional_modules;runtime_checks=$runtime;binary_inventory=$inventory;toolchain_logs=$logs.FullName;bootstrap=($bootstrapInfo | ConvertFrom-Json);source_transform=@{file='PCbuild/pcbuild.proj';action='omit _bz2/_lzma/_sqlite3 in private copy';sha256=(Get-FileHash $project -Algorithm SHA256).Hash.ToLowerInvariant()};source_identities=$sourceIdentities;tcl_zlib_staging=$staging}
        $result | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $Receipt
        Write-Output "Runtime prepared; native review: $($manifest.native_review.status). Receipt: $Receipt"
    } finally {
        foreach ($name in $savedEnv.Keys) { [Environment]::SetEnvironmentVariable($name,$savedEnv[$name],'Process') }
    }
} catch {
    [Console]::Error.WriteLine("Windows toolchain: " + $_.Exception.Message)
    exit 1
}
