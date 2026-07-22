@echo off
rem set-agents shim for cmd/PowerShell: the harness lives inside WSL.
wsl -e bash -lc "~/SET-AGENTS/set-agents %*"
