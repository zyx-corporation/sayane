# Sayane installer for Windows (PowerShell 5.1+).
# Usage:
#   irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
#   .\scripts\install.ps1
#
# Environment:
#   $env:SAYANE_REPO          GitHub repo (default: zyx-corporation/sayane)
#   $env:SAYANE_REF            Git ref (default: main)
#   $env:SAYANE_INSTALL_DIR    Install root (default: %LOCALAPPDATA%\Sayane)
#   $env:SAYANE_SOURCE_DIR     Local checkout for editable install (CI/dev)
#   $env:SAYANE_DEV             Set to 1 for [dev] extras
#   $env:SAYANE_SKIP_INIT       Set to 1 to skip sayane init
#   $env:SAYANE_YES             Set to 1 to skip confirmation

$ErrorActionPreference = "Stop"

$SayaneRepo = if ($env:SAYANE_REPO) { $env:SAYANE_REPO } else { "zyx-corporation/sayane" }
$SayaneRef = if ($env:SAYANE_REF) { $env:SAYANE_REF } else { "main" }
$InstallDir = if ($env:SAYANE_INSTALL_DIR) {
    $env:SAYANE_INSTALL_DIR
} else {
    Join-Path $env:LOCALAPPDATA "Sayane"
}
$VenvDir = Join-Path $InstallDir "venv"
$BinDir = Join-Path $InstallDir "bin"
$Wrapper = Join-Path $BinDir "sayane.cmd"
$GitUrl = "https://github.com/$SayaneRepo.git"

function Write-Info($Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "warning: $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "error: $Message" -ForegroundColor Red; exit 1 }

function Confirm-Install {
    if ($env:SAYANE_YES -eq "1") { return }
    if ([Console]::IsInputRedirected) {
        $env:SAYANE_YES = "1"
        return
    }
    $reply = Read-Host "Install Sayane to $InstallDir? [y/N]"
    if ($reply -notmatch '^(y|Y|yes|YES)$') { Write-Err "Aborted." }
}

function Find-Python {
    $candidates = @(
        @("py", @("-3.13")),
        @("py", @("-3.12")),
        @("py", @("-3.11")),
        @("python3", @()),
        @("python", @())
    )
    foreach ($c in $candidates) {
        $exe = $c[0]
        $args = $c[1]
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        try {
            $verArgs = $args + @("-c", "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)")
            & $exe @verArgs | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return @{ Exe = $exe; Args = $args }
            }
        } catch { continue }
    }
    Write-Err "Python 3.11+ is required. Install from https://www.python.org/downloads/ (check 'Add to PATH')."
}

function Ensure-Venv($Python) {
    $pyExe = $Python.Exe
    $pyArgs = $Python.Args
    if (-not (Test-Path $VenvDir)) {
        Write-Info "Creating virtualenv at $VenvDir"
        & $pyExe @pyArgs -m venv $VenvDir
    } else {
        Write-Info "Using existing virtualenv at $VenvDir"
    }
    if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create venv. Try: py -3.12 -m pip install --upgrade pip" }
}

function Install-Package {
    $pip = Join-Path $VenvDir "Scripts\pip.exe"
    Write-Info "Upgrading pip"
    & $pip install --upgrade pip wheel | Out-Null

    if ($env:SAYANE_SOURCE_DIR) {
        $spec = if ($env:SAYANE_DEV -eq "1") {
            "-e", "$($env:SAYANE_SOURCE_DIR)[dev]"
        } else {
            "-e", $env:SAYANE_SOURCE_DIR
        }
        Write-Info "Installing from local source: $($env:SAYANE_SOURCE_DIR)"
        & $pip install @spec
    } else {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Err "git is required. Install Git for Windows: https://git-scm.com/download/win"
        }
        $spec = if ($env:SAYANE_DEV -eq "1") {
            "sayane[dev] @ git+$GitUrl@$SayaneRef"
        } else {
            "sayane @ git+$GitUrl@$SayaneRef"
        }
        Write-Info "Installing ${SayaneRepo}@${SayaneRef}"
        & $pip install $spec
    }
    if ($LASTEXITCODE -ne 0) { Write-Err "pip install failed" }
}

function Install-Wrapper {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $sayaneExe = Join-Path $VenvDir "Scripts\sayane.exe"
    @"
@echo off
setlocal
"$sayaneExe" %*
"@ | Set-Content -Path $Wrapper -Encoding ASCII
    Write-Info "Installed wrapper: $Wrapper"
}

function Add-UserPath {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -split ';' -contains $BinDir) { return }
    Write-Info "Adding $BinDir to user PATH"
    $newPath = if ($userPath) { "$BinDir;$userPath" } else { $BinDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$BinDir;$env:Path"
    Write-Warn "Restart the terminal (or log off/on) if 'sayane' is not found immediately."
}

function Maybe-Init {
    if ($env:SAYANE_SKIP_INIT -eq "1") { return }
    $profile = Join-Path $env:USERPROFILE ".sayane\profiles\default\sayane.profile.yaml"
    if (Test-Path $profile) {
        Write-Info "Profile store already exists; skipping sayane init"
        return
    }
    Write-Info "Initializing profile store (~/.sayane)"
    & $Wrapper init
}

Confirm-Install
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$python = Find-Python
Write-Info ("Using Python via {0}" -f $python.Exe)
Ensure-Venv $python
Install-Package
Install-Wrapper
Add-UserPath
Maybe-Init
Write-Info "Done. Run: sayane --version"
Write-Info "For Bridge + Chrome Extension, use native Windows Python (not WSL). See docs/install.md"
