# KiloVCP MCP 模型配置指南

本指南说明如何配置和修改 kilovcp MCP 服务器的 AI 模型设置。

## 修改的文件

### 1. `MCP/mcp_kilovcp.mjs`

这是 MCP 服务器的主文件，定义了 `query_kilo_memory` 和 `store_kilo_reflection` 两个工具。

#### 修改位置 1：模型名称配置 (第113行)

**原始代码：**
```javascript
const result = await callVCP("/v1/chatvcp/completions", {
  model: "gemini-3-flash-preview",
  messages: [
    { role: "system", content: "你现在是 Kilo Code 的记忆检索核心。你必须在回复中包含 [[kilocode日记本]] 标签来触发记忆检索。" },
    { role: "user", content: `${args.query} [[kilocode日记本]]` }
  ],
  stream: false
});
```

**修改后：**
```javascript
const result = await callVCP("/v1/chatvcp/completions", {
  model: "gemini-3-flash-preview",  // ⚠️ 需要与 config.env 中的配置匹配
  messages: [
    { role: "system", content: "你现在是 Kilo Code 的记忆检索核心。你必须在回复中包含 [[kilocode日记本]] 标签来触发记忆检索。" },
    { role: "user", content: `${args.query} [[kilocode日记本]]` }
  ],
  stream: false
});
```

**修改说明：**
- 模型名称必须与 VCP 服务器的 `config.env` 中配置的模型兼容
- 默认为 `gemini-3-flash-preview`，因为 VCP 使用 MiniMax API

#### 修改位置 2：错误处理改进 (第121-128行)

**修改后：**
```javascript
if (result.status === "error") {
  const errorMsg = typeof result.message === 'string' 
    ? result.message 
    : JSON.stringify(result.message || result);
  return {
    content: [{ type: "text", text: `[记忆检索失败] ${errorMsg}` }],
    isError: true
  };
}
```

**修改说明：**
- 改进错误消息序列化，避免 `[object Object]` 问题
- 支持多种错误格式

#### 修改位置 3：响应格式处理 (第131-153行)

**修改后：**
```javascript
// 尝试多种可能的响应格式
let text = "";

// 格式1: OpenAI 风格
if (result.choices?.[0]?.message?.content) {
  text = result.choices[0].message.content;
}
// 格式2: 直接 content 字段
else if (result.content) {
  text = result.content;
}
// 格式3: text 字段
else if (result.text) {
  text = result.text;
}
// 格式4: response 字段
else if (result.response) {
  text = typeof result.response === 'string' ? result.response : JSON.stringify(result.response);
}
// 格式5: 整个结果的字符串表示
else {
  text = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
}
```

**修改说明：**
- 支持多种 API 响应格式
- 增强兼容性

---

### 2. `Plugin/RAGDiaryPlugin/RAGDiaryPlugin.js`

这是 RAG 记忆检索插件，处理日记本内容的向量化和检索。

#### 修改位置：dbName 自动适配 (第1364-1373行)

**新增代码：**
```javascript
// 1️⃣ 处理 dbName 兼容性问题：自动添加"日记本"后缀
let effectiveDbName = dbName;
if (!this.ragConfig[dbName]) {
  // 如果原始名称不在配置中，尝试添加"日记本"后缀
  const withSuffix = dbName + '日记本';
  if (this.ragConfig[withSuffix]) {
    effectiveDbName = withSuffix;
    console.log(`[RAGDiaryPlugin] 自动适配日记本名称: "${dbName}" -> "${effectiveDbName}"`);
  }
}
```

**修改位置 1：缓存键生成 (第1379行)**
```javascript
// 1️⃣ 生成缓存键（使用原始 dbName 保持一致性）
const cacheKey = this._generateCacheKey({
  userContent,
  aiContent: aiContent || '',
  dbName: effectiveDbName, // 使用适配后的名称
  modifiers,
  dynamicK
});
```

**修改位置 2：displayName 设置 (第1416行)**
```javascript
const displayName = effectiveDbName + '日记本';
```

**修改位置 3：vectorDBManager.search 调用 (第1468行和第1495行)**
```javascript
// Time-aware path
let ragResults = await this.vectorDBManager.search(effectiveDbName, finalQueryVector, kForSearch, tagWeight, coreTagsForSearch);

// Standard path
let searchResults = await this.vectorDBManager.search(effectiveDbName, finalQueryVector, kForSearch, tagWeight, coreTagsForSearch);
```

**修改位置 4：getTimeRangeDiaries 调用 (第1482行)**
```javascript
const timeResults = await this.getTimeRangeDiaries(effectiveDbName, timeRange);
```

