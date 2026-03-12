/**
 * modules/apiConfig.js
 * VCP 统一 API 配置文件
 * 集中管理 LLM 聊天和嵌入服务的 API 密钥、基础 URL 和模型定义
 */

const dotenv = require('dotenv');
const path = require('path');

// 确保加载了环境变量
dotenv.config({ path: path.join(__dirname, '../config.env') });

const apiConfig = {
    // 核心聊天 API 配置
    chat: {
        apiKey: process.env.API_Key || '',
        apiUrl: process.env.API_URL || '',
        model: 'z-ai/glm5'
    },
    
    // 嵌入 (Embedding) API 配置
    embedding: {
        apiKey: process.env.EMBEDDING_API_KEY || process.env.API_Key || '',
        apiUrl: process.env.EMBEDDING_API_URL || process.env.API_URL || '',
        model: process.env.WhitelistEmbeddingModel || 'nomic-embed-text:latest',
        dimension: parseInt(process.env.VECTORDB_DIMENSION) || 768
    },

    // 记忆系统专用配置 (如 MCP Server 使用)
    memory: {
        model: process.env.MEMORY_MODEL || 'z-ai/glm5',
        // 内部调用 VCP 服务的配置
        vcpApiBaseUrl: `http://127.0.0.1:${process.env.PORT || '6005'}`,
        vcpServerKey: process.env.Key || 'vcp123456'
    }
};

module.exports = apiConfig;