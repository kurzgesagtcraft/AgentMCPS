@echo off
chcp 65001 >nul
title F5-TTS API调用测试 - 项目内置Python环境

echo =====================================
echo 🎤 F5-TTS API调用测试
echo 项目内置Python环境版本
echo =====================================
echo.

rem 设置项目Python环境变量
set PYTHON_PATH=%cd%\py312
set PYTHONHOME=
set PYTHONPATH=
set PYTHONEXECUTABLE=%PYTHON_PATH%\python.exe
set PYTHONWEXECUTABLE=%PYTHON_PATH%\pythonw.exe
set PYTHON_EXECUTABLE=%PYTHON_PATH%\python.exe
set PYTHONW_EXECUTABLE=%PYTHON_PATH%\pythonw.exe
set PYTHON_BIN_PATH=%PYTHON_EXECUTABLE%
set PYTHON_LIB_PATH=%PYTHON_PATH%\Lib\site-packages
set CU_PATH=%PYTHON_PATH%\Lib\site-packages\torch\lib
set cuda_PATH=%PYTHON_PATH%\Library\bin
set FFMPEG_PATH=%cd%\py312\ffmpeg\bin
set PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%FFMPEG_PATH%;%CU_PATH%;%cuda_PATH%;%PATH%
set HF_ENDPOINT=https://hf-mirror.com
set HF_HOME=%CD%\hf_download
set TRANSFORMERS_CACHE=%CD%\tf_download
set XFORMERS_FORCE_DISABLE_TRITON=1
set PYTHONIOENCODING=utf-8

echo 🔍 检查项目Python环境...
if exist "%PYTHON_EXECUTABLE%" (
    echo ✅ 项目Python环境: %PYTHON_EXECUTABLE%
) else (
    echo ❌ 未找到项目Python环境: %PYTHON_EXECUTABLE%
    echo 💡 请确保项目完整，包含py312文件夹
    pause
    exit /b 1
)

echo.
echo 🔍 检查TTS服务状态...
curl -s http://localhost:80/config >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ TTS服务正在运行
) else (
    echo ❌ TTS服务未运行
    echo.
    set /p choice="是否启动TTS服务? (y/n): "
    if /i "!choice!"=="y" (
        echo 🚀 正在启动TTS服务...
        start "" "运行_自动开启接口服务.bat"
        echo ⏳ 请等待服务启动完成，然后按任意键继续...
        pause >nul
    ) else (
        echo 💡 请先启动TTS服务再运行此测试
        pause
        exit /b 1
    )
)

echo.
echo 📁 检查参考音频文件...
if exist "reference.wav" (
    echo ✅ 找到参考音频: reference.wav
) else (
    echo ❌ 未找到参考音频文件: reference.wav
    echo 💡 请确保当前目录有reference.wav文件
    pause
    exit /b 1
)

echo.
echo 🚀 开始API调用测试...
echo.

"%PYTHON_EXECUTABLE%" test_project_env_api.py

echo.
echo =====================================
echo 测试完成
echo =====================================

pause