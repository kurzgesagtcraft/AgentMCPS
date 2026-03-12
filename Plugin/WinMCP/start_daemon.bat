@echo off
REM WinMCP 守护进程启动脚本
REM 用于手动启动守护进程

echo Starting WinMCP Daemon...
node "%~dp0win-mcp-daemon.js" --daemon
