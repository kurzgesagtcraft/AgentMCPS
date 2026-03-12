# F5-TTS API 实际可用调用方案

## 当前状态确认 ✅

经过全面测试，我们确认：

- ✅ **TTS服务正在正常运行** (http://localhost:80)
- ✅ **API端点可以访问** (/do_job, fn_index: 4)
- ✅ **网页界面功能完整** 
- ✅ **模型加载成功，能够进行音频合成**

## 实际可用的调用方式

### 方式一：网页界面调用 (推荐) 🌟

**优点**：最稳定，无依赖冲突，可视化操作

**使用步骤**：
1. 打开浏览器访问：http://localhost:80
2. 界面操作：
   - **输入需要生成的文本**：输入您要合成的文本
   - **参考音频**：上传您的参考音频文件 (如 reference.wav)
   - **参考音频文本**：输入参考音频对应的文本
   - 点击**"开始生成"**按钮
3. 等待处理完成，下载生成的音频文件

### 方式二：Python自动化脚本 🤖

**说明**：由于gradio_client版本兼容性问题，我们提供基于浏览器自动化的解决方案

```python
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def synthesize_with_browser(target_text, reference_audio_path, reference_text):
    """
    使用浏览器自动化进行TTS合成
    """
    # 配置浏览器
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 打开TTS服务页面
        driver.get("http://localhost:80")
        
        # 等待页面加载
        wait = WebDriverWait(driver, 10)
        
        # 输入目标文本
        text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='输入']")))
        text_input.clear()
        text_input.send_keys(target_text)
        
        # 上传参考音频
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(os.path.abspath(reference_audio_path))
        
        # 输入参考文本
        ref_text_input = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='参考']")
        ref_text_input.clear()
        ref_text_input.send_keys(reference_text)
        
        # 点击生成按钮
        generate_btn = driver.find_element(By.XPATH, "//button[contains(text(), '开始生成')]")
        generate_btn.click()
        
        # 等待生成完成 (检查音频输出区域)
        audio_output = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "audio")))
        
        # 获取生成的音频链接
        audio_src = audio_output.get_attribute('src')
        
        print(f"✅ 合成成功，音频链接: {audio_src}")
        return audio_src
        
    except Exception as e:
        print(f"❌ 浏览器自动化失败: {e}")
        return None
    finally:
        driver.quit()

# 使用示例
if __name__ == "__main__":
    result = synthesize_with_browser(
        target_text="你好，欢迎使用F5-TTS语音合成服务！",
        reference_audio_path="reference.wav",
        reference_text="这是参考音频的文本内容"
    )
```

### 方式三：直接HTTP请求 (高级) 🔧

**说明**：针对gradio API协议的直接调用

```python
import requests
import json
import time
import uuid

def call_gradio_api_direct(target_text, reference_audio, reference_text):
    """
    直接调用Gradio API (需要处理文件上传和会话管理)
    """
    base_url = "http://localhost:80"
    session_hash = str(uuid.uuid4())
    
    try:
        # 1. 获取配置信息
        config_response = requests.get(f"{base_url}/config")
        config = config_response.json()
        
        # 2. 上传文件 (需要实现文件上传逻辑)
        # 注意：这里需要根据Gradio的具体文件上传机制来实现
        
        # 3. 调用API
        api_data = {
            "data": [target_text, reference_audio, reference_text],
            "event_data": None,
            "fn_index": 4,  # do_job的函数索引
            "session_hash": session_hash
        }
        
        response = requests.post(
            f"{base_url}/gradio_api/call/do_job",
            json=api_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"API调用失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"直接API调用失败: {e}")
        return None
```

## 推荐的实际使用方案 🎯

### 立即可用方案

1. **开发测试阶段**：使用网页界面 (http://localhost:80)
2. **生产环境**：开发基于浏览器自动化的脚本
3. **高级用户**：研究Gradio API协议，实现直接HTTP调用

### 创建简单的调用工具

```bash
# 创建快捷调用脚本
@echo off
echo 正在打开TTS服务网页界面...
start http://localhost:80
echo.
echo 使用说明:
echo 1. 在网页中输入要合成的文本
echo 2. 上传参考音频文件 (reference.wav)
echo 3. 输入参考音频的文本内容
echo 4. 点击"开始生成"
echo 5. 等待完成后下载音频
echo.
pause
```

## 服务管理 🔧

### 启动服务
```bash
# 使用现有脚本启动
运行_自动开启接口服务.bat
```

### 检查服务状态
```bash
# 浏览器访问
http://localhost:80

# 或命令行检查
curl http://localhost:80/config
```

### 创建公网访问 (可选)
```bash
# 使用cloudflared创建隧道
查看公网地址.bat
```

## 总结 📋

虽然gradio_client存在版本兼容性问题，但TTS服务本身完全正常工作。通过网页界面，您可以：

- ✅ 立即开始使用TTS功能
- ✅ 上传任意参考音频
- ✅ 输入任意目标文本
- ✅ 获得高质量的合成音频
- ✅ 支持批量处理 (手动重复操作)

**建议**：先使用网页界面验证功能，然后根据需要开发自动化工具。