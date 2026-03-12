/**
 * fei.mjs
 *  Agent MCP Server for VCPToolbox Integration
 * 提供记忆检索、存储和 TTS 语音播放功能
 */

console.error("[MCP] Starting fei.mjs -  Agent MCP Server...");

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import dotenv from "dotenv";
import path from "path";
import apiConfig from "../modules/apiConfig.js";
import { fileURLToPath } from "url";
import fs from "fs";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 加载 VCP 环境配置
const envPaths = [
  path.join(__dirname, 'config.env'),
  path.join(__dirname, '..', 'config.env')
];

for (const envPath of envPaths) {
  if (fs.existsSync(envPath)) {
    dotenv.config({ path: envPath });
    console.error(`[MCP] Loaded config from ${envPath}`);
  }
}

const PORT = (process.env.PORT || "6005").trim();
const SERVER_KEY = apiConfig.memory.vcpServerKey;
const ADMIN_USERNAME = (process.env.AdminUsername || "kurz");
const ADMIN_PASSWORD = (process.env.AdminPassword || "kurz");
const API_BASE_URL = apiConfig.memory.vcpApiBaseUrl;

// TTS 服务配置 - DMOSpeech2 OpenAI 兼容 API
const TTS_API_URL = process.env.TTS_API_URL || "http://127.0.0.1:8000";
const TTS_VOICE = process.env.TTS_VOICE || "saxifei";

