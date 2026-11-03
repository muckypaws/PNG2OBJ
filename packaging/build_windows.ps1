<#
=============================================================================
packaging/build_windows.ps1
-----------------------------------------------------------------------------
Build a standalone Windows executable of the PNG2OBJ CLI using Nuitka.

Entry point : PNG2ObjV3.py  (argparse CLI that imports the png2obj package)
Output      : dist\png2obj.exe            (onefile executable)
              build\windows\PNG2ObjV3.dist (standalone folder, used by the MSI)

NOTE: Nuitka cannot cross-compile. This script is authored to run on a native
Windows host (locally or on a `windows-latest` GitHub Actions runner). It has
NOT been executed on Linux; it is parse-checked only in this environment.

Usage (PowerShell):
    packaging\build_windows.ps1
    packaging\build_windows.ps1 -NoOnefile   # standalone folder only

Prerequisites (see packaging/README.md):
  - Windows 10/11
  - Python 3.11+ (python.org build recommended)
  - A C compiler: MSVC Build Tools, or let Nuitka download MinGW-w64
  - pip install -r requirements.txt -r requirements-build.txt

Shared Nuitka flags live in packaging/nuitka_common.txt (single source of
truth). GUI (PySide6/VTK) flags are added there, not here.
=============================================================================
#>
[CmdletBinding()]
param(
    # Skip the onefile build and produce only the standalone folder tree
    # (which is what the WiX MSI packages).
    [switch]$NoOnefile
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# --- Resolve paths ----------------------------------------------------------
$ScriptDir       = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot        = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$CommonFlagsFile = Join-Path $ScriptDir 'nuitka_common.txt'

$EntryPoint = Join-Path $RepoRoot 'PNG2ObjV3.py'
$BuildDir   = Join-Path $RepoRoot 'build\windows'
$DistDir    = Join-Path $RepoRoot 'dist'
$OutputName = 'png2obj'
$IconFile   = Join-Path $ScriptDir 'assets\png2obj.ico'   # optional; used if present

if ($env:PYTHON) { $Python = $env:PYTHON } else { $Python = 'python' }

Set-Location $RepoRoot

Write-Host "==> PNG2OBJ Windows build"
Write-Host "    repo root : $RepoRoot"
Write-Host "    entry     : $EntryPoint"
Write-Host "    python    : $(& $Python --version 2>&1)"

# --- Sanity checks ----------------------------------------------------------
if (-not (Test-Path $EntryPoint)) {
    throw "Entry point not found: $EntryPoint"
}
if (-not (Test-Path $CommonFlagsFile)) {
    throw "Shared flags file not found: $CommonFlagsFile"
}
& $Python -c "import nuitka" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Nuitka is not installed for '$Python'. Run: $Python -m pip install -r requirements.txt -r requirements-build.txt"
}

# --- Load shared flags ------------------------------------------------------
# Strip comments (# ...) and blank lines; keep each remaining line as one arg.
$CommonFlags = Get-Content $CommonFlagsFile |
    ForEach-Object { $_.Trim() } |
    Where-Object   { $_ -ne '' -and -not $_.StartsWith('#') }

# --- Windows-specific flags -------------------------------------------------
$WindowsFlags = @(
    "--output-dir=$BuildDir"
    "--output-filename=$OutputName.exe"
    # CLI app: keep the console window so argparse output/errors are visible.
    # ---------------------------------------------------------------------
    # FUTURE GUI EXTENSION POINT (Windows):
    #   For the windowed PySide6 GUI, switch the console off so no terminal
    #   flashes on launch:
    #       --windows-console-mode=disable
    #   and enable PySide6/VTK in packaging/nuitka_common.txt.
    # ---------------------------------------------------------------------
    '--windows-console-mode=force'
)
if (-not $NoOnefile) {
    $WindowsFlags += '--onefile'
}
if (Test-Path $IconFile) {
    $WindowsFlags += "--windows-icon-from-ico=$IconFile"
} else {
    Write-Host "    (no icon at $IconFile; building without a custom exe icon)"
}

New-Item -ItemType Directory -Force -Path $BuildDir, $DistDir | Out-Null

Write-Host "==> Running Nuitka (standalone)..."
$AllArgs = @('-m', 'nuitka') + $CommonFlags + $WindowsFlags + @($EntryPoint)
Write-Host "    $Python $($AllArgs -join ' ')"
& $Python @AllArgs
if ($LASTEXITCODE -ne 0) { throw "Nuitka build failed with exit code $LASTEXITCODE" }

# --- Collect artifacts ------------------------------------------------------
if (-not $NoOnefile) {
    $ProducedExe = Join-Path $BuildDir "$OutputName.exe"
    if (-not (Test-Path $ProducedExe)) {
        throw "Expected onefile executable not found: $ProducedExe"
    }
    Copy-Item -Force $ProducedExe (Join-Path $DistDir "$OutputName.exe")
    Write-Host "==> Onefile executable: $(Join-Path $DistDir "$OutputName.exe")"
}

# The standalone folder (used by the WiX MSI) is PNG2ObjV3.dist by default.
$DistFolder = Join-Path $BuildDir 'PNG2ObjV3.dist'
if (Test-Path $DistFolder) {
    Write-Host "==> Standalone folder: $DistFolder"
    Write-Host "    (packaged into an MSI by packaging\windows\PNG2OBJ.wxs)"
} else {
    Write-Host "WARNING: standalone folder not found at $DistFolder (onefile-only build?)."
}

Write-Host "==> Done."
Write-Host "    Next steps:"
Write-Host "      - Build the MSI: see packaging/README.md 'Windows (MSI)'."
Write-Host "      - Codesign (Authenticode) requires your certificate: see README."
