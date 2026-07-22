#Requires -Version 5.1
<#
.SYNOPSIS
  SET-AGENTS bootstrap for Windows 10/11: managed WSL setup.
.DESCRIPTION
  The harness is Unix-native and runs inside WSL. This script: (1) ensures
  WSL2 with a distro (installs Ubuntu if none; self-elevates via UAC and
  auto-resumes after a reboot through a RunOnce entry), (2) auto-provisions
  the Linux user (no OOBE screens; passwordless sudo inside WSL, documented
  and reversible — see README.md), (3) inside WSL installs git + gh, guides
  `gh auth login` (the private repo IS the access control), clones the repo
  to ~/SET-AGENTS and opens ./set-agents, (4) installs a `set-agents`
  command for cmd/PowerShell that proxies into WSL.
  Re-running is always safe.
.PARAMETER DryRun
  Print the plan (PS_PLAN/PS_SKIP markers) without changing anything.
.PARAMETER Distro
  WSL distro to use (default: the user's default distro, or Ubuntu if none).
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Distro = ""
)

$ErrorActionPreference = "Stop"
$Repo = "federico0330/SET-AGENTS"
$RunOnceKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
$env:WSL_UTF8 = "1"  # sane wsl.exe output encoding (WSL >= 0.64)

Write-Host "SET-AGENTS para Windows — esto es lo que vas a ver (detalle: README.md):"
Write-Host "  1) puede aparecer un diálogo de administrador (UAC) → hacé clic en 'Sí'"
Write-Host "  2) puede pedir un reinicio → la instalación se reanuda sola al volver"
Write-Host "  3) tu usuario de Linux se crea automáticamente (sin pantallas de setup)"
Write-Host "  4) una ventana del navegador para iniciar sesión en GitHub"
Write-Host ""

