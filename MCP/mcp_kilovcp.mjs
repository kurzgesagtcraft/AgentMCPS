/**
 * mcp_kilovcp.mjs
 * Kilo Code Agent MCP Server for VCPToolbox Integration
 */

console.error("[MCP] Starting mcp_kilovcp.mjs...");

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";
import apiConfig from "../modules/apiConfig.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 加载 VCP 环境配置
const envPath = path.join(__dirname, 'config.env');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

const PORT = (process.env.PORT || "6005").trim();
const SERVER_KEY = apiConfig.memory.vcpServerKey;
const ADMIN_USERNAME = (process.env.AdminUsername || "kurz");
const ADMIN_PASSWORD = (process.env.AdminPassword || "kurz");
const API_BASE_URL = apiConfig.memory.vcpApiBaseUrl;

const server = new Server(
  {
    name: "kilovcp-agent",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

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

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query_kilo_memory",
        description: "检索 Kilo Code 的过往记忆。在任务开始时使用，通过 [[kilocode日记本]] 触发 RAG 检索。",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "检索关键词" },
          },
          required: ["query"],
        },
      },
      {
        name: "store_kilo_reflection",
        description: "存储任务反思。在任务结束时将经验固化为长期记忆。",
        inputSchema: {
          type: "object",
          properties: {
            content: { type: "string", description: "反思内容" },
            tags: { type: "string", description: "标签" }
          },
          required: ["content"],
        },
      }
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    switch (name) {
      case "query_kilo_memory": {
        const result = await callVCP("/v1/chatvcp/completions", {
          model: apiConfig.memory.model,
          messages: [
            { role: "system", content: "你现在是 Kilo Code 的记忆检索核心。请直接根据检索到的记忆回答，不要废话。必须包含 [[kilocode日记本]] 标签。" },
            { role: "user", content: `${args.query} [[kilocode日记本]]` }
          ],
          stream: false,
          max_tokens: 1000,
          temperature: 0.3
        });

        if (result.status === "error") {
          return {
            content: [{ type: "text", text: `Error: ${result.message}` }],
            isError: true
          };
        }
  
        let text = "";
        if (result.choices?.[0]?.message?.content) {
          text = result.choices[0].message.content;
        } else {
          text = JSON.stringify(result);
        }
  
        return {
          content: [{ type: "text", text }],
        };
      }

    case "store_kilo_reflection": {
      const payload = {
        maidName: "kilocode",
        dateString: new Date().toISOString().split('T')[0],
        contentText: `### 任务反思与进化记录\n\n${args.content}\n\nTag: ${args.tags || 'reflection'}`
      };

      const result = await callVCP("/admin_api/write-diary", payload);
      return {
        content: [{ type: "text", text: `结果: ${result.status || 'success'}. ${result.message || ''}` }],
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
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});