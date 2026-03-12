@echo off
chcp 65001 >nul
title F5-TTS API快速访问工具

:menu
cls
echo ========================================
echo 🎤 F5-TTS API快速访问工具
echo ========================================
echo.
echo 📊 服务状态检查...
curl -s http://localhost:80/config >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ TTS服务正在运行
    echo 🌐 服务地址: http://localhost:80
) else (
    echo ❌ TTS服务未运行
    echo.
    echo 请选择操作:
    echo [1] 启动TTS服务
    echo [2] 退出
    echo.
    set /p choice="请输入选择 (1-2): "
    if "!choice!"=="1" (
        echo 🚀 正在启动TTS服务...
        start "" "运行_自动开启接口服务.bat"
        echo ⏳ 请等待服务启动完成...
        timeout /t 10 /nobreak >nul
        goto menu
    ) else (
        exit /b 0
    )
)

echo.
echo ========================================
echo 📱 API访问选项
echo ========================================
echo [1] 打开网页界面 (推荐)
echo [2] 查看API技术信息
echo [3] 运行API演示脚本
echo [4] 创建公网访问地址
echo [5] 退出
echo.
set /p choice="请选择访问方式 (1-5): "

if "%choice%"=="1" (
    echo 🚀 正在打开网页界面...
    start http://localhost:80
    echo.
    echo 💡 使用提示:
    echo    1. 输入目标文本: 你好，欢迎使用F5-TTS语音合成服务！
    echo    2. 上传参考音频: reference.wav
    echo    3. 输入参考文本: 这是参考音频的文本内容
    echo    4. 点击开始生成
    echo.
    pause
    goto menu
    
) else if "%choice%"=="2" (
    echo 📊 API技术信息:
    echo.
    curl -s http://localhost:80/config | python -m json.tool 2>nul || (
        echo 📡 服务地址: http://localhost:80
        echo 🎤 API端点: /do_job
        echo 📊 Gradio版本: 5.21.0
        echo ⚡ 队列启用: True
    )
    echo.
    pause
    goto menu
    
) else if "%choice%"=="3" (
    echo 🎬 运行API演示脚本...
    python api_使用演示.py
    pause
    goto menu
    
) else if "%choice%"=="4" (
    echo 🌐 创建公网访问地址...
    echo 💡 这将使用cloudflared创建临时公网隧道
    echo.
    if exist "查看公网地址.bat" (
        call "查看公网地址.bat"
    ) else (
        echo ❌ 未找到公网地址脚本
        echo 💡 请运行: cloudflared tunnel --url http://localhost:80
    )
    pause
    goto menu
    
) else if "%choice%"=="5" (
    echo 👋 感谢使用F5-TTS API服务！
    exit /b 0
    
) else (
    echo ❌ 无效选择，请重新输入
    timeout /t 2 /nobreak >nul
    goto menu
)