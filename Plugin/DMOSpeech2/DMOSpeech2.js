const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

let pluginConfig = null;
let webSocketServer = null;
let projectBasePath = null;

/**
 * 初始化插件
 */
async function initialize(config, dependencies) {
    pluginConfig = config;
    projectBasePath = config.PROJECT_BASE_PATH;
    if (config.DebugMode) {
        console.log('[DMOSpeech2] Initialized with config:', config);
    }
}

/**
 * 注册 API 路由 (hybridservice 必需)
 */
function registerApiRoutes(router, config, basePath, wss) {
    webSocketServer = wss;
    // 这里可以添加插件专属的 HTTP 端点，目前不需要
}

/**
 * 处理工具调用
 */
async function processToolCall(args) {
    const { text, voice = 'default', speed = 1.0, emotion = 'default', text_lang = 'auto' } = args;

    if (!text) {
        throw new Error('Parameter "text" is required.');
    }

    const apiUrl = pluginConfig.DMOSpeech2_ApiUrl || 'http://127.0.0.1:8000/v1/audio/speech';
    const outputMode = pluginConfig.DMOSpeech2_OutputMode || 'file';

    if (pluginConfig.DebugMode) {
        console.log(`[DMOSpeech2] Synthesizing: "${text}" with voice: ${voice}, speed: ${speed}, emotion: ${emotion}`);
    }

    try {
        const response = await axios.post(apiUrl, {
            input: text,
            voice: voice,
            speed: speed,
            response_format: 'wav',
            extra_params: {
                emotion: emotion,
                text_lang: text_lang
            }
        }, {
            responseType: 'arraybuffer'
        });

        const audioBuffer = Buffer.from(response.data);

        if (outputMode === 'file') {
            // 保存到文件系统
            const fileName = `speech_${crypto.createHash('md5').update(text + voice + speed).digest('hex')}.wav`;
            const publicDir = path.join(projectBasePath, 'file', 'speech');
            await fs.mkdir(publicDir, { recursive: true });
            const filePath = path.join(publicDir, fileName);
            await fs.writeFile(filePath, audioBuffer);

            // 构建可访问的 URL (假设 ImageServer 或类似插件提供静态文件服务)
            // 这里我们返回一个相对路径，由前端或中间层处理
            const relativeUrl = `/file/speech/${fileName}`;
            
            // 同时通过 WebSocket 广播播放指令 (如果支持)
            if (webSocketServer) {
                webSocketServer.broadcast({
                    type: 'play_audio',
                    data: {
                        url: relativeUrl,
                        text: text,
                        voice: voice
                    }
                });
            }

            return {
                status: 'success',
                message: '语音合成成功',
                audio_url: relativeUrl,
                text: text
            };
        } else {
            // 仅广播模式 (Base64)
            const base64Audio = audioBuffer.toString('base64');
            if (webSocketServer) {
                webSocketServer.broadcast({
                    type: 'play_audio_base64',
                    data: {
                        audio: base64Audio,
                        format: 'wav',
                        text: text
                    }
                });
            }

            return {
                status: 'success',
                message: '语音合成指令已广播',
                text: text
            };
        }

    } catch (error) {
        console.error('[DMOSpeech2] Synthesis failed:', error.message);
        throw new Error(`DMOSpeech2 API error: ${error.message}`);
    }
}

module.exports = {
    initialize,
    registerApiRoutes,
    processToolCall
};