# Omomuki installer for Windows (PowerShell 5.1+).
# Usage:
#   irm https://raw.githubusercontent.com/zyx-corporation/omomuki/main/scripts/install.ps1 | iex
#   .\scripts\install.ps1
#
# Environment:
#   $env:OMOMUKI_REPO          GitHub repo (default: zyx-corporation/omomuki)
#   $env:OMOMUKI_REF            Git ref (default: main)
#   $env:OMOMUKI_INSTALL_DIR    Install root (default: %LOCALAPPDATA%\Omomuki)
#   $env:OMOMUKI_SOURCE_DIR     Local checkout for editable install (CI/dev)
#   $env:OMOMUKI_DEV             Set to 1 for [dev] extras
#   $env:OMOMUKI_SKIP_INIT       Set to 1 to skip omomuki init
#   $env:OMOMUKI_YES             Set to 1 to skip confirmation

$ErrorActionPreference = "Stop"

$OmomukiRepo = if ($env:OMOMUKI_REPO) { $env:OMOMUKI_REPO } else { "zyx-corporation/omomuki" }
$OmomukiRef = if ($env:OMOMUKI_REF) { $env:OMOMUKI_REF } else { "main" }
$InstallDir = if ($env:OMOMUKI_INSTALL_DIR) {
    $env:OMOMUKI_INSTALL_DIR
} else {
    Join-Path $env:LOCALAPPDATA "Omomuki"
}
$VenvDir = Join-Path $InstallDir "venv"
$BinDir = Join-Path $InstallDir "bin"
$Wrapper = Join-Path $BinDir "omomuki.cmd"
$GitUrl = "https://github.com/$OmomukiRepo.git"

function Write-Info($Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "warning: $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "error: $Message" -ForegroundColor Red; exit 1 }

function Confirm-Install {
    if ($env:OMOMUKI_YES -eq "1") { return }
    if ([Console]::IsInputRedirected) {
        $env:OMOMUKI_YES = "1"
        return
    }
    $reply = Read-Host "Install Omomuki to $InstallDir? [y/N]"
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

    if ($env:OMOMUKI_SOURCE_DIR) {
        $spec = if ($env:OMOMUKI_DEV -eq "1") {
            "-e", "$($env:OMOMUKI_SOURCE_DIR)[dev]"
        } else {
            "-e", $env:OMOMUKI_SOURCE_DIR
        }
        Write-Info "Installing from local source: $($env:OMOMUKI_SOURCE_DIR)"
        & $pip install @spec
    } else {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Err "git is required. Install Git for Windows: https://git-scm.com/download/win"
        }
        $spec = if ($env:OMOMUKI_DEV -eq "1") {
            "omomuki[dev] @ git+$GitUrl@$OmomukiRef"
        } else {
            "omomuki @ git+$GitUrl@$OmomukiRef"
        }
        Write-Info "Installing ${OmomukiRepo}@${OmomukiRef}"
        & $pip install $spec
    }
    if ($LASTEXITCODE -ne 0) { Write-Err "pip install failed" }
}

function Install-Wrapper {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $omomukiExe = Join-Path $VenvDir "Scripts\omomuki.exe"
    @"
@echo off
setlocal
"$omomukiExe" %*
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
    Write-Warn "Restart the terminal (or log off/on) if 'omomuki' is not found immediately."
}

function Maybe-Init {
    if ($env:OMOMUKI_SKIP_INIT -eq "1") { return }
    $profile = Join-Path $env:USERPROFILE ".omomuki\profiles\default\omomuki.profile.yaml"
    if (Test-Path $profile) {
        Write-Info "Profile store already exists; skipping omomuki init"
        return
    }
    Write-Info "Initializing profile store (~/.omomuki)"
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
Write-Info "Done. Run: omomuki --version"
Write-Info "For Bridge + Chrome Extension, use native Windows Python (not WSL). See docs/install.md"
