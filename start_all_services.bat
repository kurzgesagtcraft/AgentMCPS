@echo off
:: 使用 UTF-8 编码以支持中文文件名
chcp 65001 >nul
title AgentV All-in-One Starter
echo Starting all services for AgentV...

:: 注意：MCPO 服务器已弃用，现在使用 WinMCP 插件直接调用 windows-mcp
:: WinMCP 插件无需独立服务器进程，由 VCP 后端直接调用

:: 1. Start TTS Service
echo [1/3] Starting F5-TTS OpenAI API Server...
:: 使用 /d 指定工作目录，并直接调用 bat
start "F5-TTS Server" /d "%~dp0DMOSpeech2" cmd /c "启动OpenAI接口服务.bat"

echo Waiting for TTS service to initialize (10s)...
timeout /t 10 /nobreak >nul

:: 2. Start Node.js Backend
echo [2/3] Starting Node.js Backend Server...
start "Node.js Backend" cmd /c "node server.js"

:: 3. Start VCPChat Frontend
echo [3/3] Starting VCPChat Frontend...
start "VCPChat Frontend" /d "%~dp0VCPChat" cmd /c "npm start"

echo All services have been triggered. Please check the individual windows for status.
echo.
echo Note: WinMCP plugin is used for Windows automation (no MCPO server needed).
pause
