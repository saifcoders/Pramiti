@echo off
if exist "%~dp0cloudflared.exe" (
    "%~dp0cloudflared.exe" tunnel --protocol http2 --http-host-header localhost:5173 --url http://localhost:5173 > "%~dp0frontend_tunnel.log" 2>&1
) else (
    cloudflared tunnel --protocol http2 --http-host-header localhost:5173 --url http://localhost:5173 > "%~dp0frontend_tunnel.log" 2>&1
)
