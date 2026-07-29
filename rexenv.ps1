# Reusable ReXGlue build environment (Windows).
# clang++ auto-detects the MSVC toolchain + Windows SDK, so no vcvars needed --
# we just put clang / cmake / ninja (and the SDK bin for rc.exe) on PATH.
$ninjaDir = "D:\Users\Jay\AppData\Local\Microsoft\WinGet\Packages\Ninja-build.Ninja_Microsoft.Winget.Source_8wekyb3d8bbwe"
$sdkBin = ""
$sdkRoot = "C:\Program Files (x86)\Windows Kits\10\bin"
if (Test-Path $sdkRoot) {
    $sdkVer = Get-ChildItem $sdkRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d+\.\d+' } | Sort-Object Name -Descending | Select-Object -First 1
    if ($sdkVer) { $sdkBin = Join-Path $sdkVer.FullName "x64" }
}
$env:Path = "C:\Program Files\LLVM\bin;C:\Program Files\CMake\bin;$ninjaDir;$sdkBin;" + $env:Path
