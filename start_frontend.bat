@echo off
chcp 65001
echo ========================================
echo Starting VCP Chat Frontend...
echo Time: %date% %time%
echo ========================================

:: 注意：MCPO 服务器已弃用，现在使用 WinMCP 插件直接调用 windows-mcp
:: WinMCP 插件无需独立服务器进程，由 VCP 后端直接调用

:: 创建日志目录
if not exist "logs" mkdir logs

:: 设置日志文件路径（带日期时间戳）
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_FILE=logs\frontend_%datetime:~0,8%_%datetime:~8,6%.log

echo Log file: %LOG_FILE%
echo.

:: 记录启动信息到日志
echo [%date% %time%] VCP Chat Frontend Starting... >> %LOG_FILE%
echo [%date% %time%] WinMCP plugin will be called by VCP backend >> %LOG_FILE%

:: 直接启动 VCPChat 前端
cd /d "%~dp0VCPChat"
echo [%date% %time%] Entering VCPChat directory >> ..\%LOG_FILE%
echo [%date% %time%] Executing start.bat >> ..\%LOG_FILE%

:: 启动前端（不使用 tee，直接调用）
call start.bat

echo [%date% %time%] Frontend process ended >> ..\%LOG_FILE%
