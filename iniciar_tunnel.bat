@echo off
echo ====================================
echo   YouTube MCP - Iniciando servidor
echo ====================================
echo.

:: Iniciar el servidor MCP en modo HTTP en segundo plano
echo [1/2] Iniciando servidor MCP en puerto 8000...
start "YouTube MCP Server" "C:\Users\balto\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\balto\proyectos-claude\youtube-mcp-server\server.py" --http

:: Esperar 3 segundos a que el servidor levante
timeout /t 3 /nobreak > nul

:: Iniciar cloudflared tunnel
echo [2/2] Iniciando tunel Cloudflare...
echo.
echo IMPORTANTE: Copia la URL que aparece abajo (*.trycloudflare.com)
echo y pegala en Claude Desktop como conector personalizado.
echo.
"%~dp0cloudflared.exe" tunnel --url http://localhost:8000

echo.
echo Tunel cerrado. Presiona cualquier tecla para salir.
pause > nul
