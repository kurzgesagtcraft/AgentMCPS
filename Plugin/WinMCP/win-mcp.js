/**
 * WinMCP Client - VCP插件客户端
 * 连接到守护进程，复用 MCP 连接
 *
 * v2.0 - 守护进程模式
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');
const os = require('os');

// 日志文件路径
const LOG_DIR = path.join(__dirname, '../../logs');
const WINMCP_LOG_FILE = path.join(LOG_DIR, 'winmcp_calls.log');
const PID_FILE = path.join(LOG_DIR, 'winmcp_daemon.pid');

// Windows 命名管道路径（Windows 上使用命名管道，Linux/Mac 使用 Unix Socket）
const PIPE_NAME = 'winmcp_daemon';
const SOCKET_PATH = process.platform === 'win32'
    ? `\\\\.\\pipe\\${PIPE_NAME}`
    : path.join(os.tmpdir(), `${PIPE_NAME}.sock`);

// 配置
const CONFIG = {
    SOCKET_TIMEOUT: 30000,     // socket 连接超时 30秒（与VCP框架超时一致）
    DAEMON_START_WAIT: 3000,   // 等待守护进程启动时间
    MAX_RETRIES: 3             // 最大重试次数
};

/**
 * 写入日志
 */
function writeLog(message) {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] ${message}\n`;
    
    if (!fs.existsSync(LOG_DIR)) {
        try {
            fs.mkdirSync(LOG_DIR, { recursive: true });
        } catch (e) {}
    }
    
    try {
        fs.appendFileSync(WINMCP_LOG_FILE, logLine, 'utf8');
    } catch (e) {}
    
    console.error(message);
}

/**
 * 检查守护进程是否运行
 */
function isDaemonRunning() {
    if (!fs.existsSync(PID_FILE)) {
        return false;
    }
    
    try {
        const pid = parseInt(fs.readFileSync(PID_FILE, 'utf8').trim());
        // 检查进程是否存在
        process.kill(pid, 0);
        return true;
    } catch (e) {
        // PID 文件存在但进程不存在，清理 PID 文件
        try {
            fs.unlinkSync(PID_FILE);
        } catch (err) {}
        return false;
    }
}

/**
 * 启动守护进程
 */
function spawnDaemon() {
    writeLog('[WinMCP] Spawning daemon process...');
    
    const daemonPath = path.join(__dirname, 'win-mcp-daemon.js');
    
    const daemon = spawn(process.execPath, [daemonPath, '--daemon'], {
        detached: true,
        stdio: 'ignore',
        windowsHide: true
    });
    
    daemon.unref();
    
    return new Promise((resolve) => {
        setTimeout(resolve, CONFIG.DAEMON_START_WAIT);
    });
}

/**
 * 发送请求到守护进程
 */
function sendRequest(input) {
    return new Promise((resolve, reject) => {
        const socket = net.createConnection(SOCKET_PATH, () => {
            socket.write(input + '\n');
        });

        let responseData = '';
        
        socket.on('data', (data) => {
            responseData += data.toString();
        });

        socket.on('end', () => {
            try {
                const response = JSON.parse(responseData.trim());
                resolve(response);
            } catch (e) {
                reject(new Error('Invalid response from daemon'));
            }
        });

        socket.on('error', (err) => {
            reject(new Error(`Connection failed: ${err.message}`));
        });

        socket.setTimeout(CONFIG.SOCKET_TIMEOUT, () => {
            socket.destroy();
            reject(new Error('Connection timeout'));
        });
    });
}

/**
 * 确保守护进程运行并发送请求
 */
async function ensureDaemonAndSend(input, retryCount = 0) {
    // 检查守护进程
    if (!isDaemonRunning()) {
        writeLog('[WinMCP] Daemon not running, starting...');
        await spawnDaemon();
    }
    
    try {
        const result = await sendRequest(input);
        return result;
    } catch (e) {
        if (retryCount < CONFIG.MAX_RETRIES) {
            writeLog(`[WinMCP] Request failed, retry ${retryCount + 1}/${CONFIG.MAX_RETRIES}: ${e.message}`);
            
            // 如果连接失败，可能是守护进程崩溃了，重新启动
            if (!isDaemonRunning()) {
                await spawnDaemon();
            }
            
            await new Promise(r => setTimeout(r, 1000));
            return ensureDaemonAndSend(input, retryCount + 1);
        }
        
        throw e;
    }
}

/**
 * 主入口
 */
async function main() {
    // 从 stdin 读取输入
    let input = '';
    process.stdin.setEncoding('utf8');
    
    for await (const chunk of process.stdin) {
        input += chunk;
    }

    input = input.trim();

    if (!input) {
        console.log(JSON.stringify({
            status: "error",
            error: 'No input provided'
        }));
        process.exit(1);
    }

    try {
        const result = await ensureDaemonAndSend(input);
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        writeLog(`[WinMCP] Error: ${error.message}`);
        console.log(JSON.stringify({
            status: "error",
            error: error.message
        }));
        process.exit(1);
    }
}

main().catch(error => {
    writeLog(`[WinMCP] Fatal error: ${error.message}`);
    process.exit(1);
});
