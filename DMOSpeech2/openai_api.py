import os
import sys

# 设置环境变量，与 运行_自动开启接口服务.bat 保持一致
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GRADIO_TEMP_DIR"] = os.path.join(current_dir, "tmp")
os.environ["DS_BUILD_AIO"] = "0"
os.environ["DS_BUILD_SPARSE_ATTN"] = "0"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# os.environ["HF_HOME"] = os.path.join(current_dir, "hf_download")
# os.environ["TRANSFORMERS_CACHE"] = os.path.join(current_dir, "tf_download")
os.environ["XFORMERS_FORCE_DISABLE_TRITON"] = "1"

# 设置 FFMPEG 路径
ffmpeg_path = os.path.join(current_dir, "py312", "ffmpeg", "bin")
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

import torch
import torchaudio
import numpy as np
import io
import soundfile as sf
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Add current directory to sys.path
sys.path.append(current_dir)

from f5_tts.api import F5TTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="F5-TTS OpenAI Compatible API")

# Global model instance
f5tts = None

# Reference audio directory
REFAUDIO_DIR = os.path.join(current_dir, "refaudio")

class SpeechRequest(BaseModel):
    model: str = "f5-tts"
    input: str
    voice: str = "default"
    response_format: str = "wav"
    speed: float = 1.0
    extra_params: Optional[Dict[str, Any]] = None

def get_ref_audio_and_text(voice_name: str):
    """
    Find reference audio in refaudio directory and its corresponding text.
    If voice_name is 'default', it picks the first wav file.
    If voice_name matches a filename (without extension), it uses that.
    """
    if not os.path.exists(REFAUDIO_DIR):
        os.makedirs(REFAUDIO_DIR)
        return None, None

    audio_extensions = (".wav", ".mp3", ".flac", ".ogg")
    audio_files = [f for f in os.listdir(REFAUDIO_DIR) if f.lower().endswith(audio_extensions)]
    if not audio_files:
        return None, None

    target_wav = None
    if voice_name == "default" or not voice_name:
        target_wav = audio_files[0]
    else:
        # Try to find exact match
        for f in audio_files:
            if os.path.splitext(f)[0] == voice_name:
                target_wav = f
                break
        if not target_wav:
            target_wav = audio_files[0] # Fallback

    ref_audio_path = os.path.join(REFAUDIO_DIR, target_wav)
    
    # The requirement says: "使用获取参考音频文件名自动获取参考文本方式"
    # This usually means the filename itself is the text, or there's a .txt file with the same name.
    # Let's check for .txt first, then fallback to filename.
    ref_text_path = os.path.splitext(ref_audio_path)[0] + ".txt"
    if os.path.exists(ref_text_path):
        with open(ref_text_path, "r", encoding="utf-8") as f:
            ref_text = f.read().strip()
    else:
        # Use filename as text (removing extension)
        ref_text = os.path.splitext(target_wav)[0]

    return ref_audio_path, ref_text

@app.on_event("startup")
async def startup_event():
    global f5tts
    logger.info("Loading F5-TTS model...")
    # Initialize with default settings
    f5tts = F5TTS(model="F5TTS_v1_Base")
    logger.info("Model loaded successfully.")

@app.post("/v1/audio/speech")
async def text_to_speech(request: SpeechRequest):
    if not f5tts:
        raise HTTPException(status_code=500, detail="Model not initialized")

    ref_audio, ref_text = get_ref_audio_and_text(request.voice)
    if not ref_audio:
        raise HTTPException(status_code=404, detail=f"No reference audio found in {REFAUDIO_DIR}")

    logger.info(f"Synthesizing with voice: {request.voice}, ref_audio: {ref_audio}, ref_text: {ref_text}")

    try:
        # Extract extra params if any
        seed = None
        if request.extra_params:
            seed = request.extra_params.get("seed")

        # 打印合成信息以便调试
        logger.info(f"Input text: {request.input}")
        logger.info(f"Reference text: {ref_text}")
        
        # 确保文本不为空且格式正确
        gen_text = request.input.strip()
        if not gen_text:
            raise HTTPException(status_code=400, detail="Input text cannot be empty")

        wav, sr, _ = f5tts.infer(
            ref_file=ref_audio,
            ref_text=ref_text,
            gen_text=gen_text,
            speed=request.speed,
            seed=seed,
            remove_silence=True,
            nfe_step=32,      # 强制使用 32 步以保证质量
            cfg_strength=2.0  # 默认 CFG 强度
        )

        # Convert to requested format
        buffer = io.BytesIO()
        sf.write(buffer, wav, sr, format=request.response_format.upper() if request.response_format != "mp3" else "WAV")
        
        # Note: soundfile doesn't support mp3 writing directly in many envs without extra libs.
        # If mp3 is requested and not supported, we might need pydub or just return wav.
        # For now, let's assume wav/ogg/flac which soundfile handles well.
        
        buffer.seek(0)
        
        media_type = f"audio/{request.response_format}"
        if request.response_format == "wav":
            media_type = "audio/wav"
        elif request.response_format == "mp3":
            media_type = "audio/mpeg"

        return StreamingResponse(buffer, media_type=media_type)

    except Exception as e:
        logger.error(f"Synthesis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
@app.post("/api/models")
async def list_models():
    # Return available voices based on refaudio directory
    if not os.path.exists(REFAUDIO_DIR):
        return {"status": "success", "models": {}}
    
    audio_extensions = (".wav", ".mp3", ".flac", ".ogg")
    voices = [os.path.splitext(f)[0] for f in os.listdir(REFAUDIO_DIR) if f.lower().endswith(audio_extensions)]
    models_dict = {}
    for v in voices:
        # 按照 AgentV 规范返回说话人及其支持的情感/语言列表
        models_dict[v] = {
            "zh": ["default"],
            "en": ["default"]
        }
        
    return {
        "status": "success",
        "models": models_dict
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)