@echo off
rem set-agents shim for cmd/PowerShell: the harness lives inside WSL.
rem install.ps1 generates a copy pinned to your distro; this default uses WSL's default distro.
wsl -e bash -lc "\"$HOME/SET-AGENTS/set-agents\" \"$@\"" set-agents %*
