@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo DEPRECATED - 此脚本已弃用
echo ========================================
echo.
echo MCPO 服务器已不再需要！
echo.
echo VCPToolBox 现在使用 WinMCP 插件直接调用 windows-mcp，
echo 无需独立的 MCPO 服务器进程。
echo.
echo WinMCP 插件优势：
echo - 无端口冲突问题
echo - 更快的响应速度
echo - 更简单的架构
echo - 无需额外启动服务
echo.
echo 如需启动 VCP 服务，请使用：
echo   - start_all_services.bat (启动所有服务)
echo   - start_frontend.bat (仅启动前端)
echo.
echo ========================================
pause
