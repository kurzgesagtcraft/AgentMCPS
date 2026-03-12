# TTS API 接口格式规范说明文档 (V1.0)

## 1. 概述
本规范旨在为 AgentV 项目中的语音合成（TTS）服务提供统一的接口标准。通过标准化请求参数和响应格式，确保不同 TTS 引擎（如 GPT-SoVITS, Edge-TTS 等）能够无缝集成到系统中。

## 2. 基础信息
- **协议**: HTTP/1.1
- **数据格式**: JSON (Request Body), Binary Audio (Response)
- **字符编码**: UTF-8

## 3. 核心接口规范

### 3.1 语音合成接口 (OpenAI 兼容模式)
该接口参考 OpenAI 的 `/v1/audio/speech` 标准，建议作为首选集成方式。

- **路径**: `/v1/audio/speech`
- **方法**: `POST`
- **请求头**: `Content-Type: application/json`

#### 请求参数 (JSON)
| 参数名 | 类型 | 必选 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `model` | String | 是 | 使用的模型 ID 或版本号 | `gpt-sovits-v2` |
| `input` | String | 是 | 需要合成的文本内容 | `你好，我是你的 AI 助手。` |
| `voice` | String | 是 | 说话人名称/角色 ID | `Nova` |
| `response_format` | String | 否 | 音频格式 (mp3, wav, ogg, aac) | `wav` |
| `speed` | Float | 否 | 语速 (0.25 - 4.0)，默认为 1.0 | `1.0` |

#### 扩展参数 (`extra_params`)
针对 GPT-SoVITS 等复杂引擎，可在请求体中添加扩展字段：
| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `emotion` | String | 情感标签 | `happy`, `sad`, `随机` |
| `text_lang` | String | 合成文本语言 | `zh`, `en`, `ja`, `auto` |
| `prompt_lang` | String | 参考音频语言 | `zh`, `en`, `ja` |
| `seed` | Integer | 随机种子 (-1 为随机) | `42` |
| `top_k` | Integer | 采样参数 Top K | `5` |
| `top_p` | Float | 采样参数 Top P | `0.8` |
| `temperature` | Float | 采样温度 | `1.0` |

#### 响应
- **成功**: 返回音频二进制流，`Content-Type` 根据格式设为 `audio/mpeg`, `audio/wav` 等。
- **失败**: 返回 JSON 格式错误信息。
```json
{
  "error": {
    "message": "说话人不存在",
    "type": "invalid_request_error",
    "code": "voice_not_found"
  }
}
```

### 3.2 模型列表获取接口
用于前端获取当前可用的说话人和情感列表。

- **路径**: `/api/models`
- **方法**: `GET` 或 `POST`

#### 响应格式 (JSON)
```json
{
  "status": "success",
  "models": {
    "SpeakerName": {
      "zh": ["happy", "sad", "angry"],
      "en": ["default"]
    }
  }
}
```

## 4. 错误码定义
| 状态码 | 错误类型 | 说明 |
| :--- | :--- | :--- |
| 400 | parameter_error | 请求参数缺失或格式错误 |
| 401 | authentication_error | API Key 验证失败 |
| 404 | resource_not_found | 模型或说话人不存在 |
| 500 | processing_error | 引擎内部合成失败 |

## 5. 最佳实践
1. **流式输出**: 对于长文本，建议 TTS 服务端支持流式音频返回以降低首字延迟。
2. **缓存机制**: 建议对相同文本和参数的合成结果进行 MD5 缓存。
3. **超时控制**: 客户端应设置合理的超时时间（建议 15s 以上）。