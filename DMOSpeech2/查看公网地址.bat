@echo off
title 查看公网地址 - F5-TTS v3版本
echo ================================
echo 公网地址查看工具
echo ================================
echo.

echo 正在创建新的公网隧道...
echo 请等待几秒钟...
echo.

echo ⭐ 重要提示: 请查看下方显示的公网地址 ⭐
echo.

rem 启动cloudflared并显示地址
cloudflared tunnel --url http://localhost:80

echo.
echo 隧道已断开连接
pause