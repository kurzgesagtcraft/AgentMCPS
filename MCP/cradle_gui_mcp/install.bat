@echo off
echo ========================================
echo Cradle GUI MCP Server - 安装脚本
echo 飒曦菲视觉感知版
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 创建虚拟环境...
python -m venv .venv

echo [2/3] 激活虚拟环境并安装依赖...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo [3/3] 安装完成!
echo.
echo ========================================
echo 安装成功! 现在可以配置 MCP 设置了
echo ========================================
pause