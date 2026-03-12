# MobileAgent MCP 架构设计

## 1. 概述
将 MobileAgent-v3 的多智能体协作逻辑封装为 MCP (Model Context Protocol) 服务，使其能够作为工具被其他 LLM 调用，实现移动端自动化。

## 2. 核心组件映射
- **State Management**: 使用 `InfoPool` 类维护任务状态、计划、历史记录和笔记。
- **Agents**: 封装 `Manager`, `Executor`, `ActionReflector`, `Notetaker` 为内部逻辑。
- **Controller**: 封装 `AndroidController` (ADB) 和 `HarmonyOSController` (HDC)。
- **VLLM**: 封装 `GUIOwlWrapper` 或支持 OpenAI 兼容接口的 MLLM。

## 3. MCP 工具定义 (Tools)

### `initialize_task`
- **描述**: 初始化一个新的移动端任务。
- **参数**:
    - `instruction` (string): 用户指令。
    - `device_type` (string): "android" 或 "harmonyos"。
    - `adb_path` / `hdc_path` (string): 设备连接路径。
    - `api_key` (string): MLLM API 密钥。
    - `base_url` (string): MLLM API 基础 URL。
    - `model` (string): 使用的模型名称。
- **返回**: 任务 ID 和初始状态。

### `execute_step`
- **描述**: 执行任务的一个单步循环（规划 -> 执行 -> 反思 -> 记录）。
- **参数**:
    - `task_id` (string): 任务 ID。
- **返回**: 当前步骤的 Thought, Action, Outcome, 以及最新的截图路径。

### `get_task_status`
- **描述**: 获取任务的当前状态。
- **参数**:
    - `task_id` (string): 任务 ID。
- **返回**: `InfoPool` 中的完整信息（计划、历史、笔记等）。

### `stop_task`
- **描述**: 停止并清理任务资源。
- **参数**:
    - `task_id` (string): 任务 ID。

## 4. 资源定义 (Resources)
- `mobile_agent://{task_id}/screenshot`: 当前设备的实时截图。
- `mobile_agent://{task_id}/history`: 任务执行历史日志。

## 5. 实现计划
1. **环境准备**: 创建 Python 虚拟环境，安装依赖（PIL, requests, mcp）。
2. **代码迁移**: 将 `mobile_v3/utils` 中的核心类迁移并适配。
3. **MCP 封装**: 使用 `mcp` Python SDK 编写服务器。
4. **注册测试**: 在 `mcp_settings.json` 中注册并进行真机或模拟器测试。