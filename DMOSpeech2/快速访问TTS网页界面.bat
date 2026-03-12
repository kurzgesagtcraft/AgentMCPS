@echo off
chcp 65001 >nul
title F5-TTS 网页界面快速访问

echo ========================================
echo 🎤 F5-TTS 语音合成服务
echo ========================================
echo.
echo 📋 服务状态检查...

rem 检查服务是否运行
curl -s http://localhost:80/config >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ TTS服务正在正常运行
    echo 🌐 服务地址: http://localhost:80
    echo.
    
    echo 🚀 正在打开网页界面...
    start http://localhost:80
    echo.
    
    echo ========================================
    echo 📖 使用说明
    echo ========================================
    echo 1. 在"输入需要生成的文本"框中输入目标文本
    echo 2. 上传参考音频文件或从列表中选择
    echo 3. 在"参考音频文本"框中输入对应文本
    echo 4. 点击"开始生成"按钮
    echo 5. 等待处理完成，播放或下载结果
    echo.
    
    echo 📝 示例参数:
    echo    目标文本: 你好，欢迎使用F5-TTS语音合成服务！
    echo    参考音频: reference.wav (或上传其他音频)
    echo    参考文本: 这是参考音频的文本内容
    echo.
    
    echo 💡 提示: 网页界面是最稳定的调用方式
    echo    没有依赖版本冲突问题，推荐使用！
) else (
    echo ❌ TTS服务未运行
    echo.
    echo 🔧 请先启动TTS服务:
    echo    1. 运行 "运行_自动开启接口服务.bat"
    echo    2. 等待服务启动完成
    echo    3. 再次运行此脚本
    echo.
    
    set /p choice="是否现在启动TTS服务? (y/n): "
    if /i "%choice%"=="y" (
        echo.
        echo 🚀 正在启动TTS服务...
        start "" "运行_自动开启接口服务.bat"
        echo.
        echo ⏳ 请等待服务启动完成后，再次运行此脚本
    )
)

echo.
echo ========================================
pause