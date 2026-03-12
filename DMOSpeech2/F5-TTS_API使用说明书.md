# F5-TTS API调用格式说明书

## 概述

F5-TTS服务已成功部署并运行在本地端口80，提供语音合成功能。服务基于Gradio框架构建，支持通过参考音频和文本生成高质量的合成语音。

## 服务信息

- **服务地址**: http://localhost:80 或 http://0.0.0.0:80
- **服务状态**: ✅ 正常运行
- **框架**: Gradio + FastAPI
- **模型**: F5-TTS v1 Base

## API端点

### 主要端点

1. **TTS合成端点**: `/do_job`
2. **配置信息**: `/config`
3. **网页界面**: `/` (根路径)

## 调用方式

### 方式一：Gradio Client (推荐)

```python
from gradio_client import Client

# 连接到服务
client = Client("http://localhost:80")

# 调用TTS合成
result = client.predict(
    "这是要生成的文本内容",        # gen_text: 目标文本
    "reference.wav",              # prompt_audio: 参考音频文件
    "这是参考音频的文本内容",      # ref_text: 参考文本
    api_name="/do_job"            # API端点名称
)

print(f"生成的音频文件路径: {result}")
```

### 方式二：网页界面

1. 打开浏览器访问: http://localhost:80
2. 在界面中输入：
   - **输入需要生成的文本**: 您要合成的目标文本
   - **参考音频**: 上传音频文件或从列表中选择
   - **参考音频文本**: 参考音频对应的文本内容
3. 点击"开始生成"按钮
4. 等待处理完成，下载生成的音频

## 参数说明

| 参数名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| gen_text | string | 要生成语音的目标文本 | "这是一个TTS测试合成示例" |
| prompt_audio | file/string | 参考音频文件路径 | "reference.wav" |
| ref_text | string | 参考音频对应的文本内容 | "这是参考音频的文本内容" |

## 响应格式

### 成功响应
- **类型**: 文件路径 (string)
- **内容**: 生成的WAV音频文件的本地路径
- **示例**: `"/tmp/gradio/xxx/audio.wav"`

### 处理时间
- **典型处理时间**: 2-10秒 (取决于文本长度和模型负载)
- **支持的音频格式**: WAV (16kHz, 单声道)

## 完整示例代码

### Python脚本示例

```python
#!/usr/bin/env python3
import os
import shutil
from gradio_client import Client

def synthesize_speech(target_text, reference_audio, reference_text):
    """
    使用F5-TTS进行语音合成
    
    Args:
        target_text: 要合成的目标文本
        reference_audio: 参考音频文件路径  
        reference_text: 参考音频的文本内容
        
    Returns:
        生成的音频文件路径
    """
    try:
        # 连接到TTS服务
        client = Client("http://localhost:80")
        
        # 调用合成API
        result = client.predict(
            target_text,
            reference_audio,
            reference_text,
            api_name="/do_job"
        )
        
        # 复制到当前目录
        if result and os.path.exists(result):
            output_file = f"synthesized_{int(time.time())}.wav"
            shutil.copy2(result, output_file)
            return output_file
        else:
            raise Exception("未获得有效的音频文件")
            
    except Exception as e:
        print(f"语音合成失败: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    audio_file = synthesize_speech(
        target_text="你好，欢迎使用F5-TTS语音合成服务！",
        reference_audio="reference.wav",
        reference_text="这是参考音频的文本"
    )
    
    if audio_file:
        print(f"✅ 合成成功: {audio_file}")
    else:
        print("❌ 合成失败")
```

### 批量处理示例

```python
def batch_synthesize(text_list, reference_audio, reference_text):
    """批量语音合成"""
    client = Client("http://localhost:80")
    results = []
    
    for i, text in enumerate(text_list):
        try:
            result = client.predict(
                text,
                reference_audio, 
                reference_text,
                api_name="/do_job"
            )
            
            if result:
                output_file = f"batch_{i+1:03d}.wav"
                shutil.copy2(result, output_file)
                results.append(output_file)
                print(f"✅ 第{i+1}个文本合成完成: {output_file}")
            else:
                print(f"❌ 第{i+1}个文本合成失败")
                
        except Exception as e:
            print(f"❌ 第{i+1}个文本处理异常: {e}")
    
    return results

# 使用示例
texts = [
    "欢迎使用语音合成服务",
    "这是第二段测试文本",
    "批量处理功能正常工作"
]

batch_results = batch_synthesize(texts, "reference.wav", "参考文本")
print(f"批量处理完成，共生成 {len(batch_results)} 个音频文件")
```

## 错误处理

### 常见错误及解决方案

1. **连接失败**
   ```
   Could not fetch config for http://localhost:80/
   ```
   - **原因**: 服务未启动或端口占用
   - **解决**: 确保TTS服务正常运行

2. **文件不存在**
   ```
   FileNotFoundError: reference.wav
   ```
   - **原因**: 参考音频文件路径错误
   - **解决**: 检查文件路径和文件是否存在

3. **处理超时**
   - **原因**: 文本过长或服务负载过高
   - **解决**: 缩短文本长度或等待服务负载降低

### 最佳实践

1. **音频质量优化**
   - 使用高质量的参考音频 (清晰、无噪音)
   - 参考文本应与参考音频内容完全匹配
   - 控制目标文本长度 (建议单次不超过100字)

2. **性能优化**
   - 复用Client连接以提高效率
   - 避免并发过多请求
   - 适当的超时设置

3. **错误处理**
   - 添加重试机制
   - 验证输入参数
   - 监控服务状态

## 服务管理

### 启动服务
```bash
# 使用提供的批处理文件
运行_自动开启接口服务.bat

# 或直接运行Python应用
python app.py
```

### 查看服务状态
```bash
# 检查服务是否响应
curl http://localhost:80/config

# 查看网页界面
curl http://localhost:80
```

### 服务配置
- **端口**: 80
- **最大并发**: 4
- **超时**: 300秒
- **队列**: 启用

## 版本信息

- **F5-TTS**: v1 Base
- **Gradio**: 4.44.1
- **Python**: 3.12
- **更新日期**: 2025-08-23

## 支持与联系

如遇到技术问题，请检查：
1. 服务运行状态
2. 音频文件格式和质量
3. 网络连接
4. 依赖库版本兼容性

---

**注意**: 此API服务目前运行在本地环境，如需公网访问，可使用cloudflared等隧道工具。