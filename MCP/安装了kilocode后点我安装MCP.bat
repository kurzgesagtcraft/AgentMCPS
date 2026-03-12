@echo off
setlocal enabledelayedexpansion

REM 脚本：备份并覆盖 MCP 设置文件
REM 作者：Kilo Code
REM 日期：2026-01-26

echo ========================================
echo MCP 设置更新脚本
echo ========================================

REM 设置路径
set "SOURCE_FILE=%~dp0mcp_settings.json"
set "TARGET_FILE=%USERPROFILE%\AppData\Roaming\Code\User\globalStorage\kilocode.kilo-code\settings\mcp_settings.json"
set "BACKUP_FILE=%TARGET_FILE%.bak"

echo 源文件：%SOURCE_FILE%
echo 目标文件：%TARGET_FILE%
echo 备份文件：%BACKUP_FILE%

REM 检查源文件是否存在
if not exist "%SOURCE_FILE%" (
    echo 错误：源文件不存在！
    pause
    exit /b 1
)

REM 备份目标文件（如果存在）
if exist "%TARGET_FILE%" (
    echo 正在备份目标文件...
    copy "%TARGET_FILE%" "%BACKUP_FILE%" >nul
    if errorlevel 1 (
        echo 警告：备份失败，但继续执行...
    ) else (
        echo 备份成功：%BACKUP_FILE%
    )
) else (
    echo 目标文件不存在，无需备份。
)

REM 复制源文件到目标
echo 正在复制源文件到目标...
copy "%SOURCE_FILE%" "%TARGET_FILE%" >nul
if errorlevel 1 (
    echo 错误：复制失败！
    pause
    exit /b 1
) else (
    echo 复制成功！
)

echo.
echo 操作完成。
pause