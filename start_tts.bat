@echo off
chcp 65001
echo Starting DMOSpeech2 TTS Service (OpenAI API only)...
cd /d "%~dp0DMOSpeech2"
call "启动OpenAI接口服务.bat"