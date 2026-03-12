@echo off
chcp 65001 >nul
title F5-TTS API调用测试 - 项目Python环境

echo =====================================
echo F5-TTS API调用测试
echo =====================================
echo.

echo 正在使用项目内置Python环境...
echo.

rem 设置项目Python环境变量
set PYTHON_PATH=%cd%\py312
set PYTHONHOME=
set PYTHONPATH=
set PYTHONEXECUTABLE=%PYTHON_PATH%\python.exe
set PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%
set PYTHONIOENCODING=utf-8

rem 创建临时测试脚本
echo # -*- coding: utf-8 -*- > temp_api_test.py
echo import os >> temp_api_test.py
echo import sys >> temp_api_test.py
echo import time >> temp_api_test.py
echo import shutil >> temp_api_test.py
echo. >> temp_api_test.py
echo def test_api(): >> temp_api_test.py
echo     try: >> temp_api_test.py
echo         from gradio_client import Client >> temp_api_test.py
echo         print("连接到TTS服务...") >> temp_api_test.py
echo         client = Client("http://localhost:80") >> temp_api_test.py
echo         print("开始TTS合成...") >> temp_api_test.py
echo         result = client.predict( >> temp_api_test.py
echo             "你好，欢迎使用F5-TTS语音合成服务！", >> temp_api_test.py
echo             "reference.wav", >> temp_api_test.py
echo             "这是参考音频的文本内容", >> temp_api_test.py
echo             api_name="/do_job" >> temp_api_test.py
echo         ^) >> temp_api_test.py
echo         print(f"返回结果: {result}") >> temp_api_test.py
echo         if result and os.path.exists(result): >> temp_api_test.py
echo             timestamp = int(time.time()) >> temp_api_test.py
echo             output_file = f"api_success_{timestamp}.wav" >> temp_api_test.py
echo             shutil.copy2(result, output_file) >> temp_api_test.py
echo             file_size = os.path.getsize(output_file) >> temp_api_test.py
echo             print(f"合成成功: {output_file} ({file_size} bytes)") >> temp_api_test.py
echo             return True >> temp_api_test.py
echo         else: >> temp_api_test.py
echo             print("未获得音频文件") >> temp_api_test.py
echo             return False >> temp_api_test.py
echo     except Exception as e: >> temp_api_test.py
echo         print(f"API调用失败: {e}") >> temp_api_test.py
echo         return False >> temp_api_test.py
echo. >> temp_api_test.py
echo if __name__ == "__main__": >> temp_api_test.py
echo     success = test_api() >> temp_api_test.py
echo     print(f"测试结果: {'成功' if success else '失败'}") >> temp_api_test.py

echo 运行API调用测试...
echo.

"%PYTHONEXECUTABLE%" temp_api_test.py

echo.
echo =====================================
echo 测试完成
echo =====================================

rem 清理临时文件
if exist temp_api_test.py del temp_api_test.py

pause