**修改位置 5：formatCombinedTimeAwareResults 调用 (第1491行)**
```javascript
retrievedContent = this.formatCombinedTimeAwareResults(finalResultsForBroadcast, timeRanges, effectiveDbName, metadata);
```

**修改说明：**
- 当查询的日记本名称与配置不匹配时，自动适配
- 例如：`"kilocode"` → `"kilocode日记本"`

---

## 模型配置方法

### 方法1：修改 MCP 服务器代码

修改 `MCP/mcp_kilovcp.mjs` 第113行的 `model` 字段：

```javascript
model: "你的模型名称",
```

### 方法2：确保 VCP 配置匹配

在项目根目录的 `config.env` 中，确保：

```env
# API 配置
API_Key=你的API密钥
API_URL=https://api.你的服务商.com

# 模型路由
SarModel1=gemini-3-flash-preview，gemini-3-flash-preview
SarPrompt1="你的提示词"
```

### 方法3：配置 rag_tags.json

在 `Plugin/RAGDiaryPlugin/rag_tags.json` 中配置日记本：

```json
{
  "你的日记本名称": {
    "path": "Agent/你的记忆文件.txt",
    "description": "日记本描述"
  }
}
```

---

## 常见问题排查

### 问题1：unknown model 错误

**错误信息：**
```
{"type":"bad_request_error","message":"invalid params, unknown model 'xxx' (2013)","http_code":"400"}
```

**解决方法：**
1. 检查 `mcp_kilovcp.mjs` 中的模型名称
2. 确保该模型在 VCP 的 `config.env` 中已配置
3. 确认 API 提供商支持该模型

### 问题2：RAG 检索无结果

**可能原因：**
1. 日记本名称不匹配（检查 rag_tags.json 配置）
2. 知识库索引未构建（重启 VCP 服务器）
3. 向量数据库未初始化

**解决方法：**
1. 检查日记本名称后缀是否正确
2. 重启 VCP 服务器触发索引重建
3. 查看控制台日志确认向量构建成功

### 问题3：日记本名称自动适配

**日志信息：**
```
[RAGDiaryPlugin] 自动适配日记本名称: "kilocode" -> "kilocode日记本"
```

**说明：**
- 这是正常行为，表示系统自动处理了名称不匹配问题
- 如果需要精确匹配，请确保查询时使用完整的日记本名称

---

## 日志查看

### MCP 服务器日志
- 在 VSCode MCP 面板中查看 kilovcp 服务器日志
- 或在终端查看 MCP 服务器输出

### RAG 插件日志
```
[RAGDiaryPlugin] Processing system message at index: 0
[RAGDiaryPlugin] 缓存未命中，执行RAG检索...
[RAGDiaryPlugin] 缓存已保存 (当前: 1/100)
[RAGDiaryPlugin] 自动适配日记本名称: "kilocode" -> "kilocode日记本"
```

---

## 重启生效

修改代码后，必须重启 MCP 服务器才能生效：

1. **VSCode MCP 面板**
   - 打开 VSCode 侧边栏的 MCP 面板
   - 找到 kilovcp 服务器
   - 点击重启按钮

2. **手动重启**
   - 关闭所有 node.exe 进程
   - 重新打开 VSCode
   - 启动 MCP 服务器

---

## 相关文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| MCP 服务器主文件 | `MCP/mcp_kilovcp.mjs` | 定义 query_kilo_memory 和 store_kilo_reflection 工具 |
| RAG 插件文件 | `Plugin/RAGDiaryPlugin/RAGDiaryPlugin.js` | 处理记忆向量化和检索 |
| VCP 配置 | `config.env` | AI API 和模型配置 |
| 日记本配置 | `Plugin/RAGDiaryPlugin/rag_tags.json` | 日记本索引配置 |
| 知识库根目录 | `dailynote/` | 存放日记文件 |

---

## 注意事项

1. **模型兼容性**
   - 确保 VCP 后端 API 支持所选模型
   - 不同模型可能需要不同的提示词格式

2. **索引构建**
   - 修改 rag_tags.json 后需要重启 VCP 重建索引
   - 大量文件可能需要较长的索引时间

3. **缓存策略**
   - 查询结果会被缓存 1 小时（可配置）
   - 配置变更会自动清空缓存

4. **权限配置**
   - 确保 mcp_settings.json 中已启用 kilovcp
   - 设置 alwaysAllow 权限避免每次请求确认

---

## 相关文档

- [VCP 官方文档](README.md)
- [RAG 插件文档](Plugin/RAGDiaryPlugin/)
- [MCP 协议说明](https://modelcontextprotocol.io/)