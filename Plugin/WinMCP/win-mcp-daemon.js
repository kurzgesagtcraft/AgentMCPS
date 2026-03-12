/**
 * WinMCP Daemon - 守护进程模式
 * @version 2.5.9 - 强制类型对齐版
 *   - 修复工具名映射：严格对应原生 Click, Type, Snapshot
 *   - 强制处理 loc/locs：无论传入的是 [x,y] 数组还是 "[x,y]" 字符串，全部强制转换为标准 List
 *   - 增加启动前的端口自清理逻辑
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');
const os = require('os');

const LOG_DIR = path.join(__dirname, '../../logs');
const WINMCP_LOG_FILE = path.join(LOG_DIR, 'winmcp_daemon.log');
const PID_FILE = path.join(LOG_DIR, 'winmcp_daemon.pid');

const PIPE_NAME = 'winmcp_daemon';
const SOCKET_PATH = process.platform === 'win32'
    ? `\\\\.\\pipe\\${PIPE_NAME}`
    : path.join(os.tmpdir(), `${PIPE_NAME}.sock`);

const CONFIG = {
    IDLE_TIMEOUT: 5 * 60 * 1000,
    INIT_TIMEOUT: 30000,
    TOOL_TIMEOUT: 120000,
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    SOCKET_TIMEOUT: 5000
};

function writeLog(message) {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] ${message}\n`;
    if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });
    try { fs.appendFileSync(WINMCP_LOG_FILE, logLine, 'utf8'); } catch (e) {}
    console.error(message);
}

const WINDOWS_MCP_PYTHON = path.join(__dirname, '../../MCP/VCP-MCP/.venv/Scripts/python.exe');
const WINDOWS_MCP_MODULE = '-m';
const WINDOWS_MCP_NAME = 'windows_mcp';

let mcpProcess = null;
let mcpInitialized = false;
let responseHandlers = new Map();
let buffer = '';
let requestId = 1;
let idleTimer = null;

function clearIdleTimer() { if (idleTimer) { clearTimeout(idleTimer); idleTimer = null; } }
function startIdleTimer() {
    clearIdleTimer();
    idleTimer = setTimeout(() => {
        writeLog('[Daemon] Idle timeout, shutting down MCP process');
        shutdownMCP();
    }, CONFIG.IDLE_TIMEOUT);
}

async function shutdownMCP() {
    clearIdleTimer();
    if (mcpProcess) {
        try { mcpProcess.stdin.end(); } catch (e) {}
        mcpProcess = null;
        mcpInitialized = false;
        buffer = '';
        responseHandlers.clear();
    }
}

async function initMCP() {
    if (mcpProcess && mcpInitialized) { startIdleTimer(); return true; }
    return new Promise((resolve, reject) => {
        try {
            writeLog('[Daemon] Starting windows-mcp process...');
            mcpProcess = spawn(WINDOWS_MCP_PYTHON, [WINDOWS_MCP_MODULE, WINDOWS_MCP_NAME], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: path.dirname(WINDOWS_MCP_PYTHON),
                env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' }
            });

            mcpProcess.stdout.on('data', (data) => { buffer += data.toString(); processBuffer(); });
            mcpProcess.on('close', () => { mcpInitialized = false; mcpProcess = null; });

            const initRequest = {
                jsonrpc: '2.0', id: requestId++, method: 'initialize',
                params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'VCP-WinMCP-Daemon', version: '2.5.9' } }
            };

            const timeout = setTimeout(() => { reject(new Error('MCP init timeout')); }, CONFIG.INIT_TIMEOUT);
            responseHandlers.set(initRequest.id, (response) => {
                clearTimeout(timeout);
                if (response.error) reject(new Error(`MCP init error: ${response.error.message}`));
                else {
                    mcpInitialized = true;
                    sendRequest({ jsonrpc: '2.0', method: 'notifications/initialized' });
                    startIdleTimer(); resolve(true);
                }
            });
            sendRequest(initRequest);
        } catch (error) { reject(error); }
    });
}

function processBuffer() {
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
        if (line.trim()) {
            try {
                const response = JSON.parse(line);
                if (response.id !== undefined && responseHandlers.has(response.id)) {
                    const handler = responseHandlers.get(response.id);
                    responseHandlers.delete(response.id);
                    handler(response);
                }
            } catch (e) {}
        }
    }
}

function sendRequest(request) {
    if (!mcpProcess) throw new Error('MCP process not started');
    mcpProcess.stdin.write(JSON.stringify(request) + '\n');
}

async function callTool(toolName, args) {
    await initMCP();
    return new Promise((resolve, reject) => {
        const request = {
            jsonrpc: '2.0', id: requestId++, method: 'tools/call',
            params: { name: toolName, arguments: args || {} }
        };
        const timeout = setTimeout(() => {
            responseHandlers.delete(request.id);
            reject(new Error('Tool execution timeout'));
        }, CONFIG.TOOL_TIMEOUT);

        responseHandlers.set(request.id, (response) => {
            clearTimeout(timeout);
            startIdleTimer();
            if (response.error) reject(new Error(response.error.message));
            else resolve(response.result);
        });
        sendRequest(request);
    });
}

const PARAM_CONVERTERS = {
    'loc': (v) => {
        if (Array.isArray(v)) return v.map(n => Math.floor(Number(n)));
        if (typeof v === 'string') {
            const clean = v.replace(/[\[\]]/g, '');
            return clean.split(',').map(n => n.trim()).filter(n => n !== '').map(n => Math.floor(Number(n)));
        }
        return v;
    },
    'locs': (v) => {
        if (Array.isArray(v)) return v.map(item => PARAM_CONVERTERS.loc(item));
        if (typeof v === 'string') {
            try { return JSON.parse(v).map(item => PARAM_CONVERTERS.loc(item)); } catch (e) {
                return v.split(';').map(s => PARAM_CONVERTERS.loc(s));
            }
        }
        return v;
    },
    'use_vision': (v) => String(v).toLowerCase() === 'true',
    'only_active_window': (v) => String(v).toLowerCase() === 'true',
    'press_enter': (v) => String(v).toLowerCase() === 'true',
    'duration': (v) => Math.floor(Number(v))
};

// 终极对齐：确保映射到 Python 后端真实存在的工具名
const TOOL_MAP = {
    'Click': 'Click', 'Type': 'Type', 'Snapshot': 'Snapshot',
    'click': 'Click', 'type': 'Type', 'snapshot': 'Snapshot',
    'Shell': 'Shell', 'App': 'App', 'Wait': 'Wait',
    'click_tool': 'Click', 'type_tool': 'Type', 'snapshot_tool': 'Snapshot'
};

async function handleRequest(input) {
    let request;
    try { request = JSON.parse(input); } catch (e) { return { status: "error", error: "Invalid JSON" }; }
    
    let tool = request.action || request.tool || request.name;
    let args = (request.arguments && typeof request.arguments === 'object') ? request.arguments : { ...request };
    
    ['maid', 'action', 'tool', 'tool_name', 'arguments'].forEach(k => delete args[k]);
    const mcpToolName = TOOL_MAP[tool] || tool;
    
    for (const key in args) {
        if (PARAM_CONVERTERS[key]) args[key] = PARAM_CONVERTERS[key](args[key]);
    }

    writeLog(`[Daemon] Final tool: ${mcpToolName}, args: ${JSON.stringify(args)}`);

    try {
        const result = await callTool(mcpToolName, args);
        let output = '';
        if (result && result.content) { for (const item of result.content) if (item.type === 'text') output += item.text; }
        return { status: "success", result: output || result };
    } catch (error) { return { status: "error", error: error.message }; }
}

function startDaemonServer() {
    if (process.platform !== 'win32' && fs.existsSync(SOCKET_PATH)) fs.unlinkSync(SOCKET_PATH);
    const server = net.createServer((socket) => {
        socket.on('data', async (data) => {
            const result = await handleRequest(data.toString());
            socket.write(JSON.stringify(result) + '\n');
            socket.end();
        });
    });
    server.listen(SOCKET_PATH, () => {
        fs.writeFileSync(PID_FILE, process.pid.toString());
        writeLog(`[Daemon] v2.5.9 (Final Robust) listening on ${SOCKET_PATH}`);
    });
}

if (process.argv.includes('--daemon')) {
    startDaemonServer();
} else {
    let input = '';
    process.stdin.on('data', chunk => input += chunk);
    process.stdin.on('end', async () => {
        const socket = net.createConnection(SOCKET_PATH, () => {
            socket.write(input + '\n');
        });
        socket.on('data', data => {
            console.log(data.toString());
            process.exit(0);
        });
        socket.on('error', (e) => {
            console.log(JSON.stringify({ status: "error", error: e.message }));
            process.exit(1);
        });
    });
}
