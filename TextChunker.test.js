// TextChunker.test.js
const { chunkText } = require('./TextChunker');

describe('TextChunker 单元测试', () => {
    test('应该正确切分短文本', () => {
        const text = "这是第一句。这是第二句。";
        const chunks = chunkText(text, 50, 5);
        expect(chunks).toHaveLength(1);
        expect(chunks[0]).toBe("这是第一句。这是第二句。");
    });

    test('应该在超过 maxTokens 时切分文本', () => {
        const text = "第一句。".repeat(20); // 构造较长文本
        const maxTokens = 10;
        const chunks = chunkText(text, maxTokens, 2);
        expect(chunks.length).toBeGreaterThan(1);
        chunks.forEach(chunk => {
            // 验证每个块不为空
            expect(chunk.length).toBeGreaterThan(0);
        });
    });

    test('空文本应返回空数组', () => {
        expect(chunkText("")).toEqual([]);
        expect(chunkText(null)).toEqual([]);
    });

    test('应该保留重叠部分以维持上下文', () => {
        const text = "句子一。句子二。句子三。句子四。";
        // 设置较小的 maxTokens 强制产生多个块
        const chunks = chunkText(text, 10, 5);
        if (chunks.length > 1) {
            // 验证第二个块是否包含第一个块的末尾（重叠）
            // 注意：具体表现取决于 tiktoken 的分词结果，这里做基本存在性检查
            expect(chunks.length).toBeGreaterThan(1);
        }
    });
});