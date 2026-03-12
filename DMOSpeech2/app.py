import os
import sys

# 确保当前目录在 sys.path 中，以便导入本地模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 强制清除可能干扰 Gradio/FastAPI 的代理设置
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["no_proxy"] = "localhost,127.0.0.1"

import threading
import gradio as gr
import uvicorn

# 强制设置 Gradio 环境变量
os.environ["GRADIO_SHARE"] = "True"
os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"

# 增强型 Monkeypatch Gradio launch
# 处理可能的参数冲突，确保 share 始终为 True
original_launch = gr.Blocks.launch
def patched_launch(self, *args, **kwargs):
    new_args = list(args)
    # launch(self, inline, inbrowser, share, ...)
    # 如果 share 作为位置参数传递（索引为 2）
    if len(new_args) > 2:
        new_args[2] = True
    else:
        kwargs['share'] = True
    
    kwargs['server_name'] = '0.0.0.0'
    # 移除可能冲突的参数
    if 'server_port' in kwargs and kwargs['server_port'] is None:
        kwargs.pop('server_port')
        
    return original_launch(self, *tuple(new_args), **kwargs)

gr.Blocks.launch = patched_launch

# 延迟导入，确保 sys.path 已更新
from cy_app import *
from openai_api import app as openai_app

def run_openai_api():
    """启动兼容 OpenAI 规范的 FastAPI 服务"""
    # 显式指定端口 8000，确保与插件配置一致
    uvicorn.run(openai_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # 启动 FastAPI 服务 (端口 8000)
    # 使用 openai_api.py 中定义的 app 确保接口符合 AgentV 规范
    fastapi_thread = threading.Thread(target=run_openai_api, daemon=True)
    
    # 启动 Gradio 界面。
    # 注意：在某些受限网络环境下，share=True 是必须的，已通过 Monkeypatch 强制开启
    gradio_thread = threading.Thread(target=start_gradio, args=(True,), daemon=True)

    print("[DMOSpeech2] Starting FastAPI service on port 8000...")
    fastapi_thread.start()
    
    print("[DMOSpeech2] Starting Gradio interface...")
    gradio_thread.start()

    # 保持主线程运行
    try:
        fastapi_thread.join()
        gradio_thread.join()
    except KeyboardInterrupt:
        print("[DMOSpeech2] Stopping services...")