const server = new Server(
  {
    name: "fei-agent",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * 调用 VCP API
 */
async function callVCP(endpoint, data) {
  try {
    const headers = {
      'Content-Type': 'application/json',
      'X-Forwarded-For': '127.0.0.1'
    };
    
    let config = { headers, timeout: 180000 };

    if (endpoint.startsWith('/admin_api')) {
      const authValue = `Basic ${Buffer.from(`${ADMIN_USERNAME}:${ADMIN_PASSWORD}`).toString('base64')}`;
      headers['Authorization'] = authValue;
      headers['Cookie'] = `admin_auth=${encodeURIComponent(authValue)}`;
    } else {
      headers['Authorization'] = `Bearer ${SERVER_KEY}`;
    }

    const response = await axios.post(`${API_BASE_URL}${endpoint}`, data, config);
    return response.data;
  } catch (error) {
    const errorData = error.response?.data;
    return {
      status: "error",
      message: errorData?.error || errorData?.message || error.message
    };
  }
}

/**
 * 调用 TTS 服务
 * 使用 DMOSpeech2 的 OpenAI 兼容 API
 */
async function callTTS(text, voice = TTS_VOICE) {
  try {
    const response = await axios.post(`${TTS_API_URL}/v1/audio/speech`, {
      model: "f5-tts",
      input: text,
      voice: voice,
      response_format: "wav",
      speed: 1.0
    }, {
      headers: {
        'Content-Type': 'application/json'
      },
      responseType: 'arraybuffer',
      timeout: 120000 // TTS 可能需要较长时间
    });

    // 保存音频文件到临时目录
    const tempDir = path.join(__dirname, '..', 'temp');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    
    const audioFileName = `fei_tts_${Date.now()}.wav`;
    const audioFilePath = path.join(tempDir, audioFileName);
    
    fs.writeFileSync(audioFilePath, response.data);
    
    // 自动播放音频 (Windows)
    try {
      // 使用 PowerShell 播放音频，无需等待播放完成
      const playCommand = `powershell -Command "(New-Object Media.SoundPlayer '${audioFilePath}').PlaySync()"`;
      execAsync(playCommand).catch(() => {
        // 忽略播放错误，不影响主流程
      });
    } catch (playError) {
      console.error("[TTS] 播放音频时出错:", playError.message);
    }
    
    return {
      status: "success",
      message: "TTS 语音已生成并播放",
      audioFile: audioFilePath,
      text: text
    };
  } catch (error) {
    console.error("[TTS] 调用 TTS 服务失败:", error.message);
    return {
      status: "error",
      message: `TTS 服务调用失败: ${error.message}`
    };
  }
}

/**
 * 检索角色记忆
 * 通过 VCP RAG 系统检索 dailynote/saxifei 中的记忆
 */
async function queryFeiMemory(query) {
  // 增加超时容错，VCP RAG 检索可能较慢
  const result = await callVCP("/v1/chatvcp/completions", {
    model: apiConfig.memory.model,
    messages: [
      { role: "system", content: "你现在是角色的记忆检索核心。请直接根据检索到的记忆回答，不要废话。必须包含 [[saxifei日记本]] 标签。" },
      { role: "user", content: `${query} [[saxifei日记本]]` }
    ],
    stream: false,
    max_tokens: 1000,
    temperature: 0.3
  });

  if (result.status === "error") {
    return {
      status: "error",
      message: result.message
    };
  }

  let text = "";
  if (result.choices?.[0]?.message?.content) {
    text = result.choices[0].message.content;
  } else {
    text = JSON.stringify(result);
  }

  return {
    status: "success",
    content: text
  };
}

/**
 * 存储角色记忆
 * 将记忆写入 dailynote/saxifei 目录
 */
async function storeFeiMemory(content, tags = "memory") {
  const payload = {
    maidName: "saxifei",
    dateString: new Date().toISOString().split('T')[0],
    contentText: `### 角色记忆记录\n\n${content}\n\nTag: ${tags}`
  };

  const result = await callVCP("/admin_api/write-diary", payload);
  return {
    status: result.status || "success",
    message: result.message || "记忆已存储"
  };
}

// 注册工具列表
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query_fei_memory",
        description: "检索角色的过往记忆。在任务开始时或需要回忆时使用，通过 [[saxifei日记本]] 触发 RAG 检索 dailynote/saxifei 目录中的记忆。",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "检索关键词或问题" },
          },
          required: ["query"],
        },
      },
      {
        name: "store_fei_memory",
        description: "存储角色的记忆。在对话结束、上下文压缩前或需要保存重要信息时使用，将记忆写入 dailynote/saxifei 目录。",
        inputSchema: {
          type: "object",
          properties: {
            content: { type: "string", description: "要存储的记忆内容" },
            tags: { type: "string", description: "标签，用于分类记忆" }
          },
          required: ["content"],
        },
      },
      {
        name: "tts",
        description: "使用 TTS 服务播放语音。将文本转换为角色的声音并播放。每一小段对话后可调用此方法播放语音回复。",
        inputSchema: {
          type: "object",
          properties: {
            text: { type: "string", description: "要转换为语音的文本内容" },
            voice: { type: "string", description: "声音名称，默认为 saxifei" }
          },
          required: ["text"],
        },
      }
    ],
  };
});

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    switch (name) {
      case "query_fei_memory": {
        const result = await queryFeiMemory(args.query);
        
        if (result.status === "error") {
          return {
            content: [{ type: "text", text: `检索记忆时出错: ${result.message}` }],
            isError: true
          };
        }
  
        return {
          content: [{ type: "text", text: result.content }],
        };
      }

      case "store_fei_memory": {
        const result = await storeFeiMemory(args.content, args.tags);
        return {
          content: [{ type: "text", text: `记忆存储结果: ${result.status}. ${result.message}` }],
        };
      }

      case "tts": {
        const result = await callTTS(args.text, args.voice);
        
        if (result.status === "error") {
          return {
            content: [{ type: "text", text: `TTS 调用失败: ${result.message}` }],
            isError: true
          };
        }
        
        return {
          content: [{ type: "text", text: `语音已生成: ${result.message}\n文本: ${result.text}\n音频文件: ${result.audioFile}` }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `MCP Internal Error: ${error.message}\n${error.stack}` }],
      isError: true
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[MCP] Agent MCP Server 已启动并连接");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});