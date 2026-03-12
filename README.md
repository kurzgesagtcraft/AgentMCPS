AgentMCPS

AgentMCPS 是一个高度模块化、插件驱动的 **AI 中间层协议栈**，旨在为 AI Agent 提供强大的长短期记忆、自定义语音（TTS）、自动化计算机操作以及多模态交互能力。

## 🌟 核心特性

- **🧠 深度记忆系统 (RAG V2)**：
  - 基于 SQLite 和 Rust 编写的高性能向量检索引擎 (`rust-vexus-lite`)。
  - 支持长短期记忆自动同步与元思考链（Meta-Thinking Chains）。
  - 完美支持本地 Ollama 嵌入模型（如 `nomic-embed-text`）。

- **🎙️ 自定义语音交互 (TTS)**：
  - 集成 TTS 服务，支持参考音频克隆。
  - 针对不同 Agent 角色可配置专属音色。

- **🤖 自动化与计算机使用 (Computer Use)**：
  - 通过 Chrome 控制插件实现网页自动化。
  - 支持文件操作、系统监控及多种第三方工具集成。

- **🔌 强大的插件系统**：
  - 涵盖搜索（Tavily）、图像生成（Flux, NovelAI, SD）、视频生成（Wan2.1）、Bilibili 内容获取等。
  - 采用 VCP (Variable & Command Protocol) 自定义指令协议。

- **🛠️ MCP 集成**：
  - 深度集成 Model Context Protocol，扩展 AI 的工具边界。

- **🖥️ 可视化管理面板**：
  - 提供 Web 端 Admin Panel，实时调控 RAG 参数、编辑工具配置及监控日志。

## 🏗️ 项目架构

- **Core**: `server.js` 驱动，`Plugin.js` 负责插件加载。
- **Memory**: `KnowledgeBaseManager.js` 管理向量数据库与 SQLite。
- **Frontend**: `AdminPanel/` 提供管理界面。
- **Agents**: `Agent/` 目录下定义不同 AI 角色的性格与能力。

## 🚀 快速开始

### 1. 环境准备
- 安装 [Node.js](https://nodejs.org/) (建议 v18+)。
- 安装 [Python 3.10+](https://www.python.org/)。
- 安装 [Ollama](https://ollama.com/) 并拉取嵌入模型：
  ```bash
  ollama pull nomic-embed-text:latest
  ```

### 2. 安装步骤
1. **安装大文件**：将 LFP 文件夹放入根目录，运行 `LFP/copy.bat`。
2. **安装依赖**：
   ```bash
   npm install
   pip install -r requirements.txt
   ```
3. **VSCode 插件**：安装 `Kilo Code` 插件，并运行 `MCP\安装了kilocode后点我安装MCP.bat`。

### 3. 配置
复制 `config.env.example` 为 `config.env`，并填写以下核心配置：
- `API_Key` & `API_URL`: 你的 AI 服务商凭证。
- `EMBEDDING_API_URL`: 通常为 `http://localhost:11434` (Ollama)。
- `AdminUsername` & `AdminPassword`: 管理面板登录凭证。

### 4. 启动服务
- **启动核心服务**：运行 `start_server.bat`。
- **启动语音服务**：运行 `start_tts.bat`。
- **启动前端面板**：运行 `start_frontend.bat`。

## 📂 目录结构说明

- `/Agent`: 存放 Agent 角色定义文件（.txt）。
- `/dailynote`: 存放 RAG 原始文档与日记。
- `/VectorStore`: 存放向量索引与数据库。
- `/Plugin`: 丰富的扩展插件库。
- `/DMOSpeech2`: TTS 核心组件与参考音频。
- `/AdminPanel`: Web 管理后台源码。

## 📝 使用说明

- **新建 Agent**: 参考 `Agent/kilocode.txt` 格式创建新文件。
- **语音克隆**: 将参考音频放入 `DMOSpeech2\refaudio`，文件名即为音频对应的文本内容。
- **记忆管理**: 所有的对话和知识会自动向量化存入 `VectorStore`，可通过管理面板进行微调。

