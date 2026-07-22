#Requires -Version 5.1
<#
.SYNOPSIS
  SET-AGENTS bootstrap for Windows 10/11: managed WSL setup.
.DESCRIPTION
  The harness is Unix-native and runs inside WSL. This script: (1) ensures
  WSL2 with a distro (installs Ubuntu if none), (2) inside WSL installs
  git + gh, guides `gh auth login` (the private repo IS the access control),
  clones the repo to ~/SET-AGENTS and opens ./set-agents, (3) installs a
  `set-agents` command for cmd/PowerShell that proxies into WSL.
  Re-running is always safe (resumable after the WSL reboot step).
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
$env:WSL_UTF8 = "1"  # sane wsl.exe output encoding (WSL >= 0.64)

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

# ------------------------------------------------------------------ 1. WSL
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Write-Host "PS_FAIL wsl.exe no existe. Este Windows es demasiado viejo para WSL2"
    Write-Host "(se necesita Windows 10 build 19041+ o Windows 11)."
    exit 1
}

$distros = Get-WslDistros
if ($distros.Count -eq 0) {
    if ($DryRun) {
        Write-Host "PS_PLAN wsl-install (wsl --install -d Ubuntu)"
    } else {
        if (-not (Test-Admin)) {
            Write-Host "PS_NEED_ADMIN Instalar WSL requiere PowerShell como Administrador:"
            Write-Host "    1) Abrí PowerShell como Administrador"
            Write-Host "    2) Ejecutá:  wsl --install -d Ubuntu"
            Write-Host "    3) Reiniciá Windows si te lo pide"
            Write-Host "    4) Volvé a correr  .\install.ps1  (esta misma ventana normal sirve)"
            exit 1
        }
        Write-Host "Instalando WSL + Ubuntu (puede pedir reinicio)..."
        & wsl.exe --install -d Ubuntu
        Write-Host "PS_OK wsl-install"
        Write-Host "Si Windows pide reiniciar: reiniciá, abrí Ubuntu una vez (crea tu usuario)"
        Write-Host "y después volvé a correr  .\install.ps1"
        exit 0
    }
} else {
    Write-Host "PS_SKIP wsl-install (distros: $($distros -join ', '))"
}

if ($Distro -eq "") {
    # `wsl -l -q` lists the default distro first.
    $Distro = if ($distros.Count -gt 0) { $distros[0] } else { "Ubuntu" }
}
Write-Host "PS_OK distro=$Distro"

# ---------------------------------------------------- 2. bootstrap in WSL
$bootstrap = @'
set -e
if ! command -v git >/dev/null 2>&1 || ! command -v gh >/dev/null 2>&1; then
  echo "Instalando git + gh dentro de WSL (puede pedir tu password de sudo)..."
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
}

Write-Host "BOOTSTRAP_DONE_WINDOWS"
