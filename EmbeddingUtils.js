// EmbeddingUtils.js
const { get_encoding } = require("@dqbd/tiktoken");
const encoding = get_encoding("cl100k_base");

// 配置
const embeddingMaxToken = parseInt(process.env.WhitelistEmbeddingModelMaxToken, 10) || 8000;
const safeMaxTokens = Math.floor(embeddingMaxToken * 0.4); // 进一步压缩余量，应对分词器巨大差异
const MAX_BATCH_ITEMS = 1; // 强制单条发送，彻底解决本地 Ollama 的批次处理限制问题
const DEFAULT_CONCURRENCY = parseInt(process.env.TAG_VECTORIZE_CONCURRENCY) || 5; // 🌟 读取并发配置

/**
 * 内部函数：发送单个批次
 */
async function _sendBatch(batchTexts, config, batchNumber) {
    const { default: fetch } = await import('node-fetch');
    const retryAttempts = 3;
    const baseDelay = 1000;

    for (let attempt = 1; attempt <= retryAttempts; attempt++) {
        try {
            const requestUrl = `${config.apiUrl}/v1/embeddings`;
            const requestBody = { model: config.model, input: batchTexts };
            const requestHeaders = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${config.apiKey}` };

            const response = await fetch(requestUrl, {
                method: 'POST',
                headers: requestHeaders,
                body: JSON.stringify(requestBody)
            });

            const responseBodyText = await response.text();

            if (!response.ok) {
                if (response.status === 429) {
                    // 429 限流时，增加等待时间
                    const waitTime = 5000 * attempt;
                    console.warn(`[Embedding] Batch ${batchNumber} rate limited (429). Retrying in ${waitTime/1000}s...`);
                    await new Promise(r => setTimeout(r, waitTime));
                    continue;
                }
                throw new Error(`API Error ${response.status}: ${responseBodyText.substring(0, 500)}`);
            }

            let data;
            try {
                data = JSON.parse(responseBodyText);
            } catch (parseError) {
                console.error(`[Embedding] JSON Parse Error for Batch ${batchNumber}:`);
                console.error(`Response (first 500 chars): ${responseBodyText.substring(0, 500)}`);
                throw new Error(`Failed to parse API response as JSON: ${parseError.message}`);
            }

            // 增强的响应结构验证和详细错误信息
            if (!data) {
                throw new Error(`API returned empty/null response`);
            }
            
            // 检查是否是错误响应
            if (data.error) {
                const errorMsg = data.error.message || JSON.stringify(data.error);
                const errorCode = data.error.code || response.status;
                console.error(`[Embedding] API Error for Batch ${batchNumber}:`);
                console.error(`  Error Code: ${errorCode}`);
                console.error(`  Error Message: ${errorMsg}`);
                console.error(`  Hint: Check if embedding model "${config.model}" is available on your API server`);
                throw new Error(`API Error ${errorCode}: ${errorMsg}`);
            }
            
            if (!data.data) {
                console.error(`[Embedding] Missing 'data' field in response for Batch ${batchNumber}`);
                console.error(`Response keys: ${Object.keys(data).join(', ')}`);
                console.error(`Response preview: ${JSON.stringify(data).substring(0, 500)}`);
                throw new Error(`Invalid API response structure: missing 'data' field`);
            }
            
            if (!Array.isArray(data.data)) {
                console.error(`[Embedding] 'data' field is not an array for Batch ${batchNumber}`);
                console.error(`data type: ${typeof data.data}`);
                console.error(`data value: ${JSON.stringify(data.data).substring(0, 200)}`);
                throw new Error(`Invalid API response structure: 'data' is not an array`);
            }

            if (data.data.length === 0) {
                console.warn(`[Embedding] Warning: Batch ${batchNumber} returned empty embeddings array`);
            }
            
            // 简单的 Log，证明并发正在跑
            // console.log(`[Embedding] ✅ Batch ${batchNumber} completed (${batchTexts.length} items).`);
            
            return data.data.sort((a, b) => a.index - b.index).map(item => item.embedding);

        } catch (e) {
            console.warn(`[Embedding] Batch ${batchNumber}, Attempt ${attempt} failed: ${e.message}`);
            if (attempt === retryAttempts) throw e;
            await new Promise(r => setTimeout(r, baseDelay * Math.pow(2, attempt)));
        }
    }
}

/**
 * 🚀 终极版：并发批量获取 Embeddings
 */
async function getEmbeddingsBatch(texts, config) {
    if (!texts || texts.length === 0) return [];

    // 1. ⚡️ 第一步：纯 CPU 操作，先把所有文本切分成 Batches
    const batches = [];
    let currentBatch = [];
    let currentBatchTokens = 0;

    for (const text of texts) {
        const textTokens = encoding.encode(text).length;
        if (textTokens > safeMaxTokens) {
            // 🌟 关键修复：如果单个 chunk 仍然超长（由于分词器差异），进行二次切割
            console.warn(`[Embedding] Chunk still too long (${textTokens} tokens), performing emergency re-split...`);
            const subChunks = chunkText(text, safeMaxTokens, Math.floor(safeMaxTokens * 0.1));
            for (const sub of subChunks) {
                batches.push([sub]);
            }
            continue;
        }

        const isTokenFull = currentBatch.length > 0 && (currentBatchTokens + textTokens > safeMaxTokens);
        const isItemFull = currentBatch.length >= MAX_BATCH_ITEMS;

        if (isTokenFull || isItemFull) {
            batches.push(currentBatch);
            currentBatch = [text];
            currentBatchTokens = textTokens;
        } else {
            currentBatch.push(text);
            currentBatchTokens += textTokens;
        }
    }
    if (currentBatch.length > 0) batches.push(currentBatch);

    console.log(`[Embedding] Prepared ${batches.length} batches. Executing with concurrency: ${DEFAULT_CONCURRENCY}...`);

    // 2. 🌊 第二步：并发执行器
    const results = new Array(batches.length); // 预分配结果数组，保证顺序
    let cursor = 0; // 当前处理到的批次索引

    // 定义 Worker：只要队列里还有任务，就不断抢任务做
    const worker = async (workerId) => {
        while (true) {
            // 🔒 获取任务索引 (原子操作模拟)
            const batchIndex = cursor++; 
            if (batchIndex >= batches.length) break; // 没任务了，下班

            const batchTexts = batches[batchIndex];
            // 执行请求 (Batch ID 从 1 开始显示)
            results[batchIndex] = await _sendBatch(batchTexts, config, batchIndex + 1);
        }
    };

    // 启动 N 个 Worker
    const workers = [];
    for (let i = 0; i < DEFAULT_CONCURRENCY; i++) {
        workers.push(worker(i));
    }

    // 等待所有 Worker 下班
    await Promise.all(workers);

    // 3. 📦 第三步：展平结果
    // results 数组里可能包含 undefined (如果某个 batch 最终失败)，filter 掉保平安
    return results.filter(r => r).flat();
}

module.exports = { getEmbeddingsBatch };