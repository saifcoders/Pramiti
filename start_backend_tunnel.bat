@echo off
if exist "%~dp0cloudflared.exe" (
    "%~dp0cloudflared.exe" tunnel --url http://localhost:8000 > "%~dp0backend_tunnel.log" 2>&1
) else (
    cloudflared tunnel --url http://localhost:8000 > "%~dp0backend_tunnel.log" 2>&1
)