function Get-WslDistros {
    try {
        $list = & wsl.exe -l -q 2>$null
        if ($LASTEXITCODE -ne 0) { return @() }
        return @($list | Where-Object { $_ -and $_.Trim() -ne "" } | ForEach-Object { $_.Trim() })
    } catch {
        return @()
    }
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal $identity).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Register-AutoResume {
    Set-ItemProperty -Path $RunOnceKey -Name "set-agents-resume" `
        -Value "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Write-Host "PS_OK auto-resume (la instalación continúa sola tras un reinicio)"
}

function Remove-AutoResume {
    Remove-ItemProperty -Path $RunOnceKey -Name "set-agents-resume" -ErrorAction SilentlyContinue
}

function Initialize-DistroUser($TargetDistro) {
    # Skip the interactive OOBE: create the user (Windows username, sanitized),
    # make it the default via /etc/wsl.conf, passwordless sudo via a sudoers
    # drop-in (documented + reversible in README.md).
    $who = ""
    try { $who = ("$(& wsl.exe -d $TargetDistro -u root -- whoami 2>$null)").Trim() } catch { }
    if ($LASTEXITCODE -ne 0 -or $who -ne "root") {
        Write-Host "PS_WARN linux-user: no pude entrar como root a $TargetDistro (seguimos igual)"
        return
    }
    $current = ("$(& wsl.exe -d $TargetDistro -- whoami 2>$null)").Trim()
    if ($current -and $current -ne "root") {
        Write-Host "PS_SKIP linux-user ($current)"
        return
    }
    $user = ($env:USERNAME.ToLower() -replace '[^a-z0-9]', '')
    if (-not $user) { $user = "agente" }
    $setup = "id -u $user >/dev/null 2>&1 || useradd -m -s /bin/bash $user; " +
             "printf '[user]\ndefault=%s\n' $user > /etc/wsl.conf; " +
             "echo '$user ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/set-agents; " +
             "chmod 440 /etc/sudoers.d/set-agents"
    & wsl.exe -d $TargetDistro -u root -- bash -c $setup
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PS_WARN linux-user: la creación automática falló — abrí $TargetDistro una vez y re-ejecutá"
        return
    }
    & wsl.exe --terminate $TargetDistro 2>$null
    Write-Host "PS_OK linux-user ($user)"
}

# ------------------------------------------------------------------ 1. WSL
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    if ($DryRun) {
        Write-Host "PS_PLAN wsl-install (wsl.exe ausente; se instalaría WSL2 + Ubuntu)"
    } else {
        Write-Host "PS_FAIL wsl.exe no existe. Este Windows es demasiado viejo para WSL2"
        Write-Host "(se necesita Windows 10 build 19041+ o Windows 11)."
        exit 1
    }
}

$distros = Get-WslDistros
if ($distros.Count -eq 0) {
    if ($DryRun) {
        Write-Host "PS_PLAN wsl-install (wsl --install -d Ubuntu, con auto-elevación y auto-resume)"
    } else {
        if (-not (Test-Admin)) {
            Write-Host "PS_ELEVATE instalar WSL necesita Administrador — aceptá el diálogo UAC..."
            try {
                Start-Process powershell -Verb RunAs -ArgumentList @(
                    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
                exit 0
            } catch {
                Write-Host "PS_NEED_ADMIN No aceptaste el UAC. Camino manual:"
                Write-Host "    1) Abrí PowerShell como Administrador"
                Write-Host "    2) Ejecutá:  wsl --install -d Ubuntu"
                Write-Host "    3) Reiniciá Windows si te lo pide"
                Write-Host "    4) Volvé a correr  .\install.ps1"
                exit 1
            }
        }
        Register-AutoResume
        Write-Host "Instalando WSL + Ubuntu..."
        & wsl.exe --install -d Ubuntu
        Write-Host "PS_OK wsl-install"
        $distros = Get-WslDistros
        if ($distros.Count -eq 0) {
            Write-Host "Reiniciá Windows: al volver a iniciar sesión la instalación continúa sola."
            exit 0
        }
    }
} else {
    Write-Host "PS_SKIP wsl-install (distros: $($distros -join ', '))"
}

if ($Distro -eq "") {
    # `wsl -l -q` lists the default distro first.
    $Distro = if ($distros.Count -gt 0) { $distros[0] } else { "Ubuntu" }
}
Write-Host "PS_OK distro=$Distro"

if (-not $DryRun) {
    Initialize-DistroUser $Distro
}

# ---------------------------------------------------- 2. bootstrap in WSL
$bootstrap = @'
set -e
if ! command -v git >/dev/null 2>&1 || ! command -v gh >/dev/null 2>&1; then
  echo "Instalando git + gh dentro de WSL..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y git gh
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --needed --noconfirm git github-cli
  else
    echo "Instalá git y gh a mano en esta distro y re-ejecutá."
    exit 1
  fi
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "Inicia sesión en GitHub (necesitás estar invitado al repo privado):"
  gh auth login
fi
if [ ! -d "$HOME/SET-AGENTS" ]; then
  gh repo clone federico0330/SET-AGENTS "$HOME/SET-AGENTS"
fi
exec "$HOME/SET-AGENTS/set-agents"
'@

if ($DryRun) {
    Write-Host "PS_PLAN wsl-bootstrap (git+gh, gh auth login, clone $Repo, ./set-agents)"
} else {
    & wsl.exe -d $Distro -- bash -lc $bootstrap
}

# ------------------------------------------------------------- 3. el shim
$shimDir = Join-Path $env:LOCALAPPDATA "set-agents"
$shim = Join-Path $shimDir "set-agents.cmd"
if ($DryRun) {
    Write-Host "PS_PLAN shim ($shim + PATH de usuario)"
} else {
    New-Item -ItemType Directory -Force -Path $shimDir | Out-Null
    Copy-Item -Force (Join-Path $PSScriptRoot "set-agents.cmd") $shim
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$shimDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$shimDir", "User")
        Write-Host "PS_OK shim (abrí una terminal nueva para que 'set-agents' aparezca en el PATH)"
    } else {
        Write-Host "PS_SKIP shim (ya estaba en el PATH)"
    }
    Remove-AutoResume
}

Write-Host "BOOTSTRAP_DONE_WINDOWS